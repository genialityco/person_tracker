"""
Script de prueba para el estimador de head pose y gaze mejorado.
Visualiza en tiempo real los ángulos de cabeza y si está mirando.
"""
import sys
from pathlib import Path

# Añadir directorio raíz al path
ROOT_DIR = Path(__file__).parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import cv2
import numpy as np
from edge.head_pose import HeadPoseEstimator
from edge.gaze import GazeEstimator
from edge.detector import PersonDetector
from utils.logger import log


def draw_pose_info(frame, bbox, pose, is_looking):
    """Dibuja información de pose en el frame."""
    x1, y1, x2, y2 = map(int, bbox)
    
    # Color según si está mirando
    color = (0, 255, 0) if is_looking else (0, 0, 255)
    
    # Bbox
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
    
    if pose is not None:
        yaw, pitch, roll = pose
        
        # Texto con ángulos
        text_lines = [
            f"Yaw: {yaw:.1f}",
            f"Pitch: {pitch:.1f}",
            f"Roll: {roll:.1f}",
            f"Looking: {'YES' if is_looking else 'NO'}"
        ]
        
        y_offset = y1 - 10
        for i, line in enumerate(text_lines):
            y_pos = y_offset - (len(text_lines) - i - 1) * 20
            cv2.putText(frame, line, (x1, y_pos),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)


def test_head_pose_gaze():
    """Prueba el sistema mejorado de detección de mirada."""
    
    log.info("Inicializando componentes...")
    
    # Inicializar detector de personas
    detector = PersonDetector()
    
    # Inicializar estimador de gaze con head pose
    gaze = GazeEstimator(use_head_pose=True)
    
    if gaze.head_pose_estimator is None:
        log.error("❌ HeadPoseEstimator no disponible. Instalar mediapipe:")
        log.error("   pip install mediapipe")
        return
    
    # Abrir cámara
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        log.error("❌ No se pudo abrir la cámara")
        return
    
    log.info("✓ Sistema inicializado")
    log.info("📹 Presiona 'q' para salir")
    log.info("")
    log.info("Instrucciones:")
    log.info("  - Colócate frente a la cámara")
    log.info("  - Mueve la cabeza y observa los ángulos")
    log.info("  - Verde = mirando, Rojo = no mirando")
    log.info("  - Umbrales: Yaw ±30°, Pitch ±25°")
    
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_count += 1
        h, w = frame.shape[:2]
        
        # Detectar personas
        detections = detector.detect(frame)
        
        for detection in detections:
            # detection es un array: [x1, y1, x2, y2, confidence]
            x1, y1, x2, y2, conf = detection
            x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])
            bbox = (x1, y1, x2, y2)
            
            # Estimar pose de cabeza
            pose = gaze.head_pose_estimator.estimate_head_pose(frame, bbox)
            
            # Determinar si está mirando
            is_looking = gaze.is_looking_at_screen(
                frame=frame,
                bbox=bbox,
                bbox_center=((x1 + x2) // 2, (y1 + y2) // 2),
                frame_size=(w, h),
                yaw_threshold=30.0,
                pitch_threshold=25.0
            )
            
            # Dibujar info
            draw_pose_info(frame, bbox, pose, is_looking)
        
        # Info general
        info_text = f"Frame: {frame_count} | Personas: {len(detections)}"
        cv2.putText(frame, info_text, (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Mostrar
        cv2.imshow("Head Pose & Gaze Test", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    log.info("✓ Prueba completada")


if __name__ == "__main__":
    test_head_pose_gaze()
