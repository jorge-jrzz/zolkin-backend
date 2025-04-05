"""
File upload and processing routes for the Zolkin application.
"""
import os
import logging
from pathlib import Path

from fastapi.responses import JSONResponse
from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form

from services import get_milvus_conn
from services.agent import AgentManager
from services.files import FileManager, OCRProcessor, manage_files


logger = logging.getLogger(__name__)

# Crear el router
router = APIRouter(prefix="/upload_file", tags=["upload_file"])

# Instanciar el gestor de agentes
agent_manager = AgentManager()

# Configuración de rutas usando pathlib
# Update base directory to use local uploads path
BASE_DIR = Path(os.environ.get("BASE_DIR", "./uploads"))
UPLOAD_FOLDER = BASE_DIR / "originals"
PDFS_FOLDER = BASE_DIR / "pdfs"

# Create directories relative to project root
try:
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
    PDFS_FOLDER.mkdir(parents=True, exist_ok=True)
except OSError as e:
    logging.error(f"Failed to create directories: {e}")
    raise RuntimeError("Could not create uploads directories") from e

ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "ppt", "pptx", "doc", "docx"}

# Asegurar que los directorios existan
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
PDFS_FOLDER.mkdir(parents=True, exist_ok=True)

# Instanciar el gestor de archivos
file_manager = FileManager()


def allowed_file(filename: str) -> bool:
    """
    Verifica si el archivo tiene una extensión permitida.
    
    Args:
        filename (str): Nombre del archivo
        
    Returns:
        bool: True si la extensión está permitida, False en caso contrario
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@router.post("/")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    filename: str = Form(...),
):
    """
    Endpoint para subir un archivo.
    
    Valida la autenticación del usuario, el archivo y el nombre proporcionado.
    Guarda el archivo de forma segura, procesa el PDF mediante OCR, actualiza la base de datos 
    Milvus y actualiza la descripción del agente.
    
    Args:
        request: Objeto de solicitud de FastAPI
        file: Archivo subido
        filename: Nombre personalizado para el archivo
        redis: Conexión a Redis
        
    Returns:
        JSONResponse: Respuesta con el resultado de la operación
    """
    # Verificar autenticación del usuario
    user_email = request.session.get("user_email")
    if not user_email:
        logger.warning("Usuario no autenticado en endpoint de subida de archivos")
        raise HTTPException(status_code=401, detail="Usuario no autenticado")
    
    logger.info(f"Solicitud de subida de archivo recibida de usuario: {user_email}")
    
    # Validar el archivo
    if not file:
        logger.warning("No se proporcionó ningún archivo en la solicitud")
        raise HTTPException(status_code=400, detail="No se ha enviado ningún archivo: 'file'")
    
    if not filename:
        logger.warning("No se proporcionó un nombre de archivo en la solicitud")
        raise HTTPException(status_code=400, detail="No se proporcionó un nombre de archivo")
    
    if file.filename == "":
        logger.warning("Se recibió un nombre de archivo vacío en la subida")
        raise HTTPException(status_code=400, detail="No se seleccionó ningún archivo")
    
    if not allowed_file(file.filename):
        logger.warning(f"Formato de archivo no válido para: {file.filename}")
        raise HTTPException(status_code=400, detail="Formato de archivo no válido")
      
    # Construir el nuevo nombre de archivo de forma segura
    file_ext = file.filename.rsplit('.', 1)[1].lower()
    new_filename = file_manager.secure_filename(f"{filename}.{file_ext}")
    logger.debug(f"Nuevo nombre de archivo seguro generado: {new_filename}")
    
    # Preparar la ruta del archivo
    file_path = UPLOAD_FOLDER / new_filename
    
    try:
        # Guardar el archivo
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
        logger.info(f"Archivo guardado correctamente en {file_path}")
    except Exception as e:
        logger.error(f"Error al guardar el archivo '{new_filename}': {e}")
        raise HTTPException(status_code=500, detail="Error al guardar el archivo")
    
    # Obtener el agente asociado al usuario
    zolkin_agent = agent_manager.get_zolkin(user_email)
    if not zolkin_agent:
        logger.error(f"Agente no encontrado en caché para usuario: {user_email}")
        raise HTTPException(status_code=500, detail="Agente no encontrado en caché")
    
    # Procesar el archivo
    try:
        logger.info(f"Procesando archivo con FileManager para: {file_path}")
        pdf_file = manage_files(str(file_path), str(PDFS_FOLDER))
        if not pdf_file:
            raise ValueError("Error al convertir el archivo a PDF")
        logger.info(f"Archivo procesado correctamente, PDF generado en {pdf_file}")
    except Exception as e:
        logger.error(f"Error al procesar el archivo con FileManager: {e}")
        raise HTTPException(status_code=500, detail="Error al procesar el archivo")
    
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
            metadata={"filename": filename, "original_file": file.filename}
        )
        
        if not file_content:
            raise ValueError("Error al cargar el contenido del PDF")
            
        logger.info("OCR y carga de archivo completados correctamente")
    except Exception as e:
        logger.error(f"Error durante OCR o carga de archivo: {e}")
        raise HTTPException(status_code=500, detail="Error al procesar el archivo PDF")
    
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
        raise HTTPException(status_code=500, detail="Error al actualizar el almacenamiento")
    
    # Actualizar la descripción RAG del agente
    try:
        logger.info("Actualizando descripción RAG del agente")
        zolkin_agent.update_rag_tool_description()
        logger.info("Descripción RAG del agente actualizada correctamente")
    except Exception as e:
        logger.error(f"Error al actualizar la descripción RAG del agente: {e}")
        raise HTTPException(status_code=500, detail="Error al actualizar la descripción del agente")
    
    logger.info("Proceso de subida de archivo completado correctamente")
    return JSONResponse(
        status_code=200,
        content={
            "message": "Archivo subido correctamente",
            "filename": new_filename,
            "pdf_file": os.path.basename(pdf_file)
        }
    )
