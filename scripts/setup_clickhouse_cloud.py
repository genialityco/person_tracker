"""
Script para configurar ClickHouse Cloud con las tablas necesarias.
"""
import sys
from pathlib import Path

# Agregar directorio raíz al path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from db.clickhouse import ClickHouseClient
from utils.logger import log


def setup_clickhouse_cloud():
    """Configura tablas en ClickHouse Cloud."""
    
    log.info("=" * 60)
    log.info("🔧 Configurando ClickHouse Cloud")
    log.info("=" * 60)
    
    client = ClickHouseClient()
    
    try:
        # Conectar
        log.info("📡 Conectando a ClickHouse Cloud...")
        client.connect()
        
        # Crear database
        log.info("📊 Creando database analytics...")
        client.client.command("CREATE DATABASE IF NOT EXISTS analytics")
        
        # Crear tabla principal
        log.info("📋 Creando tabla sessions_raw_ch...")
        client.client.command("""
            CREATE TABLE IF NOT EXISTS analytics.sessions_raw_ch
            (
                session_id String,
                device_id UInt32,
                start_time DateTime,
                duration_seconds UInt32,
                attention_seconds Float32,
                age_group String,
                gender String,
                distance_cm UInt32,
                firmware_version String,
                model_version String,
                tracker_version String,
                insert_time DateTime DEFAULT now()
            )
            ENGINE = MergeTree()
            ORDER BY (device_id, start_time)
        """)
        
        # Crear vista materializada
        log.info("📈 Creando vista materializada hourly_metrics...")
        client.client.command("DROP VIEW IF EXISTS analytics.hourly_metrics")
        client.client.command("""
            CREATE MATERIALIZED VIEW analytics.hourly_metrics
            ENGINE = SummingMergeTree()
            ORDER BY (device_id, hour, age_group, gender)
            AS SELECT
                device_id,
                toStartOfHour(start_time) AS hour,
                age_group,
                gender,
                count() AS session_count,
                sum(duration_seconds) AS total_duration,
                sum(attention_seconds) AS total_attention,
                avg(distance_cm) AS avg_distance
            FROM analytics.sessions_raw_ch
            GROUP BY device_id, hour, age_group, gender
        """)
        
        # Verificar
        log.info("✅ Verificando tablas creadas...")
        tables = client.client.command("SHOW TABLES FROM analytics")
        log.info(f"   Tablas: {tables}")
        
        log.info("=" * 60)
        log.info("✓ ClickHouse Cloud configurado exitosamente")
        log.info("=" * 60)
        
        # Mostrar queries útiles
        log.info("\n📊 Queries útiles:")
        log.info("   Ver sesiones: SELECT * FROM analytics.sessions_raw_ch LIMIT 10")
        log.info("   Ver métricas: SELECT * FROM analytics.hourly_metrics LIMIT 10")
        log.info("   Dashboard URL: Accede a tu ClickHouse Cloud console")
        
    except Exception as e:
        log.error(f"✗ Error configurando ClickHouse Cloud: {e}")
        raise


if __name__ == "__main__":
    setup_clickhouse_cloud()
