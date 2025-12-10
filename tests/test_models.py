"""
Test básico para el modelo SessionPayload.
"""
import pytest
from datetime import datetime
from models.session import SessionPayload, Demographics, Meta


def test_session_payload_valid():
    """Test de creación de SessionPayload válido."""
    payload = SessionPayload(
        device_id=12,
        start_time=datetime.now(),
        duration_seconds=14,
        attention_seconds=9.4,
        demographics=Demographics(
            age_group="25-34",
            gender_estimation="male",
            distance_cm=180
        ),
        meta=Meta(
            firmware_version="1.8.2",
            model_version="yolov8n"
        )
    )
    
    assert payload.device_id == 12
    assert payload.duration_seconds == 14
    assert payload.attention_seconds == 9.4
    assert payload.get_attention_rate() == pytest.approx(0.671, rel=0.01)


def test_session_payload_invalid_attention():
    """Test de validación: attention_seconds > duration_seconds."""
    with pytest.raises(ValueError):
        SessionPayload(
            device_id=12,
            start_time=datetime.now(),
            duration_seconds=10,
            attention_seconds=15,  # Inválido
            demographics=Demographics(
                age_group="25-34",
                gender_estimation="male",
                distance_cm=180
            ),
            meta=Meta(firmware_version="1.8.2")
        )


def test_demographics_invalid_age_group():
    """Test de validación de age_group."""
    with pytest.raises(ValueError):
        Demographics(
            age_group="invalid",  # Inválido
            gender_estimation="male",
            distance_cm=180
        )
