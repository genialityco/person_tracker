# Procesamiento de Videos - Guía Completa

## 🎬 Introducción

El sistema puede procesar archivos de video pregrabados además de streams en vivo. Esto es ideal para:

- **Análisis batch**: Procesar múltiples videos de forma offline
- **Demos y pruebas**: Sin necesidad de cámara física
- **Análisis histórico**: Procesar grabaciones existentes
- **Desarrollo**: Testing sin hardware específico

## 📹 Formatos Soportados

El sistema soporta todos los formatos que OpenCV puede leer:

- ✅ **MP4** (H.264, H.265)
- ✅ **AVI** (diversos codecs)
- ✅ **MOV** (QuickTime)
- ✅ **MKV** (Matroska)
- ✅ **FLV** (Flash Video)
- ✅ **WMV** (Windows Media)
- ✅ **WEBM** (VP8/VP9)

## 🚀 Formas de Usar

### 1. Línea de Comandos (Recomendado)

```bash
python edge/main.py --video videos/demo.mp4
```

**Ventajas**:
- Rápido y directo
- Perfecto para scripts
- Fácil de automatizar

### 2. Script Dedicado

```bash
python process_video.py videos/demo.mp4
```

**Ventajas**:
- Interfaz específica para videos
- Muestra estadísticas al final
- Mejor para uso interactivo

### 3. Variable de Entorno

```bash
# En .env
VIDEO_PATH=videos/demo.mp4

# Ejecutar
python edge/main.py
```

**Ventajas**:
- No necesitas modificar comandos
- Ideal para configuración persistente
- Útil en contenedores Docker

## 📊 Características del Procesamiento

### Progreso en Tiempo Real

El sistema muestra el progreso mientras procesa:

```
📹 Video: demo.mp4
  Video: 1920x1080 @ 30.0fps
  Total frames: 900
  Duración: 30.0s

📹 Progreso: 100/900 (11.1%)
📹 Progreso: 200/900 (22.2%)
📹 Progreso: 300/900 (33.3%)
...
📹 Video terminado
✅ Video procesado completamente
```

### Detección de Fin

El sistema detecta automáticamente cuando el video termina:

```python
if color_frame is None:
    if not self.camera.is_live:
        log.info("📹 Video procesado completamente")
        self.running = False
        break
```

### Métricas Finales

Al terminar, muestra estadísticas:

```
📊 Estadísticas finales:
  - Sesiones activas: 0
  - Sesiones completadas: 15
  - Timeout: 3s
```

## 🎯 Casos de Uso

### 1. Demo/Presentación

```bash
# Procesar video de demostración
python edge/main.py --video demos/store_traffic.mp4
```

**Ideal para**:
- Presentaciones a clientes
- Demos de producto
- Validación de concepto

### 2. Análisis Batch

```bash
# Procesar múltiples videos
for video in videos/*.mp4; do
    python process_video.py "$video"
done
```

**Ideal para**:
- Análisis de grabaciones de seguridad
- Procesamiento nocturno
- Análisis histórico

### 3. Testing/Desarrollo

```bash
# Usar video corto para desarrollo
python edge/main.py --video test/sample_10s.mp4
```

**Ideal para**:
- Desarrollo sin cámara
- Testing rápido
- CI/CD pipelines

### 4. Comparación de Modelos

```bash
# YOLOv8n (rápido)
YOLO_MODEL_PATH=models/yolov8n.pt python edge/main.py --video test.mp4

# YOLOv8m (preciso)
YOLO_MODEL_PATH=models/yolov8m.pt python edge/main.py --video test.mp4
```

**Ideal para**:
- Benchmark de modelos
- Ajuste de parámetros
- Optimización de performance

## ⚡ Performance

### FPS de Procesamiento

El FPS real depende del hardware y modelo YOLO:

| Hardware | YOLOv8n | YOLOv8s | YOLOv8m |
|----------|---------|---------|---------|
| CPU i5 | 15-20 | 10-15 | 5-8 |
| CPU i7 | 20-30 | 15-20 | 8-12 |
| GPU (GTX 1660) | 60+ | 45+ | 30+ |
| GPU (RTX 3060) | 100+ | 80+ | 60+ |

### Tiempo de Procesamiento

Para un video de 1 minuto (1800 frames @ 30fps):

- **CPU i5 + YOLOv8n**: ~2-3 minutos
- **CPU i7 + YOLOv8n**: ~1.5-2 minutos
- **GPU + YOLOv8n**: ~30-60 segundos

### Optimizaciones

```bash
# 1. Usar modelo más pequeño
YOLO_MODEL_PATH=models/yolov8n.pt

# 2. Reducir resolución (procesar frames más pequeños)
# El video se redimensiona automáticamente

# 3. Procesar cada N frames (skip frames)
# Implementar en el código si es necesario
```

## 📝 Ejemplos Prácticos

### Ejemplo 1: Análisis de Tienda

