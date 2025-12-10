# Dashboard Person Tracker - ClickHouse Cloud

## KPIs Principales

### 1. TPA - Tiempo Promedio de Atención (Tiempo mirando / duración total)
```sql
SELECT 
    ROUND(AVG(attention_seconds / duration_seconds) * 100, 2) AS tpa_percent
FROM analytics.sessions_raw_ch
WHERE duration_seconds > 0
```

**Visualización**: Single Value (Big Number)
- Título: "TPA - Tiempo Promedio de Atención"
- Formato: Porcentaje
- Color: Verde si > 50%, Amarillo si > 30%, Rojo si < 30%

---

### 2. Conteo Total de Sesiones
```sql
SELECT 
    COUNT(*) AS total_sesiones
FROM analytics.sessions_raw_ch
```

**Visualización**: Single Value (Big Number)
- Título: "Total de Sesiones"
- Formato: Número entero

---

### 3. Permanencia Promedio Frente a la Pantalla (Dwell Time)
```sql
SELECT 
    ROUND(AVG(duration_seconds), 2) AS dwell_time_segundos,
    ROUND(AVG(duration_seconds) / 60, 2) AS dwell_time_minutos
FROM analytics.sessions_raw_ch
```

**Visualización**: Single Value con unidades
- Título: "Permanencia Promedio"
- Mostrar en segundos o minutos según preferencia

---

### 4. Distribución por Edad
```sql
SELECT 
    age_group AS grupo_edad,
    COUNT(*) AS sesiones,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM analytics.sessions_raw_ch), 2) AS porcentaje
FROM analytics.sessions_raw_ch
GROUP BY age_group
ORDER BY sesiones DESC
```

**Visualización**: Pie Chart o Bar Chart
- Título: "Distribución por Grupo de Edad"
- Etiquetas: Mostrar porcentaje

---

### 5. Distribución por Género
```sql
SELECT 
    gender AS genero,
    COUNT(*) AS sesiones,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM analytics.sessions_raw_ch), 2) AS porcentaje
FROM analytics.sessions_raw_ch
GROUP BY gender
ORDER BY sesiones DESC
```

**Visualización**: Pie Chart
- Título: "Distribución por Género"
- Colores: Azul (male), Rosa (female), Gris (unknown)

---

### 6. % Sesiones con TPA > Umbral (50%)
```sql
SELECT 
    ROUND(
        SUM(CASE WHEN (attention_seconds / duration_seconds) > 0.5 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 
        2
    ) AS porcentaje_alta_atencion
FROM analytics.sessions_raw_ch
WHERE duration_seconds > 0
```

**Visualización**: Single Value con Gauge
- Título: "% Sesiones con Alta Atención (TPA > 50%)"
- Gauge: 0-100%
- Color: Verde si > 70%, Amarillo si > 50%, Rojo si < 50%

---

## Gráficos Adicionales Recomendados

### 7. Evolución de Sesiones por Hora (Últimas 24h)
```sql
SELECT 
    toStartOfHour(start_time) AS hora,
    COUNT(*) AS sesiones,
    ROUND(AVG(attention_seconds / duration_seconds) * 100, 2) AS tpa_promedio
FROM analytics.sessions_raw_ch
WHERE start_time >= now() - INTERVAL 24 HOUR
GROUP BY hora
ORDER BY hora DESC
```

**Visualización**: Line Chart (doble eje)
- Título: "Evolución Últimas 24 Horas"
- Eje Y1: Número de sesiones (barras)
- Eje Y2: TPA promedio (línea)

---

### 8. Matriz Edad x Género
```sql
SELECT 
    age_group AS edad,
    gender AS genero,
    COUNT(*) AS sesiones,
    ROUND(AVG(attention_seconds / duration_seconds) * 100, 2) AS tpa_promedio,
    ROUND(AVG(duration_seconds), 2) AS permanencia_promedio
FROM analytics.sessions_raw_ch
WHERE duration_seconds > 0
GROUP BY age_group, gender
ORDER BY sesiones DESC
```

**Visualización**: Table o Heatmap
- Título: "Análisis Cruzado: Edad x Género"
- Columnas: Edad, Género, Sesiones, TPA%, Permanencia

---

### 9. Distribución de TPA (Rangos)
```sql
SELECT 
    CASE 
        WHEN (attention_seconds / duration_seconds) < 0.25 THEN '0-25%'
        WHEN (attention_seconds / duration_seconds) < 0.50 THEN '25-50%'
        WHEN (attention_seconds / duration_seconds) < 0.75 THEN '50-75%'
        ELSE '75-100%'
    END AS rango_tpa,
    COUNT(*) AS sesiones,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM analytics.sessions_raw_ch WHERE duration_seconds > 0), 2) AS porcentaje
FROM analytics.sessions_raw_ch
WHERE duration_seconds > 0
GROUP BY rango_tpa
ORDER BY rango_tpa
```

**Visualización**: Bar Chart horizontal
- Título: "Distribución de Atención (TPA)"
- Colores: Rojo (0-25%), Naranja (25-50%), Amarillo (50-75%), Verde (75-100%)

---

### 10. Top Horas con Mayor Atención
```sql
SELECT 
    toHour(start_time) AS hora_del_dia,
    COUNT(*) AS sesiones,
    ROUND(AVG(attention_seconds / duration_seconds) * 100, 2) AS tpa_promedio,
    ROUND(AVG(duration_seconds), 2) AS permanencia_promedio
FROM analytics.sessions_raw_ch
WHERE duration_seconds > 0
GROUP BY hora_del_dia
ORDER BY tpa_promedio DESC
LIMIT 10
```

