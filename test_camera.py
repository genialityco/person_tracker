"""
Script de prueba del sistema de cámaras y video.
Verifica qué fuentes están disponibles y prueba el CameraManager.
"""
import sys
from pathlib import Path

# Agregar proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import cv2
from edge.camera import CameraManager
from utils.logger import log


def test_opencv_cameras():
    """Prueba cámaras disponibles con OpenCV."""
    log.info("=" * 60)
    log.info("🔍 Probando cámaras disponibles con OpenCV")
    log.info("=" * 60)
    
    found_cameras = []
    
    for i in range(5):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                h, w = frame.shape[:2]
                log.info(f"✓ Cámara {i} disponible: {w}x{h}")
                found_cameras.append(i)
            cap.release()
    
    if not found_cameras:
        log.warning("⚠ No se encontraron cámaras OpenCV")
    else:
        log.info(f"\n✓ Total cámaras encontradas: {len(found_cameras)}")
    
    return found_cameras


def test_video_files():
    """Prueba archivos de video en el directorio."""
    log.info("\n" + "=" * 60)
    log.info("🎬 Buscando archivos de video en el directorio")
    log.info("=" * 60)
    
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv']
    video_files = []
    
    for ext in video_extensions:
        video_files.extend(project_root.glob(f"**/*{ext}"))
    
    if not video_files:
        log.info("⚠ No se encontraron archivos de video")
    else:
        log.info(f"✓ Archivos de video encontrados:")
        for vf in video_files[:5]:  # Mostrar primeros 5
            cap = cv2.VideoCapture(str(vf))
            if cap.isOpened():
                w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = cap.get(cv2.CAP_PROP_FPS)
                frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                log.info(f"  • {vf.name}: {w}x{h} @ {fps:.1f}fps ({frames} frames)")
                cap.release()
    
    return video_files


def test_camera_manager(video_path=None):
    """Prueba el CameraManager."""
    if video_path:
        log.info("\n" + "=" * 60)
        log.info(f"🎥 Probando CameraManager con video: {video_path}")
        log.info("=" * 60)
    else:
        log.info("\n" + "=" * 60)
        log.info("🎥 Probando CameraManager (cámara en vivo)")
        log.info("=" * 60)
    
    try:
        camera = CameraManager(
            width=640,
            height=480,
            fps=30,
            video_path=video_path
        )
        camera.start()
        
        log.info(f"\n📊 Estado del CameraManager:")
        log.info(f"  - Usando RealSense: {camera.use_realsense}")
        log.info(f"  - Usando video: {camera.use_video}")
        log.info(f"  - Tiene depth: {camera.has_depth}")
        log.info(f"  - Es en vivo: {camera.is_live}")
        log.info(f"  - Resolución: {camera.width}x{camera.height}")
        log.info(f"  - FPS: {camera.fps}")
        
        if camera.use_video:
            log.info(f"  - Total frames: {camera.total_frames}")
        
        # Capturar algunos frames
        log.info("\n📸 Capturando frames de prueba...")
        
        max_frames = 5 if camera.is_live else min(10, camera.total_frames)
        
        for i in range(max_frames):
            color_frame, depth_frame, depth_rs = camera.get_frames()
            
            if color_frame is not None:
                h, w = color_frame.shape[:2]
                has_depth = "Sí" if depth_frame is not None else "No"
                
                if camera.use_video:
                    progress = camera.get_progress()
                    log.info(
                        f"  Frame {i+1}: {w}x{h}, Depth: {has_depth}, "
                        f"Progreso: {progress['progress_percent']:.1f}%"
                    )
                else:
                    log.info(f"  Frame {i+1}: {w}x{h}, Depth: {has_depth}")
            else:
                log.warning(f"  Frame {i+1}: Error capturando o fin de video")
                break
        
        camera.stop()
        log.info("\n✅ Test completado exitosamente")
        
    except Exception as e:
        log.error(f"\n✗ Error en test: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Entry point."""
    log.info("\n" + "=" * 60)
    log.info("🚀 Test del Sistema de Cámaras y Video")
    log.info("=" * 60)
    
    # Test 1: Cámaras OpenCV
    opencv_cameras = test_opencv_cameras()
    
    # Test 2: Archivos de video
    video_files = test_video_files()
    
    # Test 3: CameraManager con cámara
    test_camera_manager()
    
    # Test 4: CameraManager con video (si hay archivos)
    if video_files:
        log.info("\n" + "=" * 60)
        log.info("💡 Prueba con video encontrado")
        log.info("=" * 60)
        test_video = video_files[0]
        test_camera_manager(video_path=str(test_video))
    
    log.info("\n" + "=" * 60)
    log.info("✅ Tests completados")
    log.info("=" * 60)
    
    # Resumen
    log.info("\n📋 Resumen:")
    log.info(f"  - Cámaras OpenCV encontradas: {len(opencv_cameras)}")
    log.info(f"  - Archivos de video encontrados: {len(video_files)}")
    
    if opencv_cameras:
        log.info(f"  - IDs de cámaras disponibles: {opencv_cameras}")
        log.info(f"\n💡 Tip: Puedes usar CAMERA_ID={opencv_cameras[0]} en .env")
    
    if video_files:
        log.info(f"\n💡 Tip: Puedes usar VIDEO_PATH={video_files[0]} en .env")


if __name__ == "__main__":
    main()
