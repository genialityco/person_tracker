"""
Head Pose Estimation - Estimación liviana de orientación de cabeza.
Usa MediaPipe FaceMesh para obtener landmarks y calcular ángulos de Euler (yaw, pitch, roll).
"""
import cv2
import numpy as np
from typing import Optional, Tuple
import mediapipe as mp
from utils.logger import log


class HeadPoseEstimator:
    """
    Estimador de pose de cabeza usando MediaPipe FaceMesh.
    Calcula yaw, pitch y roll para determinar dirección de mirada.
    """
    
    def __init__(self, 
                 max_num_faces: int = 1,
                 min_detection_confidence: float = 0.5,
                 min_tracking_confidence: float = 0.5):
        """
        Inicializa MediaPipe FaceMesh.
        
        Args:
            max_num_faces: Número máximo de caras a detectar
            min_detection_confidence: Confianza mínima para detección
            min_tracking_confidence: Confianza mínima para tracking
        """
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=max_num_faces,
            refine_landmarks=False,  # False para mejor performance
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
            static_image_mode=False  # Optimizado para video
        )
        
        # Índices de landmarks clave para pose de cabeza (modelo MediaPipe 468 landmarks)
        # Puntos específicos para construir modelo 3D simple
        self.model_points = np.array([
            (0.0, 0.0, 0.0),           # Nariz (tip)
            (0.0, -330.0, -65.0),      # Barbilla
            (-225.0, 170.0, -135.0),   # Ojo izquierdo (esquina izq)
            (225.0, 170.0, -135.0),    # Ojo derecho (esquina der)
            (-150.0, -150.0, -125.0),  # Comisura izquierda
            (150.0, -150.0, -125.0)    # Comisura derecha
        ], dtype=np.float32)
        
        # Índices de landmarks correspondientes en MediaPipe
        self.landmark_indices = [
            1,    # Nariz
            152,  # Barbilla
            33,   # Ojo izquierdo (outer)
            263,  # Ojo derecho (outer)
            61,   # Boca izquierda
            291   # Boca derecha
        ]
        
        # Parámetros de cámara (ajustar según resolución)
        self.focal_length = 1.0
        self.camera_matrix = None
        self.dist_coeffs = np.zeros((4, 1))  # Asumiendo sin distorsión
        
        log.info("✓ HeadPoseEstimator inicializado (MediaPipe)")
    
    def estimate_head_pose(
        self,
        frame: np.ndarray,
        bbox: Optional[Tuple[int, int, int, int]] = None
    ) -> Optional[Tuple[float, float, float]]:
        """
        Estima la orientación de la cabeza (yaw, pitch, roll).
        
        Args:
            frame: Frame RGB completo
            bbox: Bounding box opcional (x1, y1, x2, y2) para optimizar ROI
            
        Returns:
            tuple: (yaw, pitch, roll) en grados, o None si no detecta cara
                   yaw: rotación izq/der (-90 a +90)
                   pitch: arriba/abajo (-90 a +90)
                   roll: inclinación lateral (-90 a +90)
        """
        try:
            h, w = frame.shape[:2]
            
            # Inicializar matriz de cámara si no existe
            if self.camera_matrix is None:
                self.focal_length = w
                center = (w / 2, h / 2)
                self.camera_matrix = np.array([
                    [self.focal_length, 0, center[0]],
                    [0, self.focal_length, center[1]],
                    [0, 0, 1]
                ], dtype=np.float32)
            
            # Extraer ROI si bbox está disponible (optimización)
            if bbox is not None:
                x1, y1, x2, y2 = map(int, bbox)
                # Expandir bbox un 20% para incluir toda la cara
                margin_x = int((x2 - x1) * 0.2)
                margin_y = int((y2 - y1) * 0.2)
                x1 = max(0, x1 - margin_x)
                y1 = max(0, y1 - margin_y)
                x2 = min(w, x2 + margin_x)
                y2 = min(h, y2 + margin_y)
                
                roi = frame[y1:y2, x1:x2]
                if roi.size == 0:
                    return None
                
                # Procesar ROI
                results = self.face_mesh.process(cv2.cvtColor(roi, cv2.COLOR_BGR2RGB))
                
                if not results.multi_face_landmarks:
                    return None
                
                face_landmarks = results.multi_face_landmarks[0]
                
                # Extraer puntos 2D (ajustar coordenadas al frame completo)
                roi_h, roi_w = roi.shape[:2]
                image_points = []
                for idx in self.landmark_indices:
                    landmark = face_landmarks.landmark[idx]
                    x = landmark.x * roi_w + x1
                    y = landmark.y * roi_h + y1
                    image_points.append([x, y])
                
            else:
                # Procesar frame completo
                results = self.face_mesh.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                
                if not results.multi_face_landmarks:
                    return None
                
                face_landmarks = results.multi_face_landmarks[0]
                
                # Extraer puntos 2D
                image_points = []
                for idx in self.landmark_indices:
                    landmark = face_landmarks.landmark[idx]
                    x = landmark.x * w
                    y = landmark.y * h
                    image_points.append([x, y])
            
            image_points = np.array(image_points, dtype=np.float32)
            
            # Resolver PnP para obtener pose
            success, rotation_vector, translation_vector = cv2.solvePnP(
                self.model_points,
                image_points,
                self.camera_matrix,
                self.dist_coeffs,
                flags=cv2.SOLVEPNP_ITERATIVE
            )
            
            if not success:
                return None
            
            # Convertir rotation vector a matriz de rotación
            rotation_matrix, _ = cv2.Rodrigues(rotation_vector)
            
            # Calcular ángulos de Euler
            yaw, pitch, roll = self._rotation_matrix_to_euler_angles(rotation_matrix)
            
            return yaw, pitch, roll
            
        except Exception as e:
            log.debug(f"Error en estimación de pose: {e}")
            return None
    
    def _rotation_matrix_to_euler_angles(self, R: np.ndarray) -> Tuple[float, float, float]:
        """
        Convierte matriz de rotación a ángulos de Euler (yaw, pitch, roll).
        
        Args:
            R: Matriz de rotación 3x3
            
        Returns:
            tuple: (yaw, pitch, roll) en grados
        """
        sy = np.sqrt(R[0, 0] ** 2 + R[1, 0] ** 2)
        
        singular = sy < 1e-6
        
        if not singular:
            x = np.arctan2(R[2, 1], R[2, 2])  # Roll
            y = np.arctan2(-R[2, 0], sy)      # Pitch
            z = np.arctan2(R[1, 0], R[0, 0])  # Yaw
        else:
            x = np.arctan2(-R[1, 2], R[1, 1])
            y = np.arctan2(-R[2, 0], sy)
            z = 0
        
        # Convertir a grados
        roll = np.degrees(x)
        pitch = np.degrees(y)
        yaw = np.degrees(z)
        
        return yaw, pitch, roll
    
    def is_looking_forward(
        self,
        yaw: float,
        pitch: float,
        yaw_threshold: float = 30.0,
        pitch_threshold: float = 25.0
    ) -> bool:
        """
        Determina si la persona está mirando hacia adelante (a la pantalla).
        
        Args:
            yaw: Ángulo de rotación horizontal (grados)
            pitch: Ángulo de rotación vertical (grados)
            yaw_threshold: Umbral máximo de yaw en grados
            pitch_threshold: Umbral máximo de pitch en grados
            
        Returns:
            bool: True si está mirando hacia adelante
        """
        return abs(yaw) < yaw_threshold and abs(pitch) < pitch_threshold
    
    def __del__(self):
        """Liberar recursos de MediaPipe."""
        if hasattr(self, 'face_mesh'):
            self.face_mesh.close()
