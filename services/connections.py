"""Redis and Milvus connection services using singleton pattern."""
import os
import logging
from typing import Optional

from redis import Redis
from fastapi import HTTPException

from .agent import MilvusStorage


logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Singleton class to manage database connections throughout the application.
    Ensures only one connection is created for each service.
    """
    _redis_instance: Optional[Redis] = None
    _milvus_instance: Optional[MilvusStorage] = None
    
    @classmethod
    def get_redis_conn(cls) -> Optional[Redis]:
        """
        Returns a singleton Redis connection.
        
        Returns:
            Optional[Redis]: The Redis connection instance
        """
        if cls._redis_instance is None:
            try:
                redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
                logger.info(f"Conectando a Redis en {redis_url}")
                redis_client = Redis.from_url(redis_url, db=0)
                test_result = redis_client.ping()
                if test_result:
                    logger.info("Conexión exitosa a Redis")
                    cls._redis_instance = redis_client
                else:
                    logger.error("No se a conectado a Redis")
                    return None
            except Exception as e:
                logger.error(f"Error al conectar con Redis: {e}")
                raise HTTPException(status_code=500, detail="Error de conexión a Redis")
        
        return cls._redis_instance

    @classmethod
    def get_milvus_conn(cls) -> Optional[MilvusStorage]:
        """
        Returns a singleton Milvus connection.
        
        Returns:
            Optional[MilvusStorage]: The Milvus connection instance
        """
        if cls._milvus_instance is None:
            try:
                collection_name = os.getenv("MILVUS_COLLECTION", "zolkin_collection")
                logger.info(f"Conectando a Milvus en {collection_name}")
                milvus_client = MilvusStorage(collection_name)
                logger.info("Conexión exitosa a Milvus")
                cls._milvus_instance = milvus_client
            except Exception as e:
                logger.error(f"Error al conectar con Milvus: {e}")
                raise HTTPException(status_code=500, detail="Error de conexión a Milvus")
        
        return cls._milvus_instance


# Convenience functions to maintain backward compatibility
def get_redis_conn() -> Optional[Redis]:
    """
    Get Redis connection using the singleton pattern.
    
    Returns:
        Optional[Redis]: Redis connection
    """
    return ConnectionManager.get_redis_conn()

def get_milvus_conn() -> Optional[MilvusStorage]:
    """
    Get Milvus connection using the singleton pattern.
    
    Returns:
        Optional[MilvusStorage]: Milvus connection
    """
    return ConnectionManager.get_milvus_conn()
    