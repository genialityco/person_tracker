"""
Configuration settings using Pydantic Settings.
Carga variables desde .env automáticamente.
"""
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # Edge Device
    device_id: int = Field(default=12)
    session_timeout: int = Field(default=3)
    firmware_version: str = Field(default="1.8.2")
    model_version: str = Field(default="yolov8n")
    
    # Camera (Video file, RealSense or Standard)
    video_path: str = Field(default="")
    realsense_width: int = Field(default=640)
    realsense_height: int = Field(default=480)
    realsense_fps: int = Field(default=30)
    camera_id: int = Field(default=0)
    max_detection_distance: int = Field(default=500)
    
    # YOLO
    yolo_model_path: str = Field(default="models/yolov8n.pt")
    yolo_confidence: float = Field(default=0.5)
    yolo_iou_threshold: float = Field(default=0.45)
    yolo_device: str = Field(default="0")  # "0" para GPU, "cpu" para CPU
    
    # Tracker
    max_age: int = Field(default=30)
    min_hits: int = Field(default=3)
    iou_threshold: float = Field(default=0.3)
    
    # API
    api_url: str = Field(default="http://localhost:8000")
    api_timeout: int = Field(default=10)
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    api_workers: int = Field(default=4)
    api_key: str = Field(default="your-secret-api-key-here")
    
    # MongoDB
    mongo_uri: str = Field(default="mongodb://localhost:27017")
    mongo_db: str = Field(default="person_tracking")
    mongo_collection: str = Field(default="sessions")
    
    # Kafka
    kafka_bootstrap_servers: str = Field(default="localhost:9092")
    kafka_topic: str = Field(default="session_events")
    kafka_consumer_group: str = Field(default="session_processor")
    
    # ClickHouse
    clickhouse_host: str = Field(default="localhost")
    clickhouse_port: int = Field(default=8123)  # Puerto HTTP (9000 es para clickhouse-client)
    clickhouse_user: str = Field(default="default")
    clickhouse_password: str = Field(default="")
    clickhouse_database: str = Field(default="analytics")
    
    # Logging
    log_level: str = Field(default="INFO")
    log_file: str = Field(default="logs/app.log")
    
    # Display
    show_display: bool = Field(default=False)  # Mostrar ventana con detecciones
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
