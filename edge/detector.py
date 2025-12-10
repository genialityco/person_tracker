"""
YOLOv8 Detector wrapper con optimizaciones.
"""
import numpy as np
from ultralytics import YOLO
from config.settings import settings
from utils.logger import log


class PersonDetector:
    """Detector de personas usando YOLOv8."""
    
    def __init__(self, model_path: str = None):
        """
        Inicializa el detector.
        
        Args:
            model_path: Ruta al modelo YOLO (default: desde settings)
        """
        self.model_path = model_path or settings.yolo_model_path
        self.confidence = settings.yolo_confidence
        self.iou_threshold = settings.yolo_iou_threshold
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Carga el modelo YOLO."""
        try:
            log.info(f"Cargando modelo YOLO: {self.model_path}")
            self.model = YOLO(self.model_path)
            
            # Configurar dispositivo (GPU/CPU)
            device_setting = settings.yolo_device
            self.model.to(device_setting)
            
            # Detectar dispositivo actual
            device = self.model.device
            device_name = "GPU (CUDA)" if "cuda" in str(device) else "CPU"
            log.info(f"🔧 Dispositivo de detección: {device_name} (configurado: {device_setting})")
            
            # Optimización: ejecutar una predicción dummy para warm-up
            dummy_img = np.zeros((640, 640, 3), dtype=np.uint8)
            _ = self.model(dummy_img, verbose=False)
            
            log.info(f"✓ Modelo YOLO cargado: {self.model_path}")
        except Exception as e:
            log.error(f"✗ Error cargando modelo YOLO: {e}")
            raise
    
    def detect(self, frame: np.ndarray) -> np.ndarray:
        """
        Detecta personas en un frame.
        
        Args:
            frame: Frame RGB de OpenCV (H, W, 3)
            
        Returns:
            np.ndarray: Detecciones en formato [x1, y1, x2, y2, confidence]
                       Shape: (N, 5) donde N es el número de detecciones
        """
        try:
            # Ejecutar detección
            results = self.model(
                frame,
                conf=self.confidence,
                iou=self.iou_threshold,
                classes=[0],  # Clase 0 = persona en COCO
                verbose=False
            )[0]
            
            # Extraer bounding boxes
            if len(results.boxes) == 0:
                return np.empty((0, 5))
            
            boxes = results.boxes.xyxy.cpu().numpy()  # [x1, y1, x2, y2]
            scores = results.boxes.conf.cpu().numpy().reshape(-1, 1)  # [conf]
            
            # Concatenar: [x1, y1, x2, y2, conf]
            detections = np.hstack([boxes, scores])
            
            return detections
            
        except Exception as e:
            log.error(f"✗ Error en detección: {e}")
            return np.empty((0, 5))
    
    def detect_with_metadata(self, frame: np.ndarray) -> dict:
        """
        Detecta personas y retorna metadata adicional.
        
        Args:
            frame: Frame RGB
            
        Returns:
            dict: {
                'detections': np.ndarray,
                'count': int,
                'inference_time': float
            }
        """
        import time
        
        start = time.time()
        detections = self.detect(frame)
        inference_time = time.time() - start
        
        return {
            'detections': detections,
            'count': len(detections),
            'inference_time': inference_time
        }
