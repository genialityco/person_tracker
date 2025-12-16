"""ClickHouse client and operations."""
import clickhouse_connect
from typing import List, Dict, Any
from config.settings import settings
from utils.logger import log


class ClickHouseClient:
    """Cliente de ClickHouse para analítica OLAP."""
    
    def __init__(self):
        self.client = None
    
    def connect(self):
        """Establece conexión con ClickHouse."""
        try:
            # Detectar si es ClickHouse Cloud (usa HTTPS)
            secure = settings.clickhouse_port == 8443 or '.clickhouse.cloud' in settings.clickhouse_host
            
            self.client = clickhouse_connect.get_client(
                host=settings.clickhouse_host,
                port=settings.clickhouse_port,
                username=settings.clickhouse_user,
                password=settings.clickhouse_password,
                database=settings.clickhouse_database,
                secure=secure  # Habilitar HTTPS para Cloud
            )
            log.info(f"✓ Conectado a ClickHouse: {settings.clickhouse_host}:{settings.clickhouse_port}")
        except Exception as e:
            log.error(f"✗ Error conectando a ClickHouse: {e}")
            raise
    
    def create_tables(self):
        """Crea las tablas necesarias si no existen."""
        try:
            # Tabla principal de sesiones
            self.client.command("""
                CREATE TABLE IF NOT EXISTS sessions_raw_ch (
                    session_id String,
                    start_time DateTime,
                    device_id UInt32,
                    duration_seconds UInt32,
                    attention_seconds Float32,
                    age_group String,
                    gender String,
                    distance_cm UInt32,
                    firmware_version String,
                    model_version String,
                    tracker_version String,
                    insert_time DateTime DEFAULT now()
                ) ENGINE = MergeTree()
                PARTITION BY toYYYYMM(start_time)
                ORDER BY (device_id, start_time)
            """)
            
            # Materialized view para métricas por hora (sin attention_rate como columna)
            self.client.command("DROP VIEW IF EXISTS hourly_metrics")
            self.client.command("""
                CREATE MATERIALIZED VIEW hourly_metrics
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
                FROM sessions_raw_ch
                GROUP BY device_id, hour, age_group, gender
            """)
            
            log.info("✓ Tablas de ClickHouse creadas/verificadas")
        except Exception as e:
            log.error(f"✗ Error creando tablas: {e}")
            raise
    
    def insert_session(self, session_data: Dict[str, Any]):
        """
        Inserta una sesión en ClickHouse.
        
        Args:
            session_data: Datos de la sesión
        """
        try:
            from datetime import datetime
            
            # Generar session_id si no existe
            session_id = session_data.get('_id', str(session_data.get('start_time', '')))
            
            # Convertir start_time de string a datetime si es necesario
            start_time = session_data['start_time']
            if isinstance(start_time, str):
                # Parsear string ISO format con timezone
                start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            
            data = [(
                session_id,
                start_time,
                session_data['device_id'],
                session_data['duration_seconds'],
                session_data['attention_seconds'],
                session_data.get('coordinates', {}).get('x', 0),
                session_data.get('coordinates', {}).get('y', 0),
                session_data['demographics']['age_group'],
                session_data['demographics']['gender_estimation'],
                session_data['demographics']['distance_cm'],
                session_data['meta']['firmware_version'],
                session_data['meta'].get('model_version', 'unknown'),
                session_data['meta'].get('tracker_version', 'BoT-SORT')
            )]
            
            self.client.insert(
                'sessions_raw_ch',
                data,
                column_names=[
                    'session_id', 'start_time', 'device_id', 'duration_seconds',
                    'attention_seconds', 'coordinate_x', 'coordinate_y', 'age_group', 'gender',
                    'distance_cm', 'firmware_version', 'model_version',
                    'tracker_version'
                ]
            )
            
            log.debug(f"✓ Sesión insertada en ClickHouse (device={session_data['device_id']})")
        except Exception as e:
            log.error(f"✗ Error insertando en ClickHouse: {e}")
            raise
    
    def query(self, sql: str) -> List[Dict[str, Any]]:
        """
        Ejecuta una query SQL y retorna resultados.
        
        Args:
            sql: Query SQL
            
        Returns:
            List[Dict]: Resultados como lista de diccionarios
        """
        try:
            result = self.client.query(sql)
            return result.result_rows
        except Exception as e:
            log.error(f"✗ Error ejecutando query: {e}")
            raise
    
    def get_hourly_metrics(self, device_id: int, hours: int = 24):
        """
        Obtiene métricas por hora para un dispositivo.
        
        Args:
            device_id: ID del dispositivo
            hours: Número de horas hacia atrás
            
        Returns:
            List[Dict]: Métricas por hora
        """
        sql = f"""
            SELECT
                date_hour,
                device_id,
                total_people,
                avg_duration,
                avg_attention_s,
                avg_attention_rate
            FROM hourly_metrics
            WHERE device_id = {device_id}
              AND date_hour >= now() - INTERVAL {hours} HOUR
            ORDER BY date_hour DESC
        """
        return self.query(sql)
    
    def get_demographic_breakdown(self, device_id: int, days: int = 7):
        """
        Obtiene distribución demográfica.
        
        Args:
            device_id: ID del dispositivo
            days: Días hacia atrás
            
        Returns:
            List[Dict]: Distribución por edad/género
        """
        sql = f"""
            SELECT
                age_group,
                gender_estimation,
                count() as total_sessions,
                avg(attention_rate) as avg_attention_rate
            FROM sessions_raw_ch
            WHERE device_id = {device_id}
              AND start_time >= now() - INTERVAL {days} DAY
            GROUP BY age_group, gender_estimation
            ORDER BY total_sessions DESC
        """
        return self.query(sql)
    
    def close(self):
        """Cierra la conexión."""
        if self.client:
            self.client.close()
            log.info("✓ Conexión ClickHouse cerrada")


# Instancia global
clickhouse_client = ClickHouseClient()
