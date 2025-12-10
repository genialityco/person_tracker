# Edge Module - Documentación

## 📁 Estructura

```
edge/
├── __init__.py         # Package init
├── camera.py           # CameraManager (RealSense + cámara estándar)
├── detector.py         # PersonDetector (YOLOv8)
├── tracker.py          # BoTSORT tracker
├── gaze.py             # GazeEstimator (atención)
├── session.py          # SessionManager (sesiones anónimas)
└── main.py             # EdgeProcessor (loop principal)
```

## 🎯 Componentes

### 1. CameraManager (`camera.py`)
Gestor unificado de fuentes de video con detección automática:

```python
# Modo 1: Archivo de video
camera = CameraManager(video_path="videos/demo.mp4")

# Modo 2: RealSense (auto-detecta)
camera = CameraManager(width=640, height=480, fps=30)

# Modo 3: Cámara específica
camera = CameraManager(camera_id=1)

camera.start()  # Auto-detecta: Video → RealSense → Cámara estándar

# Obtener frames
color, depth, depth_rs = camera.get_frames()

# Verificar modo y progreso
print(f"Es live: {camera.is_live}")
print(f"Usa video: {camera.use_video}")
if camera.use_video:
    progress = camera.get_progress()
    print(f"Progreso: {progress['progress_percent']:.1f}%")
```

**Características**:
- Prioridad: Video file → RealSense → Cámara estándar
- Soporte de formatos: MP4, AVI, MOV, MKV, FLV, WMV
- Seguimiento de progreso para videos
- Estimación de distancia 2D cuando no hay depth
- No requiere `pyrealsense2` para funcionar

### 2. PersonDetector (`detector.py`)
Wrapper de YOLOv8 para detección de personas:

```python
detector = PersonDetector(model_path="yolov8n.pt")
detections = detector.detect(frame)  # Returns [x1, y1, x2, y2, conf]
```

**Características**:
- Solo detecta clase "person" (clase 0 en COCO)
- Warm-up automático del modelo
- Optimizado para Edge devices

### 3. BoTSORT (`tracker.py`)
Tracker multi-objeto sin Re-ID biométrico:

```python
tracker = BoTSORT(max_age=30, min_hits=3, iou_threshold=0.3)
tracks = tracker.update(detections)  # Returns [x1, y1, x2, y2, track_id]
```

**Características**:
- Kalman Filter para predicción de movimiento
- Asociación por IoU (no usa features faciales)
- Minimiza ID switches
- Cumple privacidad ética

### 4. GazeEstimator (`gaze.py`)
Estimación de atención sin biometría:

```python
gaze = GazeEstimator(screen_position=(0, 0, 200))

# Modo 3D (con RealSense)
is_looking = gaze.is_looking_at_screen(person_position=position_3d)

# Modo 2D (sin RealSense)
is_looking = gaze.is_looking_at_screen(
    bbox_center=(cx, cy),
    frame_size=(width, height)
)
```

**Características**:
- Funciona con o sin depth data
- Fallback 2D: posición en el frame
- No usa análisis facial

### 5. SessionManager (`session.py`)
Gestión de sesiones anónimas:

```python
manager = SessionManager(timeout=3, fps=30)

# Actualizar sesión
manager.update_session(
    track_id=1,
    is_looking=True,
    distance_cm=200
)

# Obtener sesiones expiradas
expired = manager.get_expired_sessions()
payloads = manager.generate_payloads(expired)
```

**Características**:
- IDs temporales en RAM (nunca se transmiten)
- Destrucción automática después del timeout
- Generación de payloads anónimos

### 6. EdgeProcessor (`main.py`)
Orquestador principal:

```python
processor = EdgeProcessor()
processor.start()  # Inicia el loop de procesamiento
```

**Pipeline**:
1. Captura frame
2. Detección (YOLO)
3. Tracking (BoT-SORT)
4. Cálculo de posición/distancia
5. Estimación de atención
6. Actualización de sesiones
7. Envío de sesiones expiradas al API

## 🔄 Flujo de Datos

```
Video/Cámara → Frame
    ↓
YOLO → Detecciones [x1, y1, x2, y2, conf]
    ↓
BoT-SORT → Tracks [x1, y1, x2, y2, track_id]
    ↓
[Para cada track]
    ├─ Depth/2D → Distancia
    ├─ Gaze → is_looking
    └─ Session → update()
    ↓
[Timeout]
    ↓
SessionManager → Payload anónimo
    ↓
HTTP → API
    ↓
[Si es video: continuar hasta fin]
[Si es live: loop infinito]
```

## ⚙️ Configuración

### Variables de entorno (`.env`):

