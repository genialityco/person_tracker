"""
Kafka Consumer - Consume sesiones de Kafka y las inserta en ClickHouse.
"""
from confluent_kafka import Consumer, KafkaError
from db.clickhouse import clickhouse_client
from config.settings import settings
from utils.logger import log
import json
import signal
import sys


class KafkaConsumer:
    """Consumer de Kafka para pipeline analítico."""
    
    def __init__(self):
        """Inicializa el consumer."""
        self.consumer = None
        self.running = False
    
    def connect(self):
        """Establece conexión con Kafka."""
        try:
            config = {
                'bootstrap.servers': settings.kafka_bootstrap_servers,
                'group.id': settings.kafka_consumer_group,
                'auto.offset.reset': 'earliest',
                'enable.auto.commit': True,
                'auto.commit.interval.ms': 5000,
                'max.poll.interval.ms': 300000
            }
            
            self.consumer = Consumer(config)
            self.consumer.subscribe([settings.kafka_topic])
            
            log.info(
                f"✓ Kafka Consumer conectado: topic={settings.kafka_topic}, "
                f"group={settings.kafka_consumer_group}"
            )
            
        except Exception as e:
            log.error(f"✗ Error conectando Kafka Consumer: {e}")
            raise
    
    def start(self):
        """Inicia el loop de consumo."""
        self.running = True
        
        # Conectar a ClickHouse
        clickhouse_client.connect()
        clickhouse_client.create_tables()
        
        log.info("🚀 Kafka Consumer iniciado - Procesando mensajes...")
        
        # Handler para shutdown graceful
        def signal_handler(sig, frame):
            log.info("⚠ Recibida señal de terminación...")
            self.running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            self._consume_loop()
        finally:
            self.close()
    
    def _consume_loop(self):
        """Loop principal de consumo."""
        message_count = 0
        
        while self.running:
            try:
                # Poll de mensajes (timeout 1s)
                msg = self.consumer.poll(timeout=1.0)
                
                if msg is None:
                    continue
                
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        # Fin de partición, normal
                        continue
                    else:
                        log.error(f"✗ Kafka error: {msg.error()}")
                        continue
                
                # Procesar mensaje
                self._process_message(msg)
                message_count += 1
                
                # Log periódico
                if message_count % 100 == 0:
                    log.info(f"📊 Procesados {message_count} mensajes")
                
            except Exception as e:
                log.error(f"✗ Error procesando mensaje: {e}")
    
    def _process_message(self, msg):
        """
        Procesa un mensaje de Kafka.
        
        Args:
            msg: Mensaje de Kafka
        """
        try:
            # Deserializar JSON
            session_data = json.loads(msg.value().decode('utf-8'))
            
            # Insertar en ClickHouse
            clickhouse_client.insert_session(session_data)
            
            log.debug(
                f"✓ Sesión procesada: device={session_data['device_id']}, "
                f"offset={msg.offset()}"
            )
            
        except json.JSONDecodeError as e:
            log.error(f"✗ Error decodificando JSON: {e}")
        except Exception as e:
            log.error(f"✗ Error insertando en ClickHouse: {e}")
    
    def close(self):
        """Cierra el consumer."""
        if self.consumer:
            self.consumer.close()
            log.info("✓ Kafka Consumer cerrado")
        
        clickhouse_client.close()


def main():
    """Entry point."""
    log.info("=" * 60)
    log.info("📊 Kafka → ClickHouse Consumer")
    log.info(f"   Topic: {settings.kafka_topic}")
    log.info(f"   Group: {settings.kafka_consumer_group}")
    log.info("=" * 60)
    
    consumer = KafkaConsumer()
    consumer.connect()
    consumer.start()


if __name__ == "__main__":
    main()