```bash
# Video de cámara de seguridad de tienda
python edge/main.py --video recordings/store_2025-12-09.mp4

# Output esperado:
# - Sesiones de clientes detectadas
# - Tiempo de permanencia
# - Áreas de atención
```

### Ejemplo 2: Evento/Exhibición

```bash
# Video de stand en feria
python process_video.py events/booth_morning.mp4

# Métricas:
# - Total de visitantes
# - Tiempo promedio de interacción
# - Picos de tráfico
```

### Ejemplo 3: Testing Continuo

```bash
# Script de CI/CD
#!/bin/bash
python edge/main.py --video tests/fixtures/test_video.mp4
if [ $? -eq 0 ]; then
    echo "✅ Video processing test passed"
else
    echo "❌ Video processing test failed"
    exit 1
fi
```

## 🔧 Configuración Avanzada

### Ajustar Detección para Videos

```bash
# En .env para videos específicos:

# Video con personas pequeñas/lejanas
YOLO_CONFIDENCE=0.3  # Más sensible

# Video con mucho ruido/movimiento
YOLO_CONFIDENCE=0.7  # Más restrictivo

# Video con tracking difícil
MAX_AGE=45  # Mantener tracks más tiempo
MIN_HITS=2  # Menos frames para confirmar track
```

### Session Timeout para Videos

```bash
# Video de flujo rápido (retail)
SESSION_TIMEOUT=2  # Sesiones más cortas

# Video de observación lenta (museo)
SESSION_TIMEOUT=5  # Sesiones más largas
```

## 🐛 Troubleshooting

### Video no se procesa

```bash
# Verificar que el archivo existe y es válido
python -c "import cv2; cap=cv2.VideoCapture('video.mp4'); print(cap.isOpened())"

# Si retorna False, el video puede estar corrupto o usar codec no soportado
```

### Procesamiento muy lento

```bash
# Verificar FPS de procesamiento vs FPS del video
# Si FPS procesamiento << FPS video, considerar:
# 1. Modelo más pequeño
# 2. Reducir resolución
# 3. Skip frames
```

### Memoria alta

```bash
# Si el video es muy grande:
# 1. Procesar en chunks
# 2. Liberar recursos cada N frames
# 3. Usar modelo más pequeño
```

## 📊 Análisis de Resultados

Los resultados se envían al API en tiempo real:

```json
{
  "device_id": 12,
  "start_time": "2025-12-09T14:30:00Z",
  "duration_seconds": 14,
  "attention_seconds": 9.4,
  "demographics": {
    "age_group": "25-34",
    "gender_estimation": "male",
    "distance_cm": 180
  }
}
```

### Ver Resultados en Grafana

1. Abrir Grafana: `http://localhost:3000`
2. Dashboard: "Person Tracker Analytics"
3. Filtrar por `device_id` y rango de tiempo
4. Analizar métricas:
   - Total personas
   - Tiempo promedio de atención
   - Distribución demográfica

### Consultar en MongoDB

```javascript
// Sesiones del video procesado hoy
db.sessions.find({
    device_id: 12,
    start_time: {
        $gte: ISODate("2025-12-09T00:00:00Z")
    }
})
```

### Consultar en ClickHouse

```sql
-- Métricas del video por hora
SELECT
    toStartOfHour(start_time) as hour,
    count() as total_people,
    avg(attention_rate) as avg_attention
FROM sessions_raw_ch
WHERE device_id = 12
  AND start_time >= today()
GROUP BY hour
ORDER BY hour;
```

## 🎓 Tips y Best Practices

1. **Nombrado de Archivos**: Usar timestamps en nombres
   ```
   store_2025-12-09_morning.mp4
   booth_2025-12-09_14-30.mp4
   ```

2. **Organización**: Crear estructura de carpetas
   ```
   videos/
   ├── raw/          # Videos originales
   ├── processed/    # Videos procesados
   └── samples/      # Videos de prueba
   ```

3. **Metadata**: Usar DEVICE_ID diferente por ubicación
   ```bash
   python edge/main.py --video store1.mp4 --device-id 1
   python edge/main.py --video store2.mp4 --device-id 2
   ```

4. **Testing**: Crear video corto de prueba (5-10s)
   ```bash
   # Extraer primeros 10 segundos
   ffmpeg -i input.mp4 -t 10 -c copy sample_10s.mp4
   ```

5. **Backup**: Siempre mantener videos originales
   - No sobrescribir
   - Usar almacenamiento redundante
   - Documentar fecha/ubicación

## 📚 Recursos Adicionales

- [OpenCV VideoCapture docs](https://docs.opencv.org/master/d8/dfe/classcv_1_1VideoCapture.html)
- [FFmpeg para conversión de formatos](https://ffmpeg.org/)
- [Edge Module README](README.md)
- [Camera System docs](../docs/CAMERA_SYSTEM.md)