**Visualización**: Bar Chart
- Título: "Top 10 Horas con Mayor TPA"
- Ordenado por TPA descendente

---

### 11. Análisis de Distancia
```sql
SELECT 
    CASE 
        WHEN distance_cm < 100 THEN 'Muy cerca (<1m)'
        WHEN distance_cm < 200 THEN 'Cerca (1-2m)'
        WHEN distance_cm < 300 THEN 'Media (2-3m)'
        WHEN distance_cm < 400 THEN 'Lejos (3-4m)'
        ELSE 'Muy lejos (>4m)'
    END AS rango_distancia,
    COUNT(*) AS sesiones,
    ROUND(AVG(attention_seconds / duration_seconds) * 100, 2) AS tpa_promedio
FROM analytics.sessions_raw_ch
WHERE duration_seconds > 0
GROUP BY rango_distancia
ORDER BY 
    CASE 
        WHEN distance_cm < 100 THEN 1
        WHEN distance_cm < 200 THEN 2
        WHEN distance_cm < 300 THEN 3
        WHEN distance_cm < 400 THEN 4
        ELSE 5
    END
```

**Visualización**: Bar Chart
- Título: "TPA por Distancia a la Pantalla"

---

### 12. Métricas en Tiempo Real (últimos 5 minutos)
```sql
SELECT 
    COUNT(*) AS sesiones_recientes,
    ROUND(AVG(attention_seconds / duration_seconds) * 100, 2) AS tpa_reciente,
    ROUND(AVG(duration_seconds), 2) AS permanencia_reciente
FROM analytics.sessions_raw_ch
WHERE insert_time >= now() - INTERVAL 5 MINUTE
```

**Visualización**: 3 Single Values en fila
- Auto-refresh cada 30 segundos

---

## Layout Sugerido del Dashboard

```
+------------------+------------------+------------------+------------------+
|   TPA (KPI #1)   | Total Sesiones   | Permanencia Prom | % Alta Atención  |
|     65.4%        |     1,234        |    12.5 seg      |     68.2%        |
+------------------+------------------+------------------+------------------+
|                                                                           |
|          Evolución de Sesiones por Hora (últimas 24h)                    |
|                    (Line Chart + Bar Chart)                               |
|                                                                           |
+---------------------------------+-----------------------------------------+
|  Distribución por Edad          |  Distribución por Género                |
|     (Pie Chart)                 |     (Pie Chart)                         |
+---------------------------------+-----------------------------------------+
|                                                                           |
|          Matriz Edad x Género (Table/Heatmap)                            |
|                                                                           |
+---------------------------------+-----------------------------------------+
|  Distribución de TPA (Rangos)  |  TPA por Distancia                      |
|     (Bar Chart)                 |     (Bar Chart)                         |
+---------------------------------+-----------------------------------------+
|                    Top 10 Horas con Mayor TPA                            |
|                         (Bar Chart)                                       |
+---------------------------------------------------------------------------+
```

---

## Configuración en ClickHouse Cloud Console

### Paso 1: Acceder a SQL Console
1. Login en ClickHouse Cloud
2. Navega a **SQL Console**
3. Selecciona database: `analytics`

### Paso 2: Crear Charts
Para cada query:

1. **Pega la query** en el editor SQL
2. **Click "Run"** para verificar resultados
3. **Click "Create Chart"** en la parte superior derecha
4. **Selecciona el tipo de visualización** apropiado
5. **Configura título y formato**
6. **Guarda el chart**

### Paso 3: Crear Dashboard
1. Click en **"Dashboards"** en el menú lateral
2. Click **"Create Dashboard"**
3. Nombre: "Person Tracker Analytics"
4. **Arrastra los charts** creados al dashboard
5. **Organiza según el layout sugerido**

### Paso 4: Configurar Auto-refresh
1. En el dashboard, click **⚙️ Settings**
2. **Auto-refresh interval**: 30 segundos o 1 minuto
3. **Guarda configuración**

---

## Variables de Dashboard (Filtros)

Agrega estos filtros para hacer el dashboard interactivo:

### Filtro por Fecha
```sql
-- Agregar a todas las queries:
WHERE start_time >= {fecha_inicio} AND start_time <= {fecha_fin}
```

### Filtro por Dispositivo
```sql
-- Agregar a todas las queries:
WHERE device_id = {device_id_seleccionado}
```

### Ejemplo de Query con Filtros
```sql
SELECT 
    ROUND(AVG(attention_seconds / duration_seconds) * 100, 2) AS tpa_percent
FROM analytics.sessions_raw_ch
WHERE duration_seconds > 0
  AND start_time >= '{fecha_inicio}'
  AND start_time <= '{fecha_fin}'
  AND (device_id = {device_id} OR {device_id} = 0)  -- 0 = todos
```

---

## Alertas Sugeridas

Configura alertas para monitoreo:

### Alerta 1: TPA Bajo
```sql
SELECT AVG(attention_seconds / duration_seconds) * 100 AS tpa
FROM analytics.sessions_raw_ch
WHERE start_time >= now() - INTERVAL 1 HOUR
  AND duration_seconds > 0
HAVING tpa < 40  -- Alerta si TPA < 40%
```

### Alerta 2: Pocas Sesiones
```sql
SELECT COUNT(*) AS sesiones
FROM analytics.sessions_raw_ch
WHERE start_time >= now() - INTERVAL 1 HOUR
HAVING sesiones < 10  -- Alerta si menos de 10 sesiones/hora
```

---

## Exportar Dashboard

Para compartir o backup:

1. En el dashboard, click **"..."** (más opciones)
2. **"Export to JSON"**
3. Guarda el archivo JSON
4. Para importar: **"Import Dashboard"** → Sube el JSON
