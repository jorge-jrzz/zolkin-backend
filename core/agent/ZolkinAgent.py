"""ZolklinAgent class definition."""

import os
from typing import Any, List, Set

from dotenv import load_dotenv
from pymilvus import Collection, connections
from langchain_milvus import Milvus
from langchain_openai import ChatOpenAI
from langchain_core.tools.simple import Tool
from langchain_core.messages import SystemMessage
from langgraph.prebuilt import create_react_agent
from google.oauth2.credentials import Credentials

from core.agent.tools import MilvusStorage, get_google_toolkit
from core.agent.memory import RedisSaver


load_dotenv()


class ZolkinAgent:
    """ZolkinAgent class."""
    def __init__(self, 
                google_creds: Credentials,
                milvus_conn: MilvusStorage,
                milvus_storage: Milvus,
                partition_key_field: str):
        self.google_creds = google_creds
        self.milvus_conn = milvus_conn
        self.milvus_storage = milvus_storage
        self.partition_key_field = partition_key_field
        self._model = ChatOpenAI(model=os.getenv('OPENAI_MODEL'), api_key=os.getenv('OPENAI_API_KEY'))
        self._tools = None

    def _create_rag_tool(self) -> List[Tool]:
        return [self.milvus_conn.create_retriver_tool(self.milvus_storage, self.partition_key_field)]
    
    def _create_google_tools(self) -> List[Any]:
        return get_google_toolkit(self.google_creds)
    
    def _get_unique_filenames(self, namespace: str, collection_name: str) -> Set[str]:
        connections.connect("default", uri=os.getenv("MILVUS_URL"))
        collection = Collection(collection_name)
        results = collection.query( 
            expr=f"namespace == '{namespace}'", 
            output_fields=["source"]
        ) 
        names = [r['source'] for r in results]
        connections.disconnect("default")
        return set(names)
    
    def update_rag_tool_description(self, namespace: str, collection_name: str) -> str:
        return (
            "A Retrieval Augmented Generation tool using Milvus. "
            "This vector storage contains data from the following files: "
            f"{self._get_unique_filenames(namespace, collection_name)}"
        )
    
    def init_tools(self) -> Any:
        self._tools = self._create_google_tools() + self._create_rag_tool()
        return self
    
    def create_agent(self, memory: RedisSaver) -> Any:
        system_message = SystemMessage(content=(
            "You are a useful assistant and able to manage the user's email and calendar, "
            "you can also find valuable information in the RAG tool."
            "Respond in the same language as the user."
        ))
        return create_react_agent(
            model=self._model, 
            tools=self._tools,
            state_modifier=system_message,
            checkpointer=memory
        )
    
    def update_rag_description(self, collection_name: str):
        for tool in self._tools:
            if isinstance(tool, Tool) and tool.name == 'Milvus_RAG':
                tool.description = (
                    "A Retrieval Augmented Generation tool using Milvus. "
                    "This vector storage contains data from the following files: "
                    f"{self._get_unique_filenames(self.partition_key_field, collection_name)}"
                )
                break
