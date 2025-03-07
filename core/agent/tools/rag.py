"""MilvusStorage class."""
import os
import json
import hashlib
from typing import Optional, List

from pymilvus import MilvusClient
from langchain_milvus import Milvus
from langchain_core.tools.simple import Tool
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from langchain.tools.retriever import create_retriever_tool


class MilvusStorage:
    def __init__(self, collection_name):
        self.milvus_url = os.getenv("MILVUS_URL")
        self.embeddings_model = OpenAIEmbeddings(
            model=os.getenv("EMBEDDINGS_MODEL"), api_key=os.getenv("OPENAI_API_KEY")
        )
        self.collection_name = collection_name


    def _deterministic_hash(self, text: str) -> str:
        text_bytes = text.encode("utf-8")
        hash_object = hashlib.sha256(text_bytes)
        return hash_object.hexdigest()


    def _delete_by_ids(self, ids: List[str]) -> None:
        try:
            client = MilvusClient(uri=self.milvus_url)
            client.load_collection(self.collection_name)
            res = client.get(collection_name=self.collection_name, ids=ids)
            if len(res) != 0:
                client.delete(collection_name=self.collection_name, ids=ids)
            else:
                print("No documents to delete.")
                return
            client.close()
        except Exception as e:
            print(f"Error deleting documents by ids: {e}")


    def use_collection(
        self, partition_key_field: str = "namespace"
    ) -> Optional[Milvus]:
        try:
            print(f"Intentando conectar a Milvus en: {self.milvus_url}")
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
            print("Conexión establecida, añadiendo documento dummy")
            vector_storage.add_documents(
                documents=[
                    Document(
                        metadata={
                            partition_key_field: "",
                            "source": "",
                            "page": 0,
                            "author": "",
                        },
                        page_content="",
                    )
                ],
                ids=["1a"],
            )
            return vector_storage
        except Exception as e:
            print(f"Error al conectar a Milvus: {type(e).__name__} - {str(e)}")
            return None


    def upsert_files(
        self, vectorstore: Milvus, docs: List[Document]
    ) -> Optional[List[str]]:
        if docs is None or len(docs) == 0:
            print("No documents to upsert.")
            return None
        try:
            uuids = [self._deterministic_hash(json.dumps(doc.metadata)) for doc in docs]
            self._delete_by_ids(uuids)
            ids = vectorstore.add_documents(docs, ids=uuids)
            return ids
        except Exception as e:
            print(f"Error upserting documents: {e}")
            return None


    def create_retriver_tool(
        self, vectorstore: Milvus, namespace: str
    ) -> Optional[Tool]:
        if vectorstore is None:
            print("Error: vectorstore es None, no se puede crear el retriever")
            return None
        try:
            retriever = vectorstore.as_retriever(
                search_kwargs={
                    "expr": f"namespace == '{namespace}'",
                    "k": 2,
                    "metric_type": "COSINE",
                    "score_threshold": 0.8,
                }
            )
            retriever_tool = create_retriever_tool(
                retriever, name="Milvus_RAG", description=" "
            )
            return retriever_tool
        except Exception as e:
            print(f"Error creando RAG: {e}")
            return None
