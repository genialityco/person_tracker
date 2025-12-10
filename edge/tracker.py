"""
BoT-SORT Tracker implementation.
Basado en: https://github.com/NirAharon/BoT-SORT
"""
import numpy as np
from scipy.optimize import linear_sum_assignment
from filterpy.kalman import KalmanFilter
from utils.logger import log


class KalmanBoxTracker:
    """Kalman Filter para tracking de bounding boxes."""
    
    count = 0
    
    def __init__(self, bbox):
        """
        Inicializa tracker con detección inicial.
        
        Args:
            bbox: [x1, y1, x2, y2, score]
        """
        # Definir Kalman filter con modelo de velocidad constante
        self.kf = KalmanFilter(dim_x=7, dim_z=4)
        self.kf.F = np.array([
            [1, 0, 0, 0, 1, 0, 0],
            [0, 1, 0, 0, 0, 1, 0],
            [0, 0, 1, 0, 0, 0, 1],
            [0, 0, 0, 1, 0, 0, 0],
            [0, 0, 0, 0, 1, 0, 0],
            [0, 0, 0, 0, 0, 1, 0],
            [0, 0, 0, 0, 0, 0, 1]
        ])
        self.kf.H = np.array([
            [1, 0, 0, 0, 0, 0, 0],
            [0, 1, 0, 0, 0, 0, 0],
            [0, 0, 1, 0, 0, 0, 0],
            [0, 0, 0, 1, 0, 0, 0]
        ])
        
        self.kf.R[2:, 2:] *= 10.0
        self.kf.P[4:, 4:] *= 1000.0
        self.kf.P *= 10.0
        self.kf.Q[-1, -1] *= 0.01
        self.kf.Q[4:, 4:] *= 0.01
        
        self.kf.x[:4] = self._convert_bbox_to_z(bbox)
        self.time_since_update = 0
        self.id = KalmanBoxTracker.count
        KalmanBoxTracker.count += 1
        self.history = []
        self.hits = 0
        self.hit_streak = 0
        self.age = 0
    
    def _convert_bbox_to_z(self, bbox):
        """Convierte [x1,y1,x2,y2] a [x,y,s,r] (centro, escala, ratio)."""
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        x = bbox[0] + w / 2.0
        y = bbox[1] + h / 2.0
        s = w * h
        r = w / float(h + 1e-6)
        return np.array([x, y, s, r]).reshape((4, 1))
    
    def _convert_x_to_bbox(self, x):
        """Convierte [x,y,s,r] a [x1,y1,x2,y2]."""
        w = np.sqrt(x[2] * x[3])
        h = x[2] / w
        return np.array([
            x[0] - w / 2.0,
            x[1] - h / 2.0,
            x[0] + w / 2.0,
            x[1] + h / 2.0
        ]).reshape((1, 4))
    
    def update(self, bbox):
        """Actualiza el tracker con nueva detección."""
        self.time_since_update = 0
        self.history = []
        self.hits += 1
        self.hit_streak += 1
        self.kf.update(self._convert_bbox_to_z(bbox))
    
    def predict(self):
        """Predice la posición siguiente."""
        if (self.kf.x[6] + self.kf.x[2]) <= 0:
            self.kf.x[6] *= 0.0
        self.kf.predict()
        self.age += 1
        if self.time_since_update > 0:
            self.hit_streak = 0
        self.time_since_update += 1
        self.history.append(self._convert_x_to_bbox(self.kf.x))
        return self.history[-1]
    
    def get_state(self):
        """Retorna el estado actual del bounding box."""
        return self._convert_x_to_bbox(self.kf.x)


