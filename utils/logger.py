"""
Configuración de logging con Loguru.
"""
import sys
from pathlib import Path
from loguru import logger
from config.settings import settings


def setup_logger():
    """Configura el logger global."""
    # Remover handler por defecto
    logger.remove()
    
    # Console handler
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.log_level,
        colorize=True,
    )
    
    # File handler
    log_path = Path(settings.log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.add(
        settings.log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=settings.log_level,
        rotation="500 MB",
        retention="10 days",
        compression="zip",
    )
    
    return logger


# Inicializar logger
log = setup_logger()
