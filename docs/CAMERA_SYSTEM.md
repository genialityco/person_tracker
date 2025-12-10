# Sistema de Cámaras - Guía Técnica

## 🎥 Soporte Multi-Cámara

El sistema soporta **automáticamente** dos modos de operación:

### 1. Modo RealSense (Preferido)
- **Cámara**: Intel RealSense D400 series
- **Ventajas**:
  - Medición precisa de distancia 3D
  - Depth map para posicionamiento espacial
  - Estimación de atención basada en geometría 3D
- **Requisito**: `pyrealsense2` instalado

### 2. Modo Cámara Estándar (Fallback)
- **Cámara**: Cualquier webcam USB o cámara integrada
- **Ventajas**:
  - No requiere hardware especial
  - Compatible con cualquier cámara OpenCV
  - Funciona sin `pyrealsense2`
- **Limitaciones**:
  - Distancia estimada por tamaño del bbox (menos precisa)
  - Atención estimada por posición en el frame

## 🔄 Detección Automática

El sistema automáticamente:

1. **Intenta usar RealSense** primero
2. Si falla (no disponible/no instalado), **cambia a cámara estándar**
3. Continúa funcionando normalmente con las capacidades disponibles

No requiere configuración manual. El cambio es transparente.

## ⚙️ Configuración

### Archivo `.env`

```bash
# Configuración de cámara
REALSENSE_WIDTH=640
REALSENSE_HEIGHT=480
REALSENSE_FPS=30
CAMERA_ID=0  # ID de cámara estándar (0 = default, 1 = segunda cámara, etc.)
```

### Cambiar ID de cámara estándar

Si tienes múltiples cámaras:

```bash
# Probar cámara por índice
CAMERA_ID=0  # Primera cámara
CAMERA_ID=1  # Segunda cámara
CAMERA_ID=2  # Tercera cámara
```

## 🧪 Probar Cámaras Disponibles

### Script de prueba:

```python
import cv2

# Probar cámaras disponibles
for i in range(5):
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        ret, frame = cap.read()
        if ret:
            print(f"✓ Cámara {i} disponible: {frame.shape}")
        cap.release()
    else:
        print(f"✗ Cámara {i} no disponible")
```

## 📊 Diferencias en Métricas

### Con RealSense (Depth disponible):
- **Distancia**: Medición real en cm desde el sensor depth
- **Atención**: Cálculo de ángulo 3D entre persona y pantalla
- **Precisión**: Alta (~±5cm)

### Con Cámara Estándar:
- **Distancia**: Estimación basada en altura del bbox
  ```python
  distance = (0.8 / height_ratio) * 200.0
  # Asume persona promedio 170cm
  ```
- **Atención**: Basada en posición en el frame
  - Centro del frame = mirando
  - Bordes del frame = no mirando
- **Precisión**: Moderada (~±20cm)

## 🔧 Calibración

### Cámara Estándar

Si la estimación de distancia no es precisa, ajustar en `edge/camera.py`:

```python
def estimate_distance_2d(self, bbox_height: float, frame_height: int) -> float:
    AVERAGE_PERSON_HEIGHT_CM = 170.0  # Ajustar según tu audiencia
    
    # Calibración empírica: bbox al 80% del frame ≈ 200cm
    estimated_distance = (0.8 / height_ratio) * 200.0  # Ajustar 200.0
    
    return max(50.0, min(estimated_distance, 500.0))
```

### Proceso de Calibración:

1. **Colocar persona a distancia conocida** (ej: 200cm)
2. **Medir altura del bbox** en pixels
3. **Calcular ratio**: `bbox_height / frame_height`
4. **Ajustar fórmula** para que coincida

Ejemplo:
- Frame: 480px alto
- Persona a 200cm: bbox = 384px (80% del frame)
- Fórmula: `(0.8 / 0.8) * 200 = 200cm` ✓

## 📝 Logs

El sistema indica qué modo está usando:

```
✓ Usando RealSense D400 series
  RealSense: 640x480@30fps
  Depth scale: 0.001
```

O:

```
⚠ No se pudo iniciar RealSense: [error]
  → Cambiando a cámara estándar...
✓ Usando cámara estándar (sin depth)
  Cámara estándar: 640x480
```

## 🐛 Troubleshooting

### RealSense no detectado

```bash
# Verificar dispositivos USB
lsusb  # Linux
# Buscar: "Intel Corp. RealSense"

# Reinstalar driver
pip uninstall pyrealsense2
pip install pyrealsense2
```

### Cámara estándar no funciona

```bash
# Verificar permisos (Linux)
sudo usermod -a -G video $USER
# Logout/login

# Probar con OpenCV directamente
python -c "import cv2; print(cv2.VideoCapture(0).isOpened())"
```

### Baja performance

- Reducir resolución: `REALSENSE_WIDTH=320, REALSENSE_HEIGHT=240`
- Reducir FPS: `REALSENSE_FPS=15`
- Usar modelo YOLO más pequeño: `yolov8n.pt`

## 🎯 Recomendaciones

### Para producción:
- **Usar RealSense** para máxima precisión
- Montar cámara a altura fija (ej: 150cm del suelo)
- Calibrar distancias con objetos conocidos

### Para desarrollo/pruebas:
- **Usar cámara estándar** es suficiente
- Enfocarse en lógica de negocio primero
- Migrar a RealSense cuando sea necesario

### Para demos:
- Cámara estándar funciona perfectamente
- Mostrar métricas relativas (no absolutas)
- Enfocarse en tendencias, no valores exactos
