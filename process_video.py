"""
Script de ejemplo para procesar archivos de video.
"""
import sys
from pathlib import Path

# Agregar proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from edge.main import EdgeProcessor
from config.settings import settings
from utils.logger import log


def process_video(video_path: str):
    """
    Procesa un archivo de video.
    
    Args:
        video_path: Ruta al archivo de video
    """
    log.info("=" * 60)
    log.info("📹 Procesador de Video - Person Tracker")
    log.info("=" * 60)
    log.info(f"Video: {video_path}")
    log.info(f"Device ID: {settings.device_id}")
    log.info("=" * 60)
    
    # Crear processor con video
    processor = EdgeProcessor(video_path=video_path)
    
    try:
        processor.start()
        log.info("\n✅ Video procesado completamente")
        
        # Mostrar estadísticas finales
        stats = processor.session_manager.get_stats()
        log.info("\n📊 Estadísticas finales:")
        log.info(f"  - Sesiones activas: {stats['active_sessions']}")
        log.info(f"  - Sesiones completadas: {stats['completed_sessions']}")
        log.info(f"  - Timeout: {stats['timeout_seconds']}s")
        
    except KeyboardInterrupt:
        log.info("\n⚠ Procesamiento interrumpido por el usuario")
    except Exception as e:
        log.error(f"\n✗ Error procesando video: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Entry point."""
    if len(sys.argv) < 2:
        log.error("❌ Error: Debes proporcionar la ruta al video")
        log.info("\nUso:")
        log.info("  python process_video.py <ruta_al_video>")
        log.info("\nEjemplo:")
        log.info("  python process_video.py videos/demo.mp4")
        sys.exit(1)
    
    video_path = sys.argv[1]
    
    # Verificar que el archivo existe
    if not Path(video_path).exists():
        log.error(f"❌ Error: Archivo no encontrado: {video_path}")
        sys.exit(1)
    
    process_video(video_path)


if __name__ == "__main__":
    main()
