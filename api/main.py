"""
FastAPI Application - API de ingesta de sesiones anónimas.
"""
from fastapi import FastAPI, HTTPException, Depends, Header
from contextlib import asynccontextmanager
from models.session import SessionPayload, SessionResponse
from db.mongodb import mongodb_client
from kafka_pipeline.producer import KafkaProducer
from config.settings import settings
from utils.logger import log


# Kafka producer global
kafka_producer = KafkaProducer()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manejo de lifecycle de la aplicación."""
    # Startup
    log.info("🚀 Iniciando API Server...")
    await mongodb_client.connect()
    kafka_producer.connect()
    log.info("✓ API Server listo")
    
    yield
    
    # Shutdown
    log.info("⚠ Cerrando API Server...")
    await mongodb_client.close()
    kafka_producer.close()
    log.info("✓ API Server cerrado")


app = FastAPI(
    title="Person Tracker API",
    description="API de ingesta para sesiones anónimas de tracking",
    version="1.0.0",
    lifespan=lifespan
)


# Dependency: API Key validation
async def verify_api_key(x_api_key: str = Header(...)):
    """Valida el API key."""
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key


@app.get("/")
async def root():
    """Health check."""
    return {
        "service": "Person Tracker API",
        "version": "1.0.0",
        "status": "healthy"
    }


@app.get("/health")
async def health():
    """Health check detallado."""
    return {
        "api": "healthy",
        "mongodb": "connected" if mongodb_client.client else "disconnected",
        "kafka": "connected" if kafka_producer.producer else "disconnected"
    }


@app.post("/sessions", response_model=SessionResponse)
async def create_session(
    session: SessionPayload,
    api_key: str = Depends(verify_api_key)
):
    """
    Recibe y procesa una sesión anónima desde un Edge device.
    
    Args:
        session: Payload de sesión validado por Pydantic
        api_key: API key (header)
        
    Returns:
        SessionResponse: Confirmación con session_id
    """
    try:
        # Convertir a dict para almacenamiento
        session_dict = session.model_dump()
        
        # 1. Guardar en MongoDB (fuente de verdad)
        session_id = await mongodb_client.insert_session(session_dict)
        
        # 2. Enviar a Kafka para procesamiento analítico
        kafka_producer.send_session(session_dict)
        
        log.info(
            f"✓ Sesión procesada: device={session.device_id}, "
            f"duration={session.duration_seconds}s, "
            f"attention={session.attention_seconds:.1f}s"
        )
        
        return SessionResponse(
            success=True,
            session_id=session_id,
            message="Session received and processed successfully"
        )
        
    except Exception as e:
        log.error(f"✗ Error procesando sesión: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions/device/{device_id}")
async def get_device_sessions(
    device_id: int,
    limit: int = 100,
    api_key: str = Depends(verify_api_key)
):
    """
    Obtiene sesiones de un dispositivo específico.
    
    Args:
        device_id: ID del dispositivo
        limit: Número máximo de resultados
        
    Returns:
        list: Lista de sesiones
    """
    try:
        sessions = await mongodb_client.get_sessions(
            device_id=device_id,
            limit=limit
        )
        
        # Convertir ObjectId a string
        for session in sessions:
            session['_id'] = str(session['_id'])
        
        return {
            "device_id": device_id,
            "count": len(sessions),
            "sessions": sessions
        }
        
    except Exception as e:
        log.error(f"✗ Error obteniendo sesiones: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions/device/{device_id}/stats")
async def get_device_stats(
    device_id: int,
    api_key: str = Depends(verify_api_key)
):
    """
    Obtiene estadísticas agregadas de un dispositivo.
    
    Args:
        device_id: ID del dispositivo
        
    Returns:
        dict: Estadísticas agregadas
    """
    try:
        stats = await mongodb_client.get_device_stats(device_id)
        
        if not stats:
            raise HTTPException(
                status_code=404,
                detail=f"No data found for device_id={device_id}"
            )
        
        # Calcular métricas adicionales
        stats['avg_attention_rate'] = (
            stats['avg_attention'] / stats['avg_duration']
            if stats['avg_duration'] > 0 else 0
        )
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"✗ Error obteniendo stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
