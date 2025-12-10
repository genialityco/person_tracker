# Person Tracker - Guía de Instalación Rápida

## 📦 Paso 1: Instalar dependencias

```bash
# Activar entorno virtual (recomendado)
python -m venv venv
.\venv\Scripts\activate  # Windows

# Instalar paquetes
pip install -r requirements.txt
```

## 🔧 Paso 2: Configurar entorno

```bash
# Copiar y editar archivo de configuración
copy .env.example .env
notepad .env  # Editar con tus valores
```

## 🐳 Paso 3: Levantar infraestructura con Docker

```bash
# Iniciar servicios (MongoDB, Kafka, ClickHouse, Grafana)
docker-compose up -d

# Verificar que estén corriendo
docker-compose ps
```

## 🤖 Paso 4: Descargar modelo YOLO

```bash
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"
```

## ✅ Paso 5: Verificar setup

```bash
python setup.py
```

## 🚀 Paso 6: Ejecutar componentes

### A. Edge Device - Cámara en vivo
```bash
python edge/main.py
```

### B. Edge Device - Procesar video
```bash
# Método 1: Argumento de línea de comandos
python edge/main.py --video videos/demo.mp4

# Método 2: Script dedicado
python process_video.py videos/demo.mp4

# Método 3: Configurar en .env
# VIDEO_PATH=videos/demo.mp4
python edge/main.py
```

### C. API Server (ingesta)
```bash
uvicorn api.main:app --reload --port 8000
```

### D. Kafka Consumer (pipeline analítico)
```bash
python kafka_pipeline/consumer.py
```

## 📊 Paso 7: Acceder a Grafana

```
URL: http://localhost:3000
Usuario: admin
Password: admin123
```

## 🧪 Paso 8: Ejecutar tests (opcional)

```bash
pytest tests/ -v
```

## 🔗 URLs útiles

- **API Docs**: http://localhost:8000/docs
- **Grafana**: http://localhost:3000
- **ClickHouse**: http://localhost:8123
- **MongoDB**: mongodb://localhost:27017

## ⚙️ Configuración Edge Device

Edita `.env` para configurar:
- `DEVICE_ID`: ID único del dispositivo
- `SESSION_TIMEOUT`: Segundos sin detección para cerrar sesión
- `MAX_DETECTION_DISTANCE`: Distancia máxima en cm (500 = 5m)
- `YOLO_CONFIDENCE`: Umbral de confianza (0.5 = 50%)

## 🛑 Detener todo

```bash
# Detener servicios Docker
docker-compose down

# (Opcional) Eliminar volúmenes
docker-compose down -v
```

## ❓ Problemas comunes

### Cámara no disponible
El sistema intentará usar RealSense primero y automáticamente cambiará a cámara estándar si no está disponible.

### Error: "No module named 'pyrealsense2'"
**Normal** - El sistema funciona sin RealSense. Si quieres usar RealSense:
```bash
pip install pyrealsense2
```

### Error: "Could not connect to MongoDB"
Verifica que Docker esté corriendo: `docker-compose ps`

### Error: "YOLO model not found"
Ejecuta: `python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"`

### Error: "Could not open camera 0"
Verifica que tienes una cámara conectada o prueba otro ID:
```python
# En .env, añadir:
CAMERA_ID=1  # Probar con diferentes valores 0, 1, 2...
```
