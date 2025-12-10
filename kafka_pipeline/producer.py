"""
Kafka Producer - Envía sesiones a Kafka para procesamiento analítico.
"""
from confluent_kafka import Producer
from config.settings import settings
from utils.logger import log
import json


class KafkaProducer:
    """Producer de Kafka para eventos de sesión."""
    
    def __init__(self):
        """Inicializa el producer."""
        self.producer = None
        self.topic = settings.kafka_topic
    
    def connect(self):
        """Establece conexión con Kafka."""
        try:
            config = {
                'bootstrap.servers': settings.kafka_bootstrap_servers,
                'client.id': f'edge-producer-{settings.device_id}',
                'acks': 'all',  # Confirmación de todos los brokers
                'retries': 3,
                'max.in.flight.requests.per.connection': 5,
                'compression.type': 'snappy'
            }
            
            self.producer = Producer(config)
            log.info(f"✓ Kafka Producer conectado: {settings.kafka_bootstrap_servers}")
            
        except Exception as e:
            log.error(f"✗ Error conectando Kafka Producer: {e}")
            raise
    
    def _delivery_callback(self, err, msg):
        """Callback para confirmación de entrega."""
        if err:
            log.error(f"✗ Mensaje no entregado: {err}")
        else:
            log.debug(
                f"✓ Mensaje entregado: topic={msg.topic()}, "
                f"partition={msg.partition()}, offset={msg.offset()}"
            )
    
    def send_session(self, session_data: dict):
        """
        Envía una sesión a Kafka.
        
        Args:
            session_data: Diccionario con datos de sesión
        """
        try:
            # Serializar a JSON
            message = json.dumps(session_data, default=str)
            
            # Enviar mensaje
            self.producer.produce(
                topic=self.topic,
                key=str(session_data['device_id']),  # Particionar por device_id
                value=message,
                callback=self._delivery_callback
            )
            
            # Flush asíncrono (no bloqueante)
            self.producer.poll(0)
            
        except Exception as e:
            log.error(f"✗ Error enviando mensaje a Kafka: {e}")
            raise
    
    def flush(self):
        """Flush de mensajes pendientes."""
        if self.producer:
            self.producer.flush()
    
    def close(self):
        """Cierra el producer."""
        if self.producer:
            self.flush()
            log.info("✓ Kafka Producer cerrado")
