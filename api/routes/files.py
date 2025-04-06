"""
File upload and processing routes for the Zolkin application.
"""
import os
import logging
from pathlib import Path

from fastapi.responses import JSONResponse
from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form

from ..file_to_rag import upsert_file_to_rag
from services.files import secure_filename


logger = logging.getLogger(__name__)


# Crear el router
router = APIRouter(prefix="/upload_file", tags=["upload_file"])

# Configuración de rutas usando pathlib
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
    
    if not allowed_file(file.filename):
        logger.warning(f"Formato de archivo no válido para: {file.filename}")
        raise HTTPException(status_code=400, detail="Formato de archivo no válido")
      
    # Construir el nuevo nombre de archivo de forma segura
    file_ext = file.filename.rsplit('.', 1)[1].lower()
    new_filename = secure_filename(f"{filename}.{file_ext}")
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
        raise HTTPException(status_code=500, detail="Error al guardar el archivo") from e
    
    # Procesar el archivo para el RAG
    pdf_file = upsert_file_to_rag(
        user_email=user_email,
        file_path=str(file_path),
        pdfs_dir=str(PDFS_FOLDER)
    )
    logger.info("Proceso de subida de archivo completado correctamente")

    return JSONResponse(
        status_code=200,
        content={
            "message": "Archivo subido correctamente",
            "filename": new_filename,
            "pdf_file": pdf_file
        }
    )