class BoTSORT:
    """BoT-SORT Tracker para tracking multi-objeto sin Re-ID."""
    
    def __init__(self, max_age=30, min_hits=3, iou_threshold=0.3):
        """
        Args:
            max_age: Frames máximos sin detección antes de eliminar track
            min_hits: Detecciones mínimas para considerar track válido
            iou_threshold: Umbral de IoU para matching
        """
        self.max_age = max_age
        self.min_hits = min_hits
        self.iou_threshold = iou_threshold
        self.trackers = []
        self.frame_count = 0
    
    def update(self, detections: np.ndarray) -> np.ndarray:
        """
        Actualiza tracks con nuevas detecciones.
        
        Args:
            detections: Array de detecciones [x1, y1, x2, y2, score] shape (N, 5)
            
        Returns:
            np.ndarray: Tracks activos [x1, y1, x2, y2, track_id] shape (M, 5)
        """
        self.frame_count += 1
        
        # Predicciones de todos los trackers
        trks = np.zeros((len(self.trackers), 5))
        to_del = []
        for t, trk in enumerate(trks):
            pos = self.trackers[t].predict()[0]
            trk[:] = [pos[0], pos[1], pos[2], pos[3], 0]
            if np.any(np.isnan(pos)):
                to_del.append(t)
        
        trks = np.ma.compress_rows(np.ma.masked_invalid(trks))
        for t in reversed(to_del):
            self.trackers.pop(t)
        
        # Matching usando Hungarian algorithm
        matched, unmatched_dets, unmatched_trks = self._associate_detections_to_trackers(
            detections, trks
        )
        
        # Actualizar trackers matched
        for m in matched:
            self.trackers[m[1]].update(detections[m[0], :])
        
        # Crear nuevos trackers para detecciones no matched
        for i in unmatched_dets:
            trk = KalmanBoxTracker(detections[i, :])
            self.trackers.append(trk)
        
        # Eliminar trackers muertos
        ret = []
        i = len(self.trackers)
        for trk in reversed(self.trackers):
            d = trk.get_state()[0]
            if (trk.time_since_update < 1) and (
                trk.hit_streak >= self.min_hits or self.frame_count <= self.min_hits
            ):
                ret.append(np.concatenate((d, [trk.id + 1])).reshape(1, -1))
            i -= 1
            if trk.time_since_update > self.max_age:
                self.trackers.pop(i)
        
        if len(ret) > 0:
            return np.concatenate(ret)
        return np.empty((0, 5))
    
    def _associate_detections_to_trackers(self, detections, trackers):
        """Asocia detecciones a trackers usando IoU."""
        if len(trackers) == 0:
            return np.empty((0, 2), dtype=int), np.arange(len(detections)), np.empty((0, 5), dtype=int)
        
        iou_matrix = self._iou_batch(detections, trackers)
        
        if min(iou_matrix.shape) > 0:
            a = (iou_matrix > self.iou_threshold).astype(np.int32)
            if a.sum(1).max() == 1 and a.sum(0).max() == 1:
                matched_indices = np.stack(np.where(a), axis=1)
            else:
                matched_indices = self._linear_assignment(-iou_matrix)
        else:
            matched_indices = np.empty(shape=(0, 2))
        
        unmatched_detections = []
        for d, det in enumerate(detections):
            if d not in matched_indices[:, 0]:
                unmatched_detections.append(d)
        
        unmatched_trackers = []
        for t, trk in enumerate(trackers):
            if t not in matched_indices[:, 1]:
                unmatched_trackers.append(t)
        
        matches = []
        for m in matched_indices:
            if iou_matrix[m[0], m[1]] < self.iou_threshold:
                unmatched_detections.append(m[0])
                unmatched_trackers.append(m[1])
            else:
                matches.append(m.reshape(1, 2))
        
        if len(matches) == 0:
            matches = np.empty((0, 2), dtype=int)
        else:
            matches = np.concatenate(matches, axis=0)
        
        return matches, np.array(unmatched_detections), np.array(unmatched_trackers)
    
    def _iou_batch(self, bb_test, bb_gt):
        """Calcula IoU entre dos sets de boxes."""
        bb_gt = np.expand_dims(bb_gt, 0)
        bb_test = np.expand_dims(bb_test, 1)
        
        xx1 = np.maximum(bb_test[..., 0], bb_gt[..., 0])
        yy1 = np.maximum(bb_test[..., 1], bb_gt[..., 1])
        xx2 = np.minimum(bb_test[..., 2], bb_gt[..., 2])
        yy2 = np.minimum(bb_test[..., 3], bb_gt[..., 3])
        w = np.maximum(0.0, xx2 - xx1)
        h = np.maximum(0.0, yy2 - yy1)
        wh = w * h
        o = wh / (
            (bb_test[..., 2] - bb_test[..., 0]) * (bb_test[..., 3] - bb_test[..., 1])
            + (bb_gt[..., 2] - bb_gt[..., 0]) * (bb_gt[..., 3] - bb_gt[..., 1])
            - wh
        )
        return o
    
    def _linear_assignment(self, cost_matrix):
        """Hungarian algorithm wrapper."""
        x, y = linear_sum_assignment(cost_matrix)
        return np.array(list(zip(x, y)))
