"""
Modelos Pydantic para validación de datos de sesión.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class Coordinates(BaseModel):
    """Posición predominante de la persona durante la sesión."""
    x: int = Field(..., ge=0, description="Coordenada X (centro del bbox, mediana)")
    y: int = Field(..., ge=0, description="Coordenada Y (centro del bbox, mediana)")


class Demographics(BaseModel):
    """Datos demográficos estimados (no biométricos)."""
    age_group: str = Field(..., description="Rango de edad: '18-24', '25-34', '35-44', '45-54', '55+'")
    gender_estimation: str = Field(..., description="Estimación de género: 'male', 'female', 'unknown'")
    distance_cm: int = Field(..., ge=0, description="Distancia promedio en cm")
    
    @field_validator('age_group')
    @classmethod
    def validate_age_group(cls, v):
        valid_groups = ['0-17', '18-24', '25-34', '35-44', '45-54', '55-64', '65+', 'unknown']
        if v not in valid_groups:
            raise ValueError(f"age_group debe ser uno de: {valid_groups}")
        return v
    
    @field_validator('gender_estimation')
    @classmethod
    def validate_gender(cls, v):
        valid_genders = ['male', 'female', 'unknown']
        if v not in valid_genders:
            raise ValueError(f"gender_estimation debe ser uno de: {valid_genders}")
        return v


class Meta(BaseModel):
    """Metadata técnica del dispositivo."""
    firmware_version: str = Field(..., description="Versión del firmware Edge")
    model_version: Optional[str] = Field(default="yolov8n", description="Versión del modelo YOLO")
    tracker_version: Optional[str] = Field(default="BoT-SORT", description="Versión del tracker")


class SessionPayload(BaseModel):
    """
    Payload anónimo de sesión enviado desde el Edge.
    NO contiene imágenes, video ni IDs persistentes.
    """
    device_id: int = Field(..., ge=1, description="ID único del dispositivo/pantalla")
    start_time: datetime = Field(..., description="Timestamp de inicio de sesión (UTC)")
    duration_seconds: int = Field(..., ge=0, description="Duración total de la sesión en segundos")
    attention_seconds: float = Field(..., ge=0.0, description="Tiempo mirando la pantalla")
    coordinates: Coordinates = Field(..., description="Posición predominante durante la sesión")
    demographics: Demographics = Field(..., description="Datos demográficos estimados")
    meta: Meta = Field(..., description="Metadata técnica")
    
    @field_validator('attention_seconds')
    @classmethod
    def validate_attention(cls, v, info):
        """Validar que attention_seconds <= duration_seconds."""
        if 'duration_seconds' in info.data and v > info.data['duration_seconds']:
            raise ValueError("attention_seconds no puede ser mayor que duration_seconds")
        return v
    
    def get_attention_rate(self) -> float:
        """Calcula el TPA (Tiempo Promedio de Atención)."""
        if self.duration_seconds == 0:
            return 0.0
        return self.attention_seconds / self.duration_seconds
    
    class Config:
        json_schema_extra = {
            "example": {
                "device_id": 12,
                "start_time": "2025-12-09T14:30:00Z",
                "duration_seconds": 14,
                "attention_seconds": 9.4,
                "coordinates": {
                    "x": 640,
                    "y": 360
                },
                "demographics": {
                    "age_group": "25-34",
                    "gender_estimation": "male",
                    "distance_cm": 180
                },
                "meta": {
                    "firmware_version": "1.8.2",
                    "model_version": "yolov8n",
                    "tracker_version": "BoT-SORT"
                }
            }
        }


class SessionResponse(BaseModel):
    """Respuesta de la API al recibir una sesión."""
    success: bool
    session_id: str
    message: str
