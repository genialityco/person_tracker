# Dashboard para Person Tracker - ClickHouse Cloud

## Configuración Inicial

### 1. Actualizar credenciales en `.env`:

```env
CLICKHOUSE_HOST=tu-instancia.clickhouse.cloud
CLICKHOUSE_PORT=8443
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=tu-password-cloud
CLICKHOUSE_DATABASE=analytics
```

### 2. Ejecutar configuración:

```powershell
python scripts/setup_clickhouse_cloud.py
```

## Queries para Dashboard

### KPI Principal - Total de Sesiones
```sql
SELECT COUNT(*) as total_sessions
FROM analytics.sessions_raw_ch
```

### Tasa de Atención Promedio (TPA)
```sql
SELECT 
    ROUND(AVG(attention_seconds / duration_seconds) * 100, 2) as attention_rate_percent
FROM analytics.sessions_raw_ch
WHERE duration_seconds > 0
```

### Tiempo Promedio de Estadía (Dwell Time)
```sql
SELECT 
    ROUND(AVG(duration_seconds), 2) as avg_dwell_time_seconds
FROM analytics.sessions_raw_ch
```

### Sesiones por Hora (Últimas 24h)
```sql
SELECT 
    toStartOfHour(start_time) as hour,
    COUNT(*) as sessions
FROM analytics.sessions_raw_ch
WHERE start_time >= now() - INTERVAL 24 HOUR
GROUP BY hour
ORDER BY hour DESC
```

### Distribución Demográfica - Edad
```sql
SELECT 
    age_group,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM analytics.sessions_raw_ch), 2) as percentage
FROM analytics.sessions_raw_ch
GROUP BY age_group
ORDER BY count DESC
```

### Distribución Demográfica - Género
```sql
SELECT 
    gender,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM analytics.sessions_raw_ch), 2) as percentage
FROM analytics.sessions_raw_ch
GROUP BY gender
ORDER BY count DESC
```

### Análisis Cruzado: Edad x Género
```sql
SELECT 
    age_group,
    gender,
    COUNT(*) as sessions,
    ROUND(AVG(attention_seconds / duration_seconds) * 100, 2) as avg_attention_rate,
    ROUND(AVG(duration_seconds), 2) as avg_duration
FROM analytics.sessions_raw_ch
WHERE duration_seconds > 0
GROUP BY age_group, gender
ORDER BY sessions DESC
```

### Top Horas Pico
```sql
SELECT 
    toHour(start_time) as hour_of_day,
    COUNT(*) as sessions,
    ROUND(AVG(attention_seconds), 2) as avg_attention
FROM analytics.sessions_raw_ch
GROUP BY hour_of_day
ORDER BY sessions DESC
LIMIT 10
```

### Métricas por Dispositivo
```sql
SELECT 
    device_id,
    COUNT(*) as total_sessions,
    ROUND(AVG(duration_seconds), 2) as avg_duration,
    ROUND(AVG(attention_seconds / duration_seconds) * 100, 2) as avg_attention_rate,
    ROUND(AVG(distance_cm), 0) as avg_distance_cm
FROM analytics.sessions_raw_ch
WHERE duration_seconds > 0
GROUP BY device_id
ORDER BY total_sessions DESC
```

### Tendencia Semanal
```sql
SELECT 
    toDate(start_time) as date,
    COUNT(*) as sessions,
    ROUND(AVG(attention_seconds / duration_seconds) * 100, 2) as attention_rate,
    ROUND(AVG(duration_seconds), 2) as avg_duration
FROM analytics.sessions_raw_ch
WHERE start_time >= now() - INTERVAL 7 DAY
GROUP BY date
ORDER BY date DESC
```

### Distancia Promedio por Grupo de Edad
```sql
SELECT 
    age_group,
    ROUND(AVG(distance_cm), 0) as avg_distance_cm,
    MIN(distance_cm) as min_distance,
    MAX(distance_cm) as max_distance
FROM analytics.sessions_raw_ch
GROUP BY age_group
ORDER BY avg_distance_cm
```

### Sesiones Activas en Tiempo Real (últimos 5 minutos)
```sql
SELECT 
    COUNT(*) as recent_sessions,
    COUNT(DISTINCT device_id) as active_devices
FROM analytics.sessions_raw_ch
WHERE insert_time >= now() - INTERVAL 5 MINUTE
```

## Crear Dashboard en ClickHouse Cloud Console

### Paso 1: Acceder a SQL Console
1. Login en tu ClickHouse Cloud
2. Ve a "SQL Console"
3. Selecciona database `analytics`

### Paso 2: Crear Charts
Para cada query, crea un chart:

1. **KPIs Principales (Single Value)**
   - Total Sesiones
   - TPA %
   - Dwell Time Promedio

2. **Gráficos de Línea (Line Chart)**
   - Sesiones por Hora (últimas 24h)
   - Tendencia Semanal

3. **Gráficos de Barra (Bar Chart)**
   - Top Horas Pico
   - Distribución por Edad

4. **Gráficos de Pie (Pie Chart)**
   - Distribución por Género
   - Distribución por Edad

5. **Tabla (Table)**
   - Análisis Cruzado Edad x Género
   - Métricas por Dispositivo

### Paso 3: Organizar Dashboard
1. Crea un nuevo Dashboard
2. Arrastra los charts creados
3. Organiza en secciones:
   - **Header**: KPIs principales
   - **Tendencias**: Gráficos de línea temporales
   - **Demografía**: Pie charts y bar charts
   - **Detalle**: Tablas con análisis detallado

### Paso 4: Configurar Auto-refresh
- Set refresh interval: 30 segundos o 1 minuto
- Esto mantendrá el dashboard actualizado en tiempo real

## Alternativa: Usar Grafana

Si prefieres Grafana (más personalizable):

1. Instala plugin de ClickHouse en Grafana
2. Configura datasource con credenciales Cloud
3. Importa queries como panels
4. Personaliza visualizaciones

```bash
# Grafana ya está en tu docker-compose
# Solo necesitas configurar el datasource de ClickHouse Cloud
```

## Queries de Mantenimiento

### Limpiar datos antiguos (> 30 días)
```sql
DELETE FROM analytics.sessions_raw_ch
WHERE start_time < now() - INTERVAL 30 DAY
```

### Ver uso de almacenamiento
```sql
SELECT 
    table,
    formatReadableSize(sum(bytes)) as size
FROM system.parts
WHERE database = 'analytics'
GROUP BY table
```
