"""
Script de setup inicial y verificación del proyecto.
"""
import sys
from pathlib import Path

# Agregar proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.settings import settings
from utils.logger import log


def check_environment():
    """Verifica que el entorno esté correctamente configurado."""
    log.info("=" * 60)
    log.info("🔍 Verificando configuración del proyecto")
    log.info("=" * 60)
    
    # Verificar archivo .env
    env_file = project_root / ".env"
    if not env_file.exists():
        log.warning("⚠ Archivo .env no encontrado")
        log.info("  Copiando .env.example → .env")
        import shutil
        shutil.copy(project_root / ".env.example", env_file)
        log.info("  ✓ Archivo .env creado")
    else:
        log.info("✓ Archivo .env encontrado")
    
    # Verificar configuración
    log.info(f"\n📋 Configuración actual:")
    log.info(f"  Device ID: {settings.device_id}")
    log.info(f"  Session Timeout: {settings.session_timeout}s")
    log.info(f"  API URL: {settings.api_url}")
    log.info(f"  MongoDB URI: {settings.mongo_uri}")
    log.info(f"  Kafka Servers: {settings.kafka_bootstrap_servers}")
    log.info(f"  ClickHouse: {settings.clickhouse_host}:{settings.clickhouse_port}")
    
    # Verificar directorio de logs
    log_dir = project_root / "logs"
    if not log_dir.exists():
        log_dir.mkdir(parents=True)
        log.info("\n✓ Directorio logs/ creado")
    
    # Verificar directorio de modelos
    models_dir = project_root / "models"
    if not (models_dir / "yolov8m.pt").exists():
        log.warning("\n⚠ Modelo YOLO no encontrado")
        log.info("  Ejecuta: python -c \"from ultralytics import YOLO; YOLO('yolov8n.pt')\"")
    else:
        log.info("\n✓ Modelo YOLO encontrado")
    
    log.info("\n" + "=" * 60)
    log.info("✅ Verificación completada")
    log.info("=" * 60)
    
    return True


if __name__ == "__main__":
    check_environment()
