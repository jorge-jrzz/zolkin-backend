"""Function to upsert a file into the RAG system."""
import logging
from pathlib import Path

from fastapi import HTTPException

from services import (
    AgentManager,
    OCRProcessor,
    manage_files,
    get_milvus_conn,
)


logger = logging.getLogger(__name__)


def upsert_file_to_rag(
        user_email: str,
        file_path: str,
        pdfs_dir: str,
    ) -> str:
    """
    Función para insertar un archivo en el sistema RAG.
    """
    # Instanciar el gestor de agentes
    agent_manager = AgentManager()

    # Obtener el agente asociado al usuario
    zolkin_agent = agent_manager.get_zolkin(user_email)
    if not zolkin_agent:
        logger.error(f"Agente no encontrado en caché para usuario: {user_email}")
        raise HTTPException(status_code=500, detail="Agente no encontrado en caché")
    
    # Procesar el archivo
    try:
        logger.info(f"Procesando archivo con FileManager para: {file_path}")
        pdf_file = manage_files(file_path, pdfs_dir)
        if not pdf_file:
            raise ValueError("Error al procesar el archivo a PDF")
        logger.info(f"Archivo procesado correctamente, PDF ubicado en {pdf_file}")
    except Exception as e:
        logger.error(f"Error al procesar el archivo con FileManager: {e}")
        raise HTTPException(status_code=500, detail="Error al procesar el archivo") from e
    
    # Aplicar OCR y cargar el contenido
    try:
        logger.info("Iniciando proceso de OCR en archivo PDF")
        ocr_processor = OCRProcessor()
        ocr_pdf = ocr_processor.ocr_pdf(pdf_file)
        if not ocr_pdf:
            raise ValueError("Error al aplicar OCR al PDF")
            
        file_content = ocr_processor.load_pdf(
            file_path=ocr_pdf, 
            namespace=user_email,
        )
        
        if not file_content:
            raise ValueError("Error al cargar el contenido del PDF")
            
        logger.info("OCR y carga de archivo completados correctamente")
    except Exception as e:
        logger.error(f"Error durante OCR o carga de archivo: {e}")
        raise HTTPException(status_code=500, detail="Error al procesar el archivo PDF") from e
    
    # Actualizar Milvus
    try:
        milvus_conn = get_milvus_conn()
        milvus_storage = milvus_conn.use_collection()
        if not milvus_storage:
            raise ValueError("Error al conectar con Milvus")
            
        logger.info("Actualizando almacenamiento Milvus con el contenido del archivo")
        milvus_conn.upsert_files(milvus_storage, file_content)
        logger.info("Almacenamiento Milvus actualizado correctamente")
    except Exception as e:
        logger.error(f"Error al actualizar el almacenamiento Milvus: {e}")
        raise HTTPException(status_code=500, detail="Error al actualizar el almacenamiento") from e
    
    # Actualizar la descripción RAG del agente
    try:
        logger.info("Actualizando descripción RAG del agente")
        zolkin_agent.update_rag_tool_description()
        logger.info("Descripción RAG del agente actualizada correctamente")
    except Exception as e:
        logger.error(f"Error al actualizar la descripción RAG del agente: {e}")
        raise HTTPException(status_code=500, detail="Error al actualizar la descripción del agente")from e
    
    return Path(pdf_file).name