```bash
# Device
DEVICE_ID=12
SESSION_TIMEOUT=3
FIRMWARE_VERSION=1.8.2

# Video/Camera (prioridad: VIDEO_PATH → RealSense → Camera)
VIDEO_PATH=  # Ruta a video file (dejar vacío para cámara en vivo)
REALSENSE_WIDTH=640
REALSENSE_HEIGHT=480
REALSENSE_FPS=30
CAMERA_ID=0

# YOLO
YOLO_MODEL_PATH=models/yolov8n.pt
YOLO_CONFIDENCE=0.5

# Tracker
MAX_AGE=30
MIN_HITS=3
IOU_THRESHOLD=0.3

# API
API_URL=http://localhost:8000
API_KEY=your-secret-key
```

## 🚀 Ejecución

### Modo básico (cámara en vivo):
```bash
python edge/main.py
```

### Procesar archivo de video:
```bash
# Opción 1: Argumento de línea de comandos
python edge/main.py --video videos/demo.mp4

# Opción 2: Script dedicado
python process_video.py videos/demo.mp4

# Opción 3: Configurar VIDEO_PATH en .env
VIDEO_PATH=videos/demo.mp4
python edge/main.py
```

### Con cámara específica:
```bash
# En .env
CAMERA_ID=1

# O por línea de comandos
python edge/main.py --device-id 13
```

### Test de fuentes:
```bash
python test_camera.py
```

### Opciones de línea de comandos:
```bash
python edge/main.py --help

# Argumentos disponibles:
#   --video PATH        Ruta a archivo de video
#   --device-id ID      ID del dispositivo Edge
```

## 📊 Métricas de Performance

### Hardware mínimo recomendado:
- **CPU**: Intel i5 o equivalente
- **RAM**: 4GB
- **GPU**: Opcional (mejora FPS)

### FPS esperado:
- YOLOv8n + CPU: ~15-20 FPS
- YOLOv8n + GPU: ~60+ FPS
- YOLOv8s + CPU: ~10-15 FPS
- YOLOv8m + CPU: ~5-8 FPS

### Optimizaciones:
1. Usar modelo más pequeño (`yolov8n.pt`)
2. Reducir resolución (320x240)
3. Reducir FPS (15 fps)
4. Usar TensorRT/OpenVINO (si disponible)

## 🔒 Privacidad

### ✅ Garantías:
- **No se almacenan imágenes** en ningún momento
- **No se almacena video**
- **IDs temporales** solo en RAM
- **IDs destruidos** después del timeout
- **No se transmiten IDs** al API
- **No hay Re-ID** biométrico/facial

### ✅ Payload enviado:
```json
{
  "device_id": 12,
  "start_time": "2025-12-09T14:30:00Z",
  "duration_seconds": 14,
  "attention_seconds": 9.4,
  "demographics": {
    "age_group": "unknown",
    "gender_estimation": "unknown",
    "distance_cm": 180
  }
}
```

**Nota**: No incluye imágenes, track_id, ni datos biométricos.

## 🧪 Testing

### Test de cámara:
```bash
python test_camera.py
```

### Test de detección:
```python
from edge.detector import PersonDetector
import cv2

detector = PersonDetector()
frame = cv2.imread("test.jpg")
detections = detector.detect(frame)
print(f"Detectadas {len(detections)} personas")
```

### Test de sesiones:
```python
from edge.session import SessionManager

manager = SessionManager(timeout=3)
manager.update_session(1, is_looking=True, distance_cm=200)
# Esperar 3+ segundos
expired = manager.get_expired_sessions()
payloads = manager.generate_payloads(expired)
```

## 📝 Logs

El sistema genera logs detallados:

```
2025-12-09 14:30:00 | INFO | Inicializando Edge Processor...
2025-12-09 14:30:01 | INFO | ✓ Modelo YOLO cargado: models/yolov8n.pt
2025-12-09 14:30:02 | INFO | ✓ Usando cámara estándar (sin depth)
2025-12-09 14:30:02 | INFO | ✓ Edge Processor inicializado
2025-12-09 14:30:02 | INFO | 🚀 Edge Processor iniciado - Procesando...
2025-12-09 14:30:12 | INFO | 📊 Frame 300 | Activas: 2 | Completadas: 5
```

## 🐛 Troubleshooting

Ver [CAMERA_SYSTEM.md](../docs/CAMERA_SYSTEM.md) para guía completa.

### Problemas comunes:

1. **Cámara no disponible**: Verificar CAMERA_ID en `.env`
2. **YOLO lento**: Usar modelo más pequeño o reducir resolución
3. **Muchos ID switches**: Aumentar MAX_AGE, reducir MIN_HITS
4. **Sesiones muy cortas**: Aumentar SESSION_TIMEOUT
