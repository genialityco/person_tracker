"""
Script de prueba para el estimador de demografía con YOLOv8-face.
"""
import cv2
import numpy as np
from edge.demographics import DemographicsEstimator
from utils.logger import log


def test_demographics():
    """Prueba el estimador de demografía con la cámara."""
    
    # Inicializar estimador
    log.info("Inicializando estimador de demografía...")
    estimator = DemographicsEstimator()
    
    if not estimator.model_loaded:
        log.error("❌ No se pudieron cargar los modelos")
        return
    
    # Abrir cámara
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        log.error("❌ No se pudo abrir la cámara")
        return
    
    log.info("✓ Cámara abierta. Presiona 'q' para salir")
    log.info("Instrucciones: Colócate frente a la cámara para estimar edad/género")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Para la prueba, usamos todo el frame como bbox
        h, w = frame.shape[:2]
        bbox = (0, 0, w, h)
        
        # Estimar demografía
        age_group, gender = estimator.estimate(frame, bbox)
        
        # Dibujar resultado
        text = f"Age: {age_group} | Gender: {gender}"
        cv2.putText(frame, text, (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # Mostrar
        cv2.imshow("Demographics Test", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    log.info("✓ Prueba completada")


if __name__ == "__main__":
    test_demographics()
