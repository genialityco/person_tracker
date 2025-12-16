# Modelos de Demografía - YOLOv8-face + GenderAge

## 📋 Descripción

Este sistema usa **YOLOv8-face** para detección facial y modelos Caffe pre-entrenados para clasificación de edad y género.

## 🏗️ Arquitectura

```
Frame (persona detectada) 
    ↓
ROI (bbox de la persona)
    ↓
YOLOv8-face (detecta cara dentro del ROI)
    ↓
Face ROI (crop de la cara)
    ↓
Caffe Models (edad + género)
    ↓
(age_group, gender)
```

## 📦 Modelos Requeridos

### 1. YOLOv8-face (Detección Facial)
- **Archivo**: `models/demographics/yoloface.pt`
- **Propósito**: Detectar caras en el ROI de la persona
- **Input**: Frame RGB
- **Output**: Bounding boxes de caras con confianza

### 2. Age Net (Clasificación de Edad)
- **Archivos**: 
  - `models/demographics/age_deploy.prototxt`
  - `models/demographics/age_net.caffemodel`
- **Input**: Face ROI 227x227
- **Output**: 8 categorías de edad
  - `(0-2)` → `0-17`
  - `(4-6)` → `0-17`
  - `(8-12)` → `0-17`
  - `(15-20)` → `18-24`
  - `(25-32)` → `25-34`
  - `(38-43)` → `35-44`
  - `(48-53)` → `45-54`
  - `(60-100)` → `65+`

### 3. Gender Net (Clasificación de Género)
- **Archivos**:
  - `models/demographics/gender_deploy.prototxt`
  - `models/demographics/gender_net.caffemodel`
- **Input**: Face ROI 227x227
- **Output**: 2 categorías
  - `Male` → `male`
  - `Female` → `female`

## 🚀 Uso

### Básico (integrado en el pipeline)
```bash
python -m edge.main
```

### Prueba standalone
```bash
python test_demographics.py
```

## 🔧 Descargar Modelos

### YOLOv8-face
Ya tienes el modelo en `models/demographics/yoloface.pt` ✓

### Modelos Caffe (edad/género)
```bash
python scripts/download_demographic_models.py
```

O descargar manualmente desde:
- https://github.com/GilLevi/AgeGenderDeepLearning

## ⚠️ Consideraciones de Privacidad

- **No se almacenan imágenes**: Solo se extraen categorías agregadas
- **Procesamiento local**: Todo ocurre en el edge device
- **Anónimo**: Las estimaciones no se vinculan a identidades
- **Temporal**: Solo se usa durante la detección activa

## 🎯 Rendimiento

- **Detección facial**: ~10ms con YOLOv8n-face
- **Clasificación**: ~5ms por cara (age + gender)
- **Total**: ~15ms por persona

## 📊 Precisión Esperada

- **YOLOv8-face**: >95% en detección frontal
- **Age Net**: ~70% precisión en grupo de edad
- **Gender Net**: ~85% precisión

## 🐛 Troubleshooting

### Error: "Modelo YOLOv8-face no encontrado"
```bash
# Verificar que existe:
ls models/demographics/yoloface.pt
```

### Error: "Modelos de edad/género no encontrados"
```bash
python scripts/download_demographic_models.py
```

### Baja precisión
- Asegurar buena iluminación
- Mantener caras visibles (no de perfil)
- Verificar que el ROI de la persona incluye la cara

## 📝 Ejemplo de Salida

```python
age_group, gender = estimator.estimate(frame, bbox)
# Output: ('25-34', 'male')
```
