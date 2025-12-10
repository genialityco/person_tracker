"""
Camera Manager - Maneja RealSense, cámara estándar o archivos de video.
"""
import numpy as np
import cv2
from pathlib import Path
from typing import Optional, Tuple, Union
from utils.logger import log

# Intentar importar RealSense (opcional)
try:
    import pyrealsense2 as rs
    REALSENSE_AVAILABLE = True
except ImportError:
    REALSENSE_AVAILABLE = False
    log.warning("⚠ pyrealsense2 no disponible - usando cámara estándar o video")


class CameraManager:
    """
    Gestor unificado de cámara y video.
    Soporta: RealSense, cámara estándar, o archivo de video.
    """
    
    def __init__(
        self,
        width=640,
        height=480,
        fps=30,
        camera_id=0,
        video_path: Optional[str] = None
    ):
        """
        Args:
            width: Ancho de resolución
            height: Alto de resolución
            fps: Frames por segundo
            camera_id: ID de cámara para fallback (0 = default)
            video_path: Ruta a archivo de video (mp4, avi, etc.) - tiene prioridad
        """
        self.width = width
        self.height = height
        self.fps = fps
        self.camera_id = camera_id
        self.video_path = video_path
        
        self.use_realsense = False
        self.use_video = False
        self.pipeline = None
        self.align = None
        self.depth_scale = None
        self.cap = None
        
        self.has_depth = False
        self.total_frames = 0
        self.current_frame = 0
        self.is_live = True
    
    def start(self):
        """Inicia la fuente de video (archivo, RealSense o cámara estándar)."""
        # Prioridad 1: Archivo de video
        if self.video_path:
            try:
                self._start_video_file()
                log.info(f"✓ Usando archivo de video: {self.video_path}")
                return
            except Exception as e:
                log.error(f"✗ No se pudo abrir video {self.video_path}: {e}")
                raise
        
        # Prioridad 2: RealSense
        if REALSENSE_AVAILABLE:
            try:
                self._start_realsense()
                self.use_realsense = True
                self.has_depth = True
                log.info("✓ Usando RealSense D400 series")
                return
            except Exception as e:
                log.warning(f"⚠ No se pudo iniciar RealSense: {e}")
                log.info("  → Cambiando a cámara estándar...")
        
        # Prioridad 3: Cámara estándar
        self._start_standard_camera()
        log.info("✓ Usando cámara estándar (sin depth)")
    
    def _start_realsense(self):
        """Inicia RealSense D400."""
        self.pipeline = rs.pipeline()
        config = rs.config()
        
        # Configurar streams
        config.enable_stream(rs.stream.depth, self.width, self.height, rs.format.z16, self.fps)
        config.enable_stream(rs.stream.color, self.width, self.height, rs.format.bgr8, self.fps)
        
        # Iniciar pipeline
        profile = self.pipeline.start(config)
        
        # Obtener depth scale
        depth_sensor = profile.get_device().first_depth_sensor()
        self.depth_scale = depth_sensor.get_depth_scale()
        
        # Crear objeto align
        align_to = rs.stream.color
        self.align = rs.align(align_to)
        
        log.info(f"  RealSense: {self.width}x{self.height}@{self.fps}fps")
        log.info(f"  Depth scale: {self.depth_scale}")
    
    def _start_video_file(self):
        """Inicia reproducción de archivo de video."""
        video_file = Path(self.video_path)
        
        if not video_file.exists():
            raise FileNotFoundError(f"Archivo de video no encontrado: {self.video_path}")
        
        self.cap = cv2.VideoCapture(str(video_file))
        
        if not self.cap.isOpened():
            raise RuntimeError(f"No se pudo abrir archivo de video: {self.video_path}")
        
        # Obtener información del video
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        video_fps = self.cap.get(cv2.CAP_PROP_FPS)
        actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        self.use_video = True
        self.is_live = False
        
        log.info(f"  Video: {actual_width}x{actual_height} @ {video_fps:.1f}fps")
        log.info(f"  Total frames: {self.total_frames}")
        log.info(f"  Duración: {self.total_frames/video_fps:.1f}s")
    
    def _start_standard_camera(self):
        """Inicia cámara estándar con OpenCV."""
        self.cap = cv2.VideoCapture(self.camera_id)
        
        if not self.cap.isOpened():
            raise RuntimeError(f"No se pudo abrir cámara {self.camera_id}")
        
        # Configurar resolución
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.cap.set(cv2.CAP_PROP_FPS, self.fps)
        
        # Verificar resolución real
        actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        self.is_live = True
        
        log.info(f"  Cámara estándar: {actual_width}x{actual_height}")
    
    def get_frames(self) -> Tuple[Optional[np.ndarray], Optional[np.ndarray], Optional[object]]:
        """
        Obtiene frames de la cámara.
        
        Returns:
            tuple: (color_image, depth_image, depth_frame)
                  - color_image: np.ndarray RGB (H, W, 3)
                  - depth_image: np.ndarray depth en mm (H, W) o None si no hay depth
                  - depth_frame: rs.depth_frame o None
        """
        if self.use_realsense:
            return self._get_realsense_frames()
        else:
            return self._get_standard_frames()
    
    def _get_realsense_frames(self):
        """Obtiene frames de RealSense."""
        try:
            frames = self.pipeline.wait_for_frames()
            aligned_frames = self.align.process(frames)
            
            depth_frame = aligned_frames.get_depth_frame()
            color_frame = aligned_frames.get_color_frame()
            
            if not depth_frame or not color_frame:
                return None, None, None
            
            depth_image = np.asanyarray(depth_frame.get_data())
            color_image = np.asanyarray(color_frame.get_data())
            
            return color_image, depth_image, depth_frame
            
        except Exception as e:
            log.error(f"✗ Error obteniendo frames RealSense: {e}")
            return None, None, None
    
    def _get_standard_frames(self):
        """Obtiene frames de cámara estándar o video."""
        try:
            ret, frame = self.cap.read()
            
            if not ret:
                # Si es un video, puede haber terminado
                if self.use_video:
                    log.info("📹 Video terminado")
                return None, None, None
            
            # Incrementar contador de frames
            if self.use_video:
                self.current_frame += 1
                
                # Log de progreso cada 100 frames
                if self.current_frame % 100 == 0:
                    progress = (self.current_frame / self.total_frames) * 100
                    log.info(f"📹 Progreso: {self.current_frame}/{self.total_frames} ({progress:.1f}%)")
            
            # No hay depth con cámara estándar o video
            return frame, None, None
            
        except Exception as e:
            log.error(f"✗ Error obteniendo frames: {e}")
            return None, None, None
    
    def get_3d_position(self, depth_frame, pixel_x: int, pixel_y: int) -> Optional[np.ndarray]:
        """
        Convierte coordenadas pixel + depth a posición 3D.
        Solo funciona con RealSense.
        
        Args:
            depth_frame: Frame de profundidad de RealSense
            pixel_x: Coordenada X del pixel
            pixel_y: Coordenada Y del pixel
            
        Returns:
            np.ndarray: Posición 3D [x, y, z] en cm (None si no disponible)
        """
        if not self.use_realsense or depth_frame is None:
            return None
        
        try:
            depth = depth_frame.get_distance(pixel_x, pixel_y)
            
            if depth == 0:
                return None
            
            intrinsics = depth_frame.profile.as_video_stream_profile().intrinsics
            point_3d = rs.rs2_deproject_pixel_to_point(intrinsics, [pixel_x, pixel_y], depth)
            
            # Convertir de metros a centímetros
            return np.array(point_3d) * 100.0
            
        except Exception as e:
            log.warning(f"⚠ Error obteniendo posición 3D: {e}")
            return None
    
    def estimate_distance_2d(self, bbox_height: float, frame_height: int) -> float:
        """
        Estima distancia basada en altura del bounding box (cámara estándar).
        Aproximación simple: altura_real / altura_pixel ≈ distancia
        
        Args:
            bbox_height: Altura del bounding box en pixels
            frame_height: Altura del frame
            
        Returns:
            float: Distancia estimada en cm
        """
        # Aproximación: persona promedio 170cm, bbox ocupa % del frame
        # Esto es muy aproximado, ajustar según calibración
        AVERAGE_PERSON_HEIGHT_CM = 170.0
        
        if bbox_height < 10:  # Muy pequeño, muy lejos
            return 500.0  # 5m por defecto
        
        # Proporción del frame que ocupa la persona
        height_ratio = bbox_height / frame_height
        
        # Estimación inversa (cuanto más ocupa, más cerca está)
        # Calibración empírica: bbox al 80% del frame ≈ 200cm
        estimated_distance = (0.8 / height_ratio) * 200.0
        
        # Limitar rango
        return max(50.0, min(estimated_distance, 500.0))
    
    def stop(self):
        """Detiene la fuente de video."""
        if self.use_realsense and self.pipeline:
            self.pipeline.stop()
            log.info("✓ RealSense detenido")
        elif self.cap:
            self.cap.release()
            if self.use_video:
                log.info(f"✓ Video cerrado (procesados {self.current_frame}/{self.total_frames} frames)")
            else:
                log.info("✓ Cámara estándar detenida")
    
    def get_progress(self) -> dict:
        """
        Obtiene progreso de procesamiento (útil para videos).
        
        Returns:
            dict: {
                'current_frame': int,
                'total_frames': int,
                'progress_percent': float,
                'is_live': bool
            }
        """
        return {
            'current_frame': self.current_frame,
            'total_frames': self.total_frames,
            'progress_percent': (self.current_frame / self.total_frames * 100) if self.total_frames > 0 else 0,
            'is_live': self.is_live
        }
