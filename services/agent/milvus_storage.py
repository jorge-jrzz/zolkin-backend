""""MilvusStorage class for managing document storage and retrieval in Milvus."""
import os
import json
import hashlib
import logging
from typing import Optional, List

from pymilvus import MilvusClient
from langchain_milvus import Milvus
from langchain_core.tools import Tool
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain.tools.retriever import create_retriever_tool


logger = logging.getLogger(__name__)


class MilvusStorage:
    """
    Clase para manejar el almacenamiento y recuperación de documentos en Milvus.
    Proporciona funcionalidades para insertar, actualizar y consultar vectores.
    """
    
    def __init__(self, collection_name: str):
        """
        Inicializa la conexión con Milvus.
        
        Args:
            collection_name: Nombre de la colección en Milvus
        """
        self.milvus_url = os.getenv("MILVUS_URL", "http://localhost:19530")
        self.embeddings_model = OpenAIEmbeddings(
            model=os.getenv("EMBEDDINGS_MODEL", "text-embedding-3-small"), 
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.collection_name = collection_name

    def _deterministic_hash(self, text: str) -> str:
        """
        Genera un hash determinístico para un texto dado.
        
        Args:
            text: Texto a hashear
            
        Returns:
            String con el hash SHA-256 hexadecimal
        """
        text_bytes = text.encode("utf-8")
        hash_object = hashlib.sha256(text_bytes)
        return hash_object.hexdigest()

    def _delete_by_ids(self, ids: List[str]) -> None:
        """
        Elimina documentos de Milvus por sus IDs.
        
        Args:
            ids: Lista de IDs a eliminar
        """
        try:
            client = MilvusClient(uri=self.milvus_url)
            client.load_collection(self.collection_name)
            res = client.get(collection_name=self.collection_name, ids=ids)
            if res and len(res) > 0:
                client.delete(collection_name=self.collection_name, ids=ids)
                logger.info(f"Eliminados {len(ids)} documentos de Milvus")
            else:
                logger.info("No se encontraron documentos para eliminar")
            client.close()
        except Exception as e:
            logger.error(f"Error eliminando documentos por IDs: {e}")

    def use_collection(self, partition_key_field: str = "namespace") -> Optional[Milvus]:
        """
        Inicializa y conecta a una colección de Milvus.
        
        Args:
            partition_key_field: Campo para particionar la colección
            
        Returns:
            Instancia de Milvus conectada o None si hay error
        """
        try:
            logger.info(f"Conectando a Milvus en: {self.milvus_url}")
            vector_storage = Milvus(
                embedding_function=self.embeddings_model,
                collection_name=self.collection_name,
                connection_args={"uri": self.milvus_url},
                drop_old=True,
                auto_id=False,
                primary_field="primary_key",
                index_params={"metric_type": "COSINE"},
                partition_key_field=partition_key_field,
            )
            
            # Añadir documento dummy para asegurar que la colección esté inicializada
            logger.info("Inicializando colección con documento dummy")
            vector_storage.add_documents(
                documents=[
                    Document(
                        metadata={
                            partition_key_field: "dummy",
                            "source": "initialization",
                            "page": 0,
                            "author": "system",
                        },
                        page_content="Documento de inicialización",
                    )
                ],
                ids=["init_doc_1"],
            )
            logger.info("Colección inicializada correctamente")
            return vector_storage
        except Exception as e:
            logger.error(f"Error al conectar a Milvus: {type(e).__name__} - {str(e)}")
            return None

    def upsert_files(self, vectorstore: Milvus, docs: List[Document]) -> Optional[List[str]]:
        """
        Inserta o actualiza documentos en el vectorstore.
        
        Args:
            vectorstore: Instancia de Milvus ya conectada
            docs: Lista de documentos a insertar/actualizar
            
        Returns:
            Lista de IDs de los documentos insertados o None si hay error
        """
        if not docs:
            logger.info("No hay documentos para actualizar")
            return None
        
        try:
            # Generar IDs determinísticos basados en metadatos
            uuids = [self._deterministic_hash(json.dumps(doc.metadata)) for doc in docs]
            
            # Eliminar documentos existentes con los mismos IDs
            self._delete_by_ids(uuids)
            
            # Insertar nuevos documentos
            ids = vectorstore.add_documents(docs, ids=uuids)
            logger.info(f"Insertados/actualizados {len(ids)} documentos en Milvus")
            return ids
        except Exception as e:
            logger.error(f"Error al insertar/actualizar documentos: {e}")
            return None

    def create_retriever_tool(self, vectorstore: Milvus, namespace: str) -> Optional[Tool]:
        """
        Crea una herramienta de recuperación para LangChain.
        
        Args:
            vectorstore: Instancia de Milvus ya conectada
            namespace: Espacio de nombres para filtrar la búsqueda
            
        Returns:
            Herramienta de recuperación o None si hay error
        """
        if vectorstore is None:
            logger.error("Error: vectorstore es None, no se puede crear el retriever")
            return None
        
        try:
            # Configurar el retriever con filtro por namespace
            retriever = vectorstore.as_retriever(
                search_kwargs={
                    "expr": f"namespace == '{namespace}'",
                    "k": 3,  # Aumentado a 3 para mejorar la recuperación de contexto
                    "metric_type": "COSINE",
                    "score_threshold": 0.75,  # Ajustado para mejor recall
                }
            )
            
            # Crear la herramienta de recuperación
            retriever_tool = create_retriever_tool(
                retriever, 
                name="buscar_informacion",
                description="Busca información relevante en la base de conocimiento. Útil para encontrar datos específicos sobre documentos o contexto del usuario."
            )
            logger.info(f"Herramienta de recuperación creada para namespace: {namespace}")
            return retriever_tool
        except Exception as e:
            logger.error(f"Error creando herramienta de recuperación: {e}")
            return None