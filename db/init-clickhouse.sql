-- ClickHouse Initialization Script
-- Crea base de datos y tablas necesarias

-- Crear base de datos si no existe
CREATE DATABASE IF NOT EXISTS analytics;

USE analytics;

-- Tabla principal: Sesiones raw
CREATE TABLE IF NOT EXISTS sessions_raw_ch (
    start_time DateTime,
    device_id UInt32,
    duration_seconds Int32,
    attention_seconds Float32,
    coordinate_x Int32,
    coordinate_y Int32,
    age_group String,
    gender_estimation String,
    distance_cm Int32,
    firmware_version String,
    model_version String,
    attention_rate Float32
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(start_time)
ORDER BY (start_time, device_id)
SETTINGS index_granularity = 8192;

-- Materialized View: Métricas por hora
CREATE MATERIALIZED VIEW IF NOT EXISTS hourly_metrics
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(date_hour)
ORDER BY (date_hour, device_id)
AS SELECT
    toStartOfHour(start_time) as date_hour,
    device_id,
    count() as total_people,
    avg(duration_seconds) as avg_duration,
    avg(attention_seconds) as avg_attention_s,
    avg(attention_rate) as avg_attention_rate,
    sum(duration_seconds) as total_duration,
    sum(attention_seconds) as total_attention
FROM sessions_raw_ch
GROUP BY date_hour, device_id;

-- Materialized View: Métricas diarias
CREATE MATERIALIZED VIEW IF NOT EXISTS daily_metrics
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(date_day)
ORDER BY (date_day, device_id)
AS SELECT
    toDate(start_time) as date_day,
    device_id,
    count() as total_people,
    avg(duration_seconds) as avg_duration,
    avg(attention_seconds) as avg_attention_s,
    avg(attention_rate) as avg_attention_rate,
    sum(duration_seconds) as total_duration,
    sum(attention_seconds) as total_attention
FROM sessions_raw_ch
GROUP BY date_day, device_id;

-- Materialized View: Segmentación demográfica por día
CREATE MATERIALIZED VIEW IF NOT EXISTS demographic_daily
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(date_day)
ORDER BY (date_day, device_id, age_group, gender_estimation)
AS SELECT
    toDate(start_time) as date_day,
    device_id,
    age_group,
    gender_estimation,
    count() as total_sessions,
    avg(attention_rate) as avg_attention_rate,
    avg(duration_seconds) as avg_duration
FROM sessions_raw_ch
GROUP BY date_day, device_id, age_group, gender_estimation;

-- Tabla para KPIs en tiempo real (últimas 24h)
CREATE TABLE IF NOT EXISTS kpi_realtime (
    timestamp DateTime,
    device_id UInt32,
    metric_name String,
    metric_value Float64
) ENGINE = MergeTree()
PARTITION BY toYYYYMMDD(timestamp)
ORDER BY (timestamp, device_id, metric_name)
TTL timestamp + INTERVAL 7 DAY;
