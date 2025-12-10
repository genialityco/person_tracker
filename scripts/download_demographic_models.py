"""
Script para descargar modelos pre-entrenados de edad y género.
Usa modelos de OpenCV DNN (Caffe models).
"""
import urllib.request
from pathlib import Path
from utils.logger import log



def download_file(url: str, destination: Path):
    """Descarga un archivo con barra de progreso."""
    log.info(f"Descargando {destination.name}...")
    
    try:
        urllib.request.urlretrieve(url, destination)
        log.info(f"✓ {destination.name} descargado")
    except Exception as e:
        log.error(f"✗ Error descargando {destination.name}: {e}")
        raise


def main():
    """Descarga todos los modelos necesarios."""
    log.info("=" * 60)
    log.info("📦 Descargando modelos de demografía")
    log.info("=" * 60)
    
    # Crear directorio
    models_dir = Path("models/demographics")
    models_dir.mkdir(parents=True, exist_ok=True)
    
    # URLs de los modelos (OpenCV DNN models)
    models = {
        "opencv_face_detector.pbtxt": "https://raw.githubusercontent.com/opencv/opencv/master/samples/dnn/face_detector/opencv_face_detector.pbtxt",
        "opencv_face_detector_uint8.pb": "https://github.com/opencv/opencv_3rdparty/raw/dnn_samples_face_detector_20170830/opencv_face_detector_uint8.pb",
        "age_deploy.prototxt": "https://raw.githubusercontent.com/GilLevi/AgeGenderDeepLearning/master/age_net_definitions/age_deploy.prototxt",
        "age_net.caffemodel": "https://github.com/GilLevi/AgeGenderDeepLearning/raw/master/models/age_net.caffemodel",
        "gender_deploy.prototxt": "https://raw.githubusercontent.com/GilLevi/AgeGenderDeepLearning/master/gender_net_definitions/gender_deploy.prototxt",
        "gender_net.caffemodel": "https://github.com/GilLevi/AgeGenderDeepLearning/raw/master/models/gender_net.caffemodel"
    }
    
    # Descargar cada modelo
    for filename, url in models.items():
        destination = models_dir / filename
        
        if destination.exists():
            log.info(f"⏭ {filename} ya existe, omitiendo...")
            continue
        
        download_file(url, destination)
    
    log.info("=" * 60)
    log.info("✓ Todos los modelos descargados exitosamente")
    log.info(f"📁 Ubicación: {models_dir.absolute()}")
    log.info("=" * 60)
    
    # Verificar tamaños
    log.info("\nTamaños de archivos:")
    for filename in models.keys():
        filepath = models_dir / filename
        if filepath.exists():
            size_mb = filepath.stat().st_size / (1024 * 1024)
            log.info(f"  {filename}: {size_mb:.2f} MB")


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    main()
