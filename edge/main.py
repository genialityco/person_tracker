"""
Edge Main Loop - Procesamiento principal en el dispositivo Edge.
"""
import sys
import time
import httpx
import argparse
import numpy as np
import cv2
from pathlib import Path

# Añadir directorio raíz al path
ROOT_DIR = Path(__file__).parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from edge.detector import PersonDetector
from edge.tracker import BoTSORT
from edge.camera import CameraManager
from edge.gaze import GazeEstimator
from edge.session import SessionManager
from edge.demographics import DemographicsEstimator
from config.settings import settings
from utils.logger import log


class EdgeProcessor:
    """Procesador principal del Edge Device."""
    
    def __init__(self, video_path=None):
        """
        Inicializa componentes del Edge.
        
        Args:
            video_path: Ruta a archivo de video (opcional, sobrescribe settings)
        """
        log.info("Inicializando Edge Processor...")
        
        # Componentes de visión
        self.detector = PersonDetector()
        self.tracker = BoTSORT(
            max_age=settings.max_age,
            min_hits=settings.min_hits,
            iou_threshold=settings.iou_threshold
        )
        
        # Camera Manager (Video, RealSense o cámara estándar)
        # video_path como argumento tiene prioridad sobre settings
        final_video_path = video_path or (settings.video_path if settings.video_path else None)
        
        self.camera = CameraManager(
            width=settings.realsense_width,
            height=settings.realsense_height,
            fps=settings.realsense_fps,
            camera_id=settings.camera_id,
            video_path=final_video_path
        )
        
        # Gaze estimator (pantalla frente a la cámara)
        self.gaze = GazeEstimator(
            screen_position=(0, 0, 200),  # 2m frente a cámara
            screen_normal=(0, 0, -1)  # Normal apuntando hacia cámara
        )
        
        # Demographics estimator (edad y género)
        self.demographics = DemographicsEstimator()
        
        # Session manager
        self.session_manager = SessionManager(
            timeout=settings.session_timeout,
            fps=settings.realsense_fps
        )
        
        # HTTP client para API
        self.http_client = httpx.Client(timeout=settings.api_timeout)
        
        self.running = False
        self.frame_count = 0
        self.show_display = settings.show_display
        
        log.info("✓ Edge Processor inicializado")
        if self.show_display:
            log.info("📺 Modo visualización activado")
    
    def start(self):
        """Inicia el procesamiento."""
        try:
            self.camera.start()
            self.running = True
            log.info("🚀 Edge Processor iniciado - Procesando...")
            
            self.run_loop()
            
        except KeyboardInterrupt:
            log.info("⚠ Deteniendo por interrupción del usuario...")
        except Exception as e:
            log.error(f"✗ Error fatal: {e}")
        finally:
            self.stop()
    
    def run_loop(self):
        """Loop principal de procesamiento."""
        while self.running:
            # Obtener frames de la cámara o video
            color_frame, depth_frame, depth_rs = self.camera.get_frames()
            
            if color_frame is None:
                # Si es un video, puede haber terminado
                if not self.camera.is_live:
                    log.info("📹 Video procesado completamente")
                    self.running = False
                    break
                continue
            
            self.frame_count += 1
            frame_height, frame_width = color_frame.shape[:2]
            
            # 1. DETECCIÓN - YOLO detecta personas
            detections = self.detector.detect(color_frame)
            
            # 2. TRACKING - BoT-SORT asigna IDs temporales
            tracks = self.tracker.update(detections)
            
            # 3. PROCESAR CADA TRACK
            for track in tracks:
                x1, y1, x2, y2, track_id = track
                track_id = int(track_id)
                
                # Centro y altura del bounding box
                cx = int((x1 + x2) / 2)
                cy = int((y1 + y2) / 2)
                bbox_height = y2 - y1
                
                # Intentar obtener posición 3D desde depth (si disponible)
                position_3d = None
                distance_cm = None
                
                if self.camera.has_depth and depth_rs is not None:
                    # Modo RealSense: usar depth real
                    position_3d = self.camera.get_3d_position(depth_rs, cx, cy)
                    
                    if position_3d is not None:
                        distance_cm = abs(position_3d[2])
                    
                        # Filtrar detecciones muy lejanas
                        if distance_cm > settings.max_detection_distance:
                            continue
                else:
                    # Modo cámara estándar: estimar distancia por tamaño del bbox
                    distance_cm = self.camera.estimate_distance_2d(bbox_height, frame_height)
                    
                    # Filtrar detecciones muy lejanas (estimadas)
                    if distance_cm > settings.max_detection_distance:
                        continue
                
                # 4. ESTIMACIÓN DE ATENCIÓN
                is_looking = self.gaze.is_looking_at_screen(
                    person_position=position_3d,
                    bbox_center=(cx, cy),
                    frame_size=(frame_width, frame_height)
                )
                
                # 5. ESTIMACIÓN DE DEMOGRAFÍA (solo una vez por sesión para optimizar)
                # Verificar si esta sesión ya tiene demografía estimada
                session = self.session_manager.sessions.get(track_id)
                age_group, gender = "unknown", "unknown"
                
                if session is None or not session.demographics_estimated:
                    # Primera vez viendo esta persona, estimar demografía
                    age_group, gender = self.demographics.estimate(
                        color_frame,
                        (x1, y1, x2, y2)
                    )
                
                # 6. ACTUALIZAR SESIÓN
                self.session_manager.update_session(
                    track_id=track_id,
                    is_looking=is_looking,
                    distance_cm=distance_cm,
                    age_group=age_group if age_group != "unknown" else None,
                    gender=gender if gender != "unknown" else None
                )
            
            # 7. PROCESAR SESIONES EXPIRADAS
            expired_sessions = self.session_manager.get_expired_sessions()
            
            if expired_sessions:
                payloads = self.session_manager.generate_payloads(expired_sessions)
                self._send_payloads(payloads)
            
            # Log periódico
            if self.frame_count % 300 == 0:  # Cada 10 segundos @ 30fps
                stats = self.session_manager.get_stats()
                log.info(
                    f"📊 Frame {self.frame_count} | "
                    f"Activas: {stats['active_sessions']} | "
                    f"Completadas: {stats['completed_sessions']}"
                )
            
            # 8. VISUALIZACIÓN (opcional)
            if self.show_display:
                display_frame = self._draw_detections(color_frame.copy(), tracks, expired_sessions)
                cv2.imshow('Person Tracker', display_frame)
                
                # Presionar 'q' para salir
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    log.info("⚠ Deteniendo por presionar 'q'...")
                    self.running = False
                    break
            
            # Pequeña pausa para no saturar CPU
            time.sleep(0.001)
    
    def _draw_detections(self, frame: np.ndarray, tracks: np.ndarray, expired_sessions: list) -> np.ndarray:
        """
        Dibuja detecciones y tracks en el frame.
        
        Args:
            frame: Frame RGB
            tracks: Array de tracks [x1, y1, x2, y2, track_id]
            expired_sessions: Lista de sesiones expiradas
            
        Returns:
            Frame con visualizaciones
        """
        # Dibujar cada track
        for track in tracks:
            x1, y1, x2, y2, track_id = track
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            track_id = int(track_id)
            
            # Color verde para tracks activos
            color = (0, 255, 0)
            thickness = 2
            
            # Dibujar bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
            
            # Dibujar ID
            label = f"ID: {track_id}"
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            
            # Fondo para el texto
            cv2.rectangle(
                frame,
                (x1, y1 - label_size[1] - 10),
                (x1 + label_size[0], y1),
                color,
                -1
            )
            
            # Texto
            cv2.putText(
                frame,
                label,
                (x1, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 0, 0),
                2
            )
        
        # Información en la parte superior
        stats = self.session_manager.get_stats()
        info_text = [
            f"Frame: {self.frame_count}",
            f"Tracks activos: {len(tracks)}",
            f"Sesiones activas: {stats['active_sessions']}",
            f"Sesiones completadas: {stats['completed_sessions']}"
        ]
        
        y_offset = 30
        for text in info_text:
            cv2.putText(
                frame,
                text,
                (10, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2
            )
            cv2.putText(
                frame,
                text,
                (10, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 0, 0),
                1
            )
            y_offset += 30
        
        return frame
    
    def _send_payloads(self, payloads: list):
        """
        Envía payloads anónimos al API.
        
        Args:
            payloads: Lista de payloads de sesión
        """
        for payload in payloads:
            try:
                response = self.http_client.post(
                    f"{settings.api_url}/sessions",
                    json=payload,
                    headers={"X-API-Key": settings.api_key}
                )
                
                if response.status_code == 200:
                    log.info(f"✓ Sesión enviada al API: {response.json().get('session_id')}")
                else:
                    log.warning(f"⚠ API error {response.status_code}: {response.text}")
                    
            except Exception as e:
                log.error(f"✗ Error enviando payload: {e}")
    
    def stop(self):
        """Detiene el procesamiento."""
        self.running = False
        self.camera.stop()
        self.http_client.close()
        
        if self.show_display:
            cv2.destroyAllWindows()
        
        log.info("✓ Edge Processor detenido")


def main():
    """Entry point."""
    # Parsear argumentos de línea de comandos
    parser = argparse.ArgumentParser(description="Person Tracker - Edge Device Processor")
    parser.add_argument(
        '--video',
        type=str,
        default=None,
        help='Ruta a archivo de video para procesar (mp4, avi, etc.)'
    )
    parser.add_argument(
        '--device-id',
        type=int,
        default=None,
        help='ID del dispositivo Edge (sobrescribe .env)'
    )
    
    args = parser.parse_args()
    
    # Sobrescribir settings si se pasan argumentos
    if args.device_id is not None:
        settings.device_id = args.device_id
    
    log.info("=" * 60)
    log.info("🎯 Person Tracker - Edge Device")
    log.info(f"   Device ID: {settings.device_id}")
    log.info(f"   Firmware: {settings.firmware_version}")
    log.info(f"   Model: {settings.model_version}")
    
    if args.video:
        log.info(f"   Video: {args.video}")
    
    log.info("=" * 60)
    
    processor = EdgeProcessor(video_path=args.video)
    processor.start()


if __name__ == "__main__":
    main()
