import os
import json

import hashlib
from dotenv import load_dotenv
from typing import Optional, List, Set

from pymilvus import MilvusClient, Collection, connections, utility

from langchain_core.tools.simple import Tool
from langchain.tools.retriever import create_retriever_tool
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_milvus import Milvus


load_dotenv()


class MilvusStorage:
    def __init__(self, collection_name):
        self.milvus_url = os.getenv("MILVUS_URL")
        self.embeddings_model = OpenAIEmbeddings(model=os.getenv("EMBEDDINGS_MODEL"), api_key=os.getenv("OPENAI_API_KEY"))
        self.collection_name = collection_name

    def _deterministic_hash(self, text: str) -> str:
        text_bytes = text.encode('utf-8')
        hash_object = hashlib.sha256(text_bytes)
        return hash_object.hexdigest()
    
    def _delete_by_ids(self, ids: List[str]) -> None:
        try:
            client = MilvusClient(uri=self.milvus_url)
            client.load_collection(self.collection_name)
            res = client.get(
                collection_name=self.collection_name,
                ids=ids
            )
            if len(res) != 0: 
                client.delete(
                    collection_name=self.collection_name,
                    ids=ids
                )
            else:
                print("No documents to delete.")
                return
            client.close()
        except Exception as e:
            print(f"Error deleting documents by ids: {e}")

    # def _get_unique_filenames(self, namespace: str) -> Set[str]:
    #     connections.connect("default", uri=self.milvus_url)
    #     collection = Collection(self.collection_name)
    #     results = collection.query( 
    #         expr=f"namespace == '{namespace}'", 
    #         output_fields=["source"]
    #     ) 
    #     names = [r['source'] for r in results]
    #     connections.disconnect("default")
    #     return set(names)
    
    def use_collection(self, partition_key_field: str = "namespace") -> Optional[Milvus]:
        try:
            vector_storage = Milvus(
                embedding_function=self.embeddings_model,
                collection_name=self.collection_name,
                connection_args={"uri": self.milvus_url},
                drop_old=True,
                auto_id=False,
                primary_field="primary_key", 
                index_params={"metric_type": "COSINE"}, 
                partition_key_field=partition_key_field # Use the "namespace" field as the partition key
            )
            vector_storage.add_documents(
                documents=[Document(metadata={partition_key_field: '', 'source': '', 'page': 0, 'author': ''}, page_content='')],
                ids=['1a']
            )
            # self.upsert_files(
            #     vectorstore=vector_storage, 
            #     docs=[Document(metadata={'namespace': '', 'source': '', 'page': 0, 'author': ''}, page_content='')]
            # )
            return vector_storage
            # return Milvus.from_documents(
            #     documents=[Document(metadata={'namespace': '', 'source': '', 'page': 0, 'author': ''}, page_content='')],
            #     embedding=self.embeddings_model,
            #     collection_name=self.collection_name,
            #     connection_args={"uri": self.milvus_url},
            #     drop_old=True,
            #     auto_id=False,
            #     primary_field="primary_key", 
            #     index_params={"metric_type": "COSINE"}, 
            #     partition_key_field=partition_key_field # Use the "namespace" field as the partition key
            # )

            # connections.connect("default", uri=self.milvus_url) 
            # collections = utility.list_collections()
            # if not (self.collection_name in collections):
            #     vectorstorage.add_documents(
            #         [Document(metadata={'namespace': '', 'source': '', 'page': -1, 'author': ''}, page_content='')]
            #     )
            # connections.disconnect("default")
            # vectorstorage.add_documents(
            #     documents=[Document(metadata={'namespace': 'a', 'source': 'b', 'page': 0, 'author': 'c'}, page_content='d')], 
            #     ids=['e']
            #     )
            # return vectorstorage
        except Exception as e:
            print(f"Error for use a collection: {e}")
            return None

    def upsert_files(self, vectorstore: Milvus, docs: List[Document]) -> Optional[List[str]]:
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

    # def update_tool_description(self, namespace: str) -> str:
    #     return (
    #         "A Retrieval Augmented Generation tool using Milvus. "
    #         "This vector storage contains data from the following files: \n"
    #         f"{self._get_unique_filenames(namespace)}"
    #     )

    def create_retriver_tool(self, vectorstore: Milvus, namespace: str) -> Optional[Tool]:
        try:
            retriever = vectorstore.as_retriever(
                search_kwargs = {
                    "expr": f"namespace == '{namespace}'",
                    "k": 2, 
                    'metric_type': "COSINE",
                    'score_threshold': 0.8
                }
            )
            retriever_tool = create_retriever_tool(
                retriever, 
                name="Milvus_RAG",
                # description=self.update_tool_description(namespace)
                description=" "
            )
            return retriever_tool
        except Exception as e:
            print(f"Error creating RAG: {e}")
            return None



# docs = [
#     Document(metadata={'namespace': 'jorgeang33@gmail.com', 'source': 'example.pdf', 'page': 0, 'author': 'Jorge Angel Juarez Vazquez'}, page_content='Titulo\nEncabezado 1\nPara empezar ahora mismo, pulse el texto de cualquier marcador de posición (como este, por\nejemplo) y comience a escribir.\nPara aplicar facilmente cualquier formato de texto que vea en esta pagina, vaya al grupo\nEstilos, que encontrara en la pestana Inicio de la cinta de opciones.\n¢ Desea insertar una imagen de sus archivos o agregar una forma o un cuadro de texto?\n¡Adelante! En la pestaña Insertar de la cinta de opciones, pulse la opción que necesite.\n'),
#     Document(metadata={'namespace': 'jorgeang33@gmail.com', 'source': 'example.pdf', 'page': 1, 'author': 'Jorge Angel Juarez Vazquez'}, page_content='Esto es texto que esta en una imagen, en la segunda\npagina del documento, a continuación, información sobre\nlos perros:\nEl perro, llamado perro doméstico o can, y en algunos\nlugares coloquialmente llamado chucho, tuso, choco,\nentre otros; es un mamifero carnivoro de la familia de los\ncanidos, que constituye una especie del género Canis.\n')
# ]

# conn = MilvusStorage(collection_name="example")
# milvus = conn.use_collection()
# conn.upsert_files(milvus, docs)