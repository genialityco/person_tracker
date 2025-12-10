"""MongoDB client and operations."""
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import PyMongoError
from config.settings import settings
from utils.logger import log


class MongoDBClient:
    """Cliente asíncrono de MongoDB para gestionar sesiones."""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
        self.collection = None
    
    async def connect(self):
        """Establece conexión con MongoDB."""
        try:
            self.client = AsyncIOMotorClient(settings.mongo_uri)
            self.db = self.client[settings.mongo_db]
            self.collection = self.db[settings.mongo_collection]
            
            # Crear índices
            await self._create_indexes()
            
            log.info(f"✓ Conectado a MongoDB: {settings.mongo_db}.{settings.mongo_collection}")
        except PyMongoError as e:
            log.error(f"✗ Error conectando a MongoDB: {e}")
            raise
    
    async def _create_indexes(self):
        """Crea índices optimizados para queries."""
        try:
            # Índice compuesto para queries temporales por dispositivo
            await self.collection.create_index([
                ("device_id", 1),
                ("start_time", 1)
            ])
            
            # Índice solo temporal para agregaciones
            await self.collection.create_index([("start_time", 1)])
            
            log.info("✓ Índices de MongoDB creados")
        except PyMongoError as e:
            log.warning(f"⚠ Error creando índices: {e}")
    
    async def insert_session(self, session_data: dict) -> str:
        """
        Inserta una nueva sesión.
        
        Args:
            session_data: Diccionario con datos de sesión
            
        Returns:
            str: ObjectId de la sesión insertada
        """
        try:
            result = await self.collection.insert_one(session_data)
            log.info(f"✓ Sesión insertada: {result.inserted_id}")
            return str(result.inserted_id)
        except PyMongoError as e:
            log.error(f"✗ Error insertando sesión: {e}")
            raise
    
    async def get_sessions(
        self,
        device_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100
    ):
        """
        Recupera sesiones con filtros opcionales.
        
        Args:
            device_id: Filtrar por dispositivo
            start_date: Fecha inicio (ISO format)
            end_date: Fecha fin (ISO format)
            limit: Número máximo de resultados
            
        Returns:
            list: Lista de sesiones
        """
        try:
            query = {}
            
            if device_id:
                query["device_id"] = device_id
            
            if start_date or end_date:
                query["start_time"] = {}
                if start_date:
                    query["start_time"]["$gte"] = start_date
                if end_date:
                    query["start_time"]["$lte"] = end_date
            
            cursor = self.collection.find(query).limit(limit).sort("start_time", -1)
            sessions = await cursor.to_list(length=limit)
            
            return sessions
        except PyMongoError as e:
            log.error(f"✗ Error recuperando sesiones: {e}")
            raise
    
    async def get_device_stats(self, device_id: int):
        """
        Obtiene estadísticas agregadas de un dispositivo.
        
        Args:
            device_id: ID del dispositivo
            
        Returns:
            dict: Estadísticas agregadas
        """
        try:
            pipeline = [
                {"$match": {"device_id": device_id}},
                {"$group": {
                    "_id": "$device_id",
                    "total_sessions": {"$sum": 1},
                    "avg_duration": {"$avg": "$duration_seconds"},
                    "avg_attention": {"$avg": "$attention_seconds"},
                    "total_duration": {"$sum": "$duration_seconds"}
                }}
            ]
            
            cursor = self.collection.aggregate(pipeline)
            result = await cursor.to_list(length=1)
            
            return result[0] if result else None
        except PyMongoError as e:
            log.error(f"✗ Error obteniendo stats: {e}")
            raise
    
    async def close(self):
        """Cierra la conexión."""
        if self.client:
            self.client.close()
            log.info("✓ Conexión MongoDB cerrada")


# Instancia global
mongodb_client = MongoDBClient()
