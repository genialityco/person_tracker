"""
Script para resolver conflictos de dependencias entre MediaPipe y OpenCV.
Reinstala las versiones compatibles de numpy, opencv-python y mediapipe.
"""
import subprocess
import sys


def fix_dependencies():
    """Reinstala dependencias con versiones compatibles."""
    
    print("🔧 Resolviendo conflictos de dependencias...")
    print("")
    
    # Paso 1: Desinstalar versiones conflictivas
    print("1️⃣ Desinstalando versiones actuales...")
    packages_to_uninstall = [
        'opencv-python',
        'opencv-contrib-python',
        'mediapipe',
        'numpy'
    ]
    
    for pkg in packages_to_uninstall:
        try:
            subprocess.run(
                [sys.executable, '-m', 'pip', 'uninstall', '-y', pkg],
                check=False,
                capture_output=True
            )
            print(f"  ✓ Desinstalado: {pkg}")
        except Exception as e:
            print(f"  ⚠ No se pudo desinstalar {pkg}: {e}")
    
    print("")
    
    # Paso 2: Instalar versiones compatibles en orden
    print("2️⃣ Instalando versiones compatibles...")
    
    compatible_packages = [
        ('numpy', '1.26.4'),
        ('opencv-python', '4.10.0.84'),
        ('mediapipe', '0.10.9')
    ]
    
    for pkg, version in compatible_packages:
        try:
            print(f"  Instalando {pkg}=={version}...")
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', f'{pkg}=={version}'],
                check=True,
                capture_output=True,
                text=True
            )
            print(f"  ✓ {pkg}=={version} instalado")
        except subprocess.CalledProcessError as e:
            print(f"  ✗ Error instalando {pkg}: {e.stderr}")
            return False
    
    print("")
    
    # Paso 3: Verificar instalación
    print("3️⃣ Verificando instalación...")
    
    try:
        import numpy
        import cv2
        import mediapipe as mp
        
        print(f"  ✓ numpy: {numpy.__version__}")
        print(f"  ✓ opencv-python: {cv2.__version__}")
        print(f"  ✓ mediapipe: {mp.__version__}")
        print("")
        print("✅ Dependencias resueltas correctamente!")
        return True
        
    except ImportError as e:
        print(f"  ✗ Error importando: {e}")
        return False


if __name__ == "__main__":
    success = fix_dependencies()
    sys.exit(0 if success else 1)
