# Solución de Conflictos de Dependencias

## 🐛 Problema

Conflicto entre MediaPipe y OpenCV debido a incompatibilidades en las versiones de numpy:

- **MediaPipe 0.10.x**: Requiere numpy `>=1.21.0,<2.0.0`
- **OpenCV 4.10.x**: Requiere numpy `>=1.21.2`
- **OpenCV 4.12.x**: Requiere numpy `>=2.0.0` ❌ (incompatible con MediaPipe)

## ✅ Solución

Usar versiones específicas compatibles entre sí:

```
numpy==1.26.4
opencv-python==4.10.0.84
mediapipe==0.10.9
```

## 🔧 Aplicar Solución

### Opción 1: Script Automático (Recomendado)

```bash
python scripts/fix_dependencies.py
```

Este script:
1. Desinstala versiones conflictivas
2. Instala versiones compatibles
3. Verifica la instalación

### Opción 2: Manual

```bash
# 1. Desinstalar versiones conflictivas
pip uninstall -y opencv-python opencv-contrib-python mediapipe numpy

# 2. Instalar versiones compatibles en orden
pip install numpy==1.26.4
pip install opencv-python==4.10.0.84
pip install mediapipe==0.10.9
```

### Opción 3: Desde requirements.txt

```bash
pip install -r requirements.txt --force-reinstall --no-cache-dir
```

## ⚠️ Notas Importantes

### opencv-contrib-python
Si tienes `opencv-contrib-python` instalado, **desinstálalo**:

```bash
pip uninstall -y opencv-contrib-python
```

**Razón**: `opencv-contrib-python` v4.12+ requiere numpy 2.x, incompatible con MediaPipe.

El proyecto **no necesita** opencv-contrib-python para funcionar.

### Verificación

Después de instalar, verifica que todo funciona:

```bash
python -c "import numpy; import cv2; import mediapipe as mp; print(f'numpy: {numpy.__version__}'); print(f'opencv: {cv2.__version__}'); print(f'mediapipe: {mp.__version__}')"
```

Salida esperada:
```
numpy: 1.26.4
opencv: 4.10.0
mediapipe: 0.10.9
```

### Probar HeadPoseEstimator

```bash
python -c "from edge.head_pose import HeadPoseEstimator; HeadPoseEstimator()"
```

Debe mostrar:
```
✓ HeadPoseEstimator inicializado (MediaPipe)
```

## 🔍 Diagnóstico

### Ver versiones actuales

```bash
pip show numpy opencv-python mediapipe
```

### Ver conflictos

```bash
pip check
```

## 📦 requirements.txt Actualizado

El archivo `requirements.txt` ahora especifica versiones exactas:

```txt
# OpenCV y MediaPipe: versiones compatibles con numpy
opencv-python==4.10.0.84  # Compatible con numpy 1.24-1.26
numpy>=1.24.0,<2.0.0  # Rango compatible con OpenCV y MediaPipe
mediapipe==0.10.9  # Última versión estable compatible
```

## 🚀 Instalación Limpia (Desde Cero)

Si prefieres empezar desde cero:

```bash
# 1. Crear nuevo entorno virtual
python -m venv venv_new
.\venv_new\Scripts\activate  # Windows

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Verificar
python -c "import numpy, cv2, mediapipe as mp; print('✅ OK')"
```

## 🐛 Troubleshooting

### Error: "ImportError: numpy.core.multiarray"

**Causa**: numpy 2.x instalado cuando se esperaba 1.x

**Solución**:
```bash
pip uninstall -y numpy
pip install numpy==1.26.4
```

### Error: "DLL load failed while importing cv2"

**Causa**: opencv-contrib-python y opencv-python instalados simultáneamente

**Solución**:
```bash
pip uninstall -y opencv-python opencv-contrib-python
pip install opencv-python==4.10.0.84
```

### Error: "module 'mediapipe' has no attribute 'solutions'"

**Causa**: Versión incorrecta de mediapipe o numpy

**Solución**:
```bash
pip uninstall -y mediapipe
pip install mediapipe==0.10.9
```

## ✨ Resumen

| Paquete | Versión | Razón |
|---------|---------|-------|
| numpy | `1.26.4` | Compatible con MediaPipe y OpenCV 4.10 |
| opencv-python | `4.10.0.84` | Última versión compatible con numpy 1.x |
| mediapipe | `0.10.9` | Última versión estable |

**No instalar**: `opencv-contrib-python` (requiere numpy 2.x)
