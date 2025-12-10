"""
Gaze estimation y cálculo de atención.
Soporta RealSense depth o estimación 2D como fallback.
"""
import numpy as np
from typing import Optional
from utils.logger import log


class GazeEstimator:
    """
    Estimador de atención basado en proximidad y orientación.
    NO usa biometría facial, solo posición espacial.
    Funciona con o sin depth data.
    """
    
    def __init__(self, screen_position: tuple = (0, 0, 0), screen_normal: tuple = (0, 0, 1)):
        """
        Args:
            screen_position: Posición 3D de la pantalla (x, y, z) en cm
            screen_normal: Vector normal de la pantalla (hacia el frente)
        """
        self.screen_position = np.array(screen_position)
        self.screen_normal = np.array(screen_normal)
        self.screen_normal = self.screen_normal / np.linalg.norm(self.screen_normal)
    
    def is_looking_at_screen(
        self,
        person_position: Optional[np.ndarray] = None,
        person_direction: Optional[np.ndarray] = None,
        angle_threshold: float = 45.0,
        bbox_center: Optional[tuple] = None,
        frame_size: Optional[tuple] = None
    ) -> bool:
        """
        Determina si una persona está mirando la pantalla.
        
        Args:
            person_position: Posición 3D de la persona [x, y, z] en cm (opcional con depth)
            person_direction: Vector de dirección de mirada (opcional)
            angle_threshold: Ángulo máximo en grados para considerar "mirando"
            bbox_center: (x, y) centro del bbox en pixels (fallback sin depth)
            frame_size: (width, height) del frame (fallback sin depth)
            
        Returns:
            bool: True si está mirando la pantalla
        """
        # Modo 1: Con posición 3D (RealSense)
        if person_position is not None:
            return self._is_looking_3d(person_position, person_direction, angle_threshold)
        
        # Modo 2: Sin depth, estimación 2D simple
        if bbox_center is not None and frame_size is not None:
            return self._is_looking_2d(bbox_center, frame_size)
        
        # Por defecto: asumir que sí está mirando
        return True
    
    def _is_looking_3d(
        self,
        person_position: np.ndarray,
        person_direction: Optional[np.ndarray],
        angle_threshold: float
    ) -> bool:
        """Estimación 3D con depth data."""
        if person_direction is None:
            # Vector desde persona hacia pantalla
            to_screen = self.screen_position - person_position
            to_screen_norm = to_screen / np.linalg.norm(to_screen)
            
            # Ángulo entre vector persona->pantalla y normal de pantalla
            angle = np.arccos(np.clip(np.dot(to_screen_norm, -self.screen_normal), -1.0, 1.0))
            angle_deg = np.degrees(angle)
            
            return angle_deg < angle_threshold
        else:
            # Con dirección de mirada explícita
            person_direction_norm = person_direction / np.linalg.norm(person_direction)
            
            to_screen = self.screen_position - person_position
            to_screen_norm = to_screen / np.linalg.norm(to_screen)
            
            angle = np.arccos(np.clip(np.dot(person_direction_norm, to_screen_norm), -1.0, 1.0))
            angle_deg = np.degrees(angle)
            
            return angle_deg < angle_threshold
    
    def _is_looking_2d(self, bbox_center: tuple, frame_size: tuple) -> bool:
        """
        Estimación 2D sin depth (fallback).
        Asume que si la persona está en la zona central del frame, está mirando.
        
        Args:
            bbox_center: (x, y) centro del bbox
            frame_size: (width, height) del frame
            
        Returns:
            bool: True si está en zona central
        """
        cx, cy = bbox_center
        width, height = frame_size
        
        # Calcular distancia del centro del frame
        frame_center_x = width / 2
        frame_center_y = height / 2
        
        # Distancia normalizada [0, 1]
        dist_x = abs(cx - frame_center_x) / (width / 2)
        dist_y = abs(cy - frame_center_y) / (height / 2)
        
        # Si está en el 70% central del frame, considerar "mirando"
        threshold = 0.7
        return dist_x < threshold and dist_y < threshold
    
    def get_distance_to_screen(self, person_position: Optional[np.ndarray]) -> float:
        """
        Calcula distancia perpendicular de persona a pantalla.
        
        Args:
            person_position: Posición 3D [x, y, z] en cm
            
        Returns:
            float: Distancia en cm (0 si no disponible)
        """
        if person_position is None:
            return 0.0
        
        to_screen = self.screen_position - person_position
        distance = abs(np.dot(to_screen, self.screen_normal))
        return distance

