# Person Tracker - Sistema Ético de Analítica de Audiencia 👁️

Sistema de tracking de personas con privacidad-por-diseño para analítica de audiencia en pantallas digitales.

## 🎯 Características Principales

- **Privacidad Ética**: Sin almacenamiento de biometría, imágenes o video
- **Edge Processing**: Procesamiento local con YOLOv8/v11 + BoT-SORT
- **Fuentes Flexibles**: Soporta archivos de video, RealSense D400, o cualquier cámara USB
- **Sesiones Anónimas**: IDs temporales que nunca salen del dispositivo
- **Pipeline Escalable**: MongoDB → Kafka → ClickHouse → Grafana
- **Métricas de Negocio**: TPA, Dwell Time, segmentación demográfica

## 🏗️ Arquitectura

```
Edge Device (Video/Cámara + YOLOv8 + BoT-SORT)
    ↓ (session_payload anónimo)
FastAPI (Validación + Persistencia)
    ↓
MongoDB (Fuente de verdad)
    ↓
Kafka (Streaming)
    ↓
ClickHouse (OLAP)
    ↓
Grafana (Visualización)
```

### Fuentes de Video Soportadas

El sistema soporta tres modos de entrada (en orden de prioridad):

1. **Archivo de Video** (prioridad máxima):
   - Formatos: MP4, AVI, MOV, MKV, FLV, WMV
   - Ideal para análisis batch o demos
   - Muestra progreso de procesamiento

2. **RealSense D400**:
   - Cámara Intel RealSense con depth
   - Medición precisa de distancia 3D
   - Estimación de atención por posición espacial

3. **Cámara Estándar** (fallback):
   - Cualquier cámara USB/webcam
   - Estimación de distancia por tamaño del bounding box
   - Estimación de atención por posición en el frame
   - No requiere `pyrealsense2`

## 📦 Instalación

### 1. Clonar y preparar entorno

```bash
git clone <repo>
cd person_tracker
python -m venv venv
.\venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 2. Configurar variables de entorno

```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

### 3. Descargar modelo YOLO

```bash
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"
```

### 4. Levantar infraestructura (Docker)

```bash
docker-compose up -d
```

## 🚀 Uso

### Edge Device - Cámara en vivo

```bash
python edge/main.py
```

### Edge Device - Procesar archivo de video

```bash
# Método 1: Configurar en .env
# VIDEO_PATH=videos/demo.mp4

# Método 2: Pasar como argumento
python edge/main.py --video videos/demo.mp4
```

### API Server

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### Kafka Consumer

```bash
python kafka_pipeline/consumer.py
```

## 📊 KPIs

| KPI | Descripción | Fórmula |
|-----|-------------|---------|
| **TPA** | Tiempo Promedio de Atención | `attention_seconds / duration_seconds` |
| **Dwell Time** | Permanencia total | `avg(duration_seconds)` |
| **Total Personas** | Volumen de audiencia | `count(sessions)` |
| **Conversión Proxy** | Engagement efectivo | `count(TPA > 0.7) / count(*)` |

## 🛠️ Estructura del Proyecto

```
person_tracker/
├── edge/               # Procesamiento Edge
│   ├── detector.py     # YOLOv8 wrapper
│   ├── tracker.py      # BoT-SORT implementation
│   ├── gaze.py         # Cálculo de atención
│   ├── session.py      # Gestor de sesiones
│   └── main.py         # Loop principal
├── api/                # FastAPI server
│   ├── main.py         # Endpoints
│   ├── routes.py       # Rutas
│   └── dependencies.py # Inyección de dependencias
├── models/             # Schemas Pydantic
│   └── session.py      # SessionPayload model
├── db/                 # Database clients
│   ├── mongodb.py      # MongoDB connector
│   └── clickhouse.py   # ClickHouse connector
├── kafka_pipeline/     # Kafka consumers
│   ├── producer.py     # Session producer
│   └── consumer.py     # ClickHouse consumer
├── config/             # Configuración
│   └── settings.py     # Pydantic settings
└── utils/              # Utilidades
    └── logger.py       # Logging setup
```

## 📝 Payload de Sesión

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
  },
  "meta": {
    "firmware_version": "1.8.2",
    "model_version": "yolov8n"
  }
}
```

## 🔒 Privacidad y Cumplimiento

- ✅ No almacena imágenes ni video
- ✅ No usa Re-ID biométrico
- ✅ IDs locales temporales (RAM only)
- ✅ Datos agregados y anónimos
- ✅ Cumple GDPR/CCPA por diseño

## 📈 Dashboard Grafana

Ver `grafana/dashboards/` para dashboards preconfigurados:
- Métricas en tiempo real
- Segmentación demográfica
- Heatmaps por ubicación
- KPIs de negocio

## 🧪 Testing

```bash
pytest tests/ -v --cov=.
```

## 📄 Licencia

MIT License - Ver LICENSE file

## 👥 Contribuir

Pull requests son bienvenidos. Para cambios mayores, abrir un issue primero.
