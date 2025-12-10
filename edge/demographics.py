"""
Demographics Estimator - Estimación de edad y género sin biometría.
Usa modelos ligeros para clasificación sin almacenar características faciales.
"""
import cv2
import numpy as np
from pathlib import Path
from utils.logger import log


class DemographicsEstimator:
    """Estimador de demografía usando modelos pre-entrenados de OpenCV."""
    
    def __init__(self):
        """Inicializa los modelos de edad y género."""
        self.age_net = None
        self.gender_net = None
        self.face_net = None
        self.model_loaded = False
        
        # Definiciones de edad y género
        self.age_list = ['(0-2)', '(4-6)', '(8-12)', '(15-20)', '(25-32)', '(38-43)', '(48-53)', '(60-100)']
        self.gender_list = ['Male', 'Female']
        
        # Mapeo a categorías del API: ['0-17', '18-24', '25-34', '35-44', '45-54', '55-64', '65+', 'unknown']
        self.age_group_mapping = {
            '(0-2)': '0-17',
            '(4-6)': '0-17', 
            '(8-12)': '0-17',
            '(15-20)': '18-24',
            '(25-32)': '25-34',
            '(38-43)': '35-44',
            '(48-53)': '45-54',
            '(60-100)': '65+'
        }
        
        self._load_models()
    
    def _load_models(self):
        """Carga los modelos de edad, género y detección facial."""
        try:
            models_dir = Path("models/demographics")
            models_dir.mkdir(parents=True, exist_ok=True)
            
            # Paths a los modelos
            face_proto = models_dir / "opencv_face_detector.pbtxt"
            face_model = models_dir / "opencv_face_detector_uint8.pb"
            age_proto = models_dir / "age_deploy.prototxt"
            age_model = models_dir / "age_net.caffemodel"
            gender_proto = models_dir / "gender_deploy.prototxt"
            gender_model = models_dir / "gender_net.caffemodel"
            
            # Verificar si los modelos existen
            if not all([face_proto.exists(), face_model.exists(), 
                       age_proto.exists(), age_model.exists(),
                       gender_proto.exists(), gender_model.exists()]):
                log.warning("⚠ Modelos de demografía no encontrados")
                log.info("💡 Descarga los modelos con: python scripts/download_demographic_models.py")
                log.info("💡 O el sistema usará estimación por defecto")
                self.model_loaded = False
                return
            
            # Cargar modelos
            self.face_net = cv2.dnn.readNet(str(face_model), str(face_proto))
            self.age_net = cv2.dnn.readNet(str(age_model), str(age_proto))
            self.gender_net = cv2.dnn.readNet(str(gender_model), str(gender_proto))
            
            self.model_loaded = True
            log.info("✓ Modelos de demografía cargados")
            
        except Exception as e:
            log.warning(f"⚠ Error cargando modelos de demografía: {e}")
            log.info("💡 El sistema usará estimación por defecto")
            self.model_loaded = False
    
    def estimate(self, frame: np.ndarray, bbox: tuple) -> tuple:
        """
        Estima edad y género de una persona.
        
        Args:
            frame: Frame RGB completo
            bbox: Bounding box (x1, y1, x2, y2)
            
        Returns:
            tuple: (age_group, gender) ejemplo: ('adult', 'male')
        """
        if not self.model_loaded:
            return self._estimate_by_bbox_size(bbox)
        
        try:
            x1, y1, x2, y2 = map(int, bbox)
            
            # Extraer región de interés (ROI)
            roi = frame[y1:y2, x1:x2]
            
            if roi.size == 0:
                return "unknown", "unknown"
            
            # Detectar cara en el ROI
            blob = cv2.dnn.blobFromImage(roi, 1.0, (227, 227), 
                                         (78.4263377603, 87.7689143744, 114.895847746),
                                         swapRB=False)
            
            # Predecir género
            self.gender_net.setInput(blob)
            gender_preds = self.gender_net.forward()
            gender_idx = gender_preds[0].argmax()
            gender = self.gender_list[gender_idx].lower()
            
            # Predecir edad
            self.age_net.setInput(blob)
            age_preds = self.age_net.forward()
            age_idx = age_preds[0].argmax()
            age_range = self.age_list[age_idx]
            age_group = self.age_group_mapping[age_range]
            
            return age_group, gender
            
        except Exception as e:
            log.debug(f"Error en estimación de demografía: {e}")
            return "unknown", "unknown"
    
    def _estimate_by_bbox_size(self, bbox: tuple) -> tuple:
        """
        Estimación simple basada en tamaño del bbox cuando no hay modelos.
        NO ES PRECISO - solo para testing.
        
        Args:
            bbox: Bounding box (x1, y1, x2, y2)
            
        Returns:
            tuple: (age_group, gender)
        """
        x1, y1, x2, y2 = bbox
        height = y2 - y1
        
        # Estimación muy básica por altura del bbox
        # Esto NO es preciso, solo un placeholder
        # Usa las categorías del API: ['0-17', '18-24', '25-34', '35-44', '45-54', '55-64', '65+', 'unknown']
        if height < 200:
            age_group = "0-17"
        elif height < 350:
            age_group = "18-24"
        elif height < 450:
            age_group = "25-34"
        else:
            age_group = "35-44"
        
        # Género desconocido sin modelo
        gender = "unknown"
        
        return age_group, gender
    
    def estimate_batch(self, frame: np.ndarray, bboxes: list) -> list:
        """
        Estima edad y género para múltiples personas.
        
        Args:
            frame: Frame RGB completo
            bboxes: Lista de bounding boxes [(x1,y1,x2,y2), ...]
            
        Returns:
            list: Lista de tuplas [(age_group, gender), ...]
        """
        results = []
        for bbox in bboxes:
            age_group, gender = self.estimate(frame, bbox)
            results.append((age_group, gender))
        return results
