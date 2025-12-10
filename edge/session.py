"""
Session Manager - Gestiona sesiones anónimas temporales.
Los IDs locales NUNCA salen del Edge, se destruyen después del timeout.
"""
import time
from datetime import datetime
from typing import Dict, Optional
import numpy as np
from config.settings import settings
from utils.logger import log


class Session:
    """Representa una sesión anónima temporal de una persona."""
    
    def __init__(self, track_id: int, start_time: float):
        """
        Args:
            track_id: ID local temporal (RAM only, nunca se transmite)
            start_time: Timestamp de inicio (time.time())
        """
        self.track_id = track_id  # PRIVADO - Solo en RAM
        self.start_time = start_time
        self.last_seen = start_time
        
        # Métricas acumuladas
        self.total_frames = 0
        self.attention_frames = 0
        self.distances = []  # Distancias registradas en cm
        
        # Estimaciones demográficas (opcionales)
        self.age_estimates = []
        self.gender_estimates = []
        self.demographics_estimated = False  # Flag para saber si ya se estimó
    
    def update(self, is_looking: bool, distance_cm: Optional[float] = None):
        """
        Actualiza la sesión con una nueva observación.
        
        Args:
            is_looking: True si la persona está mirando la pantalla
            distance_cm: Distancia a la pantalla en cm (opcional)
        """
        self.last_seen = time.time()
        self.total_frames += 1
        
        if is_looking:
            self.attention_frames += 1
        
        if distance_cm is not None:
            self.distances.append(distance_cm)
    
    def add_demographic_estimate(self, age_group: str, gender: str):
        """
        Añade estimación demográfica (no biométrica).
        
        Args:
            age_group: Grupo de edad estimado
            gender: Género estimado
        """
        if age_group:
            self.age_estimates.append(age_group)
        if gender:
            self.gender_estimates.append(gender)
        self.demographics_estimated = True
    
    def is_expired(self, timeout: int) -> bool:
        """
        Verifica si la sesión ha expirado.
        
        Args:
            timeout: Timeout en segundos
            
        Returns:
            bool: True si expiró
        """
        return (time.time() - self.last_seen) > timeout
    
    def get_duration_seconds(self) -> int:
        """Retorna duración total en segundos."""
        return int(self.last_seen - self.start_time)
    
    def get_attention_seconds(self, fps: float = 30.0) -> float:
        """
        Calcula tiempo de atención en segundos.
        
        Args:
            fps: Frames por segundo del video
            
        Returns:
            float: Tiempo de atención en segundos
        """
        return self.attention_frames / fps
    
    def get_avg_distance_cm(self) -> int:
        """Retorna distancia promedio en cm."""
        if not self.distances:
            return 0
        return int(np.mean(self.distances))
    
    def get_most_common_age_group(self) -> str:
        """Retorna el grupo de edad más común."""
        if not self.age_estimates:
            return "unknown"
        return max(set(self.age_estimates), key=self.age_estimates.count)
    
    def get_most_common_gender(self) -> str:
        """Retorna el género más común."""
        if not self.gender_estimates:
            return "unknown"
        return max(set(self.gender_estimates), key=self.gender_estimates.count)
    
    def to_payload(self, device_id: int, firmware_version: str, model_version: str) -> dict:
        """
        Genera el payload anónimo para enviar al API.
        NOTA: NO incluye track_id (privado).
        
        Args:
            device_id: ID del dispositivo Edge
            firmware_version: Versión del firmware
            model_version: Versión del modelo YOLO
            
        Returns:
            dict: Payload anónimo de sesión
        """
        return {
            "device_id": device_id,
            "start_time": datetime.fromtimestamp(self.start_time).isoformat() + "Z",
            "duration_seconds": self.get_duration_seconds(),
            "attention_seconds": self.get_attention_seconds(),
            "demographics": {
                "age_group": self.get_most_common_age_group(),
                "gender_estimation": self.get_most_common_gender(),
                "distance_cm": self.get_avg_distance_cm()
            },
            "meta": {
                "firmware_version": firmware_version,
                "model_version": model_version,
                "tracker_version": "BoT-SORT"
            }
        }


class SessionManager:
    """Gestor de sesiones anónimas temporales."""
    
    def __init__(self, timeout: int = None, fps: float = 30.0):
        """
        Args:
            timeout: Timeout de sesión en segundos (default: desde settings)
            fps: Frames por segundo
        """
        self.timeout = timeout or settings.session_timeout
        self.fps = fps
        self.sessions: Dict[int, Session] = {}  # {track_id: Session}
        self.completed_count = 0
        
        log.info(f"SessionManager inicializado (timeout={self.timeout}s)")
    
    def update_session(
        self,
        track_id: int,
        is_looking: bool,
        distance_cm: Optional[float] = None,
        age_group: Optional[str] = None,
        gender: Optional[str] = None
    ):
        """
        Actualiza o crea sesión para un track_id.
        
        Args:
            track_id: ID del track (local, temporal)
            is_looking: ¿Está mirando la pantalla?
            distance_cm: Distancia en cm
            age_group: Grupo de edad estimado
            gender: Género estimado
        """
        if track_id not in self.sessions:
            # Crear nueva sesión
            self.sessions[track_id] = Session(track_id, time.time())
            log.debug(f"Nueva sesión iniciada: track_id={track_id}")
        
        # Actualizar sesión existente
        session = self.sessions[track_id]
        session.update(is_looking, distance_cm)
        
        if age_group or gender:
            session.add_demographic_estimate(age_group, gender)
    
    def get_expired_sessions(self) -> list:
        """
        Obtiene sesiones expiradas y las elimina del manager.
        
        Returns:
            list: Lista de objetos Session expirados
        """
        expired = []
        to_remove = []
        
        for track_id, session in self.sessions.items():
            if session.is_expired(self.timeout):
                expired.append(session)
                to_remove.append(track_id)
        
        # Eliminar sesiones expiradas (destruir IDs locales)
        for track_id in to_remove:
            del self.sessions[track_id]
            self.completed_count += 1
            log.debug(f"Sesión completada y destruida: track_id={track_id}")
        
        return expired
    
    def get_active_count(self) -> int:
        """Retorna número de sesiones activas."""
        return len(self.sessions)
    
    def generate_payloads(self, expired_sessions: list) -> list:
        """
        Genera payloads anónimos para sesiones expiradas.
        
        Args:
            expired_sessions: Lista de sesiones expiradas
            
        Returns:
            list: Lista de payloads anónimos
        """
        payloads = []
        
        for session in expired_sessions:
            # Filtrar sesiones muy cortas (< 1 segundo)
            if session.get_duration_seconds() < 1:
                continue
            
            payload = session.to_payload(
                device_id=settings.device_id,
                firmware_version=settings.firmware_version,
                model_version=settings.model_version
            )
            payloads.append(payload)
        
        return payloads
    
    def get_stats(self) -> dict:
        """Retorna estadísticas del manager."""
        return {
            "active_sessions": self.get_active_count(),
            "completed_sessions": self.completed_count,
            "timeout_seconds": self.timeout
        }
