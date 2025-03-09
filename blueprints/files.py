""""Blueprint for files route."""
import os
from pathlib import Path

from flask import Blueprint, request, jsonify, session, current_app
from werkzeug.utils import secure_filename

from core import manage_files, LoadFile, MilvusStorage, get_zolkin


files_bp = Blueprint("upload_file", __name__)

# Configuración de rutas usando pathlib
BASE_DIR = Path(os.environ.get("BASE_DIR", "./"))
UPLOAD_FOLDER = BASE_DIR / "files" / "uploads"
PDFS_FOLDER = BASE_DIR / "files" / "pdfs"
ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "ppt", "pptx", "doc", "docx"}


def allowed_file(filename: str) -> bool:
    """Verifica si el archivo tiene una extensión permitida."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_milvus_conn() -> MilvusStorage:
    """Crea una conexión a la colección de almacenamiento Milvus."""
    current_app.logger.debug("Initializing MilvusStorage connection.")
    return MilvusStorage(collection_name="zolkin_collection")


@files_bp.route("/", methods=["POST"])
def upload_file():
    """
    Endpoint para subir un archivo.
    
    Valida la autenticación del usuario, el archivo y el nombre proporcionado.
    Guarda el archivo de forma segura, procesa el PDF mediante OCR, actualiza la base de datos 
    Milvus y actualiza la descripción del agente.
    """
    # Verificar autenticación del usuario
    if "user" not in session or "email" not in session["user"]:
        current_app.logger.warning("User not authenticated in file upload endpoint.")
        return jsonify({"error": "User not authenticated"}), 401

    user_email = session["user"]["email"]
    current_app.logger.info(f"File upload request received from user: {user_email}")

    # Validar que se haya enviado un archivo y un nombre
    if "file" not in request.files:
        current_app.logger.warning("No file provided in the request.")
        return jsonify({"error": "No file has been sent: 'file'"}), 400

    custom_filename = request.form.get("filename")
    if not custom_filename:
        current_app.logger.warning("No filename provided in the request.")
        return jsonify({"error": "No filename provided"}), 400

    uploaded_file = request.files["file"]
    if uploaded_file.filename == "":
        current_app.logger.warning("Empty filename received in the file upload.")
        return jsonify({"error": "No file selected"}), 400

    if not allowed_file(uploaded_file.filename):
        current_app.logger.warning(f"Invalid file format for file: {uploaded_file.filename}")
        return jsonify({"error": "Invalid file format"}), 400

    # Construir el nuevo nombre de archivo de forma segura
    file_ext = uploaded_file.filename.rsplit('.', 1)[1].lower()
    new_filename = secure_filename(f"{custom_filename}.{file_ext}")
    current_app.logger.debug(f"New secure filename generated: {new_filename}")

    # Asegurarse de que el directorio de subida existe
    UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
    file_path = UPLOAD_FOLDER / new_filename

    try:
        uploaded_file.save(str(file_path))
        current_app.logger.info(f"File saved successfully at {file_path}")
    except Exception as e:
        current_app.logger.error(f"Error saving file '{new_filename}': {e}")
        return jsonify({"error": "Error saving file"}), 500

    # Obtener el agente asociado al usuario
    agent = get_zolkin(user_email)
    if not agent:
        current_app.logger.error(f"Agent not found in cache for user: {user_email}")
        return jsonify({"error": "Agent not found in cache"}), 500

    # Asegurarse de que el directorio de PDFs existe y procesar el archivo
    PDFS_FOLDER.mkdir(parents=True, exist_ok=True)
    try:
        current_app.logger.info(f"Processing file with manage_files for: {file_path}")
        pdf_file = manage_files(str(file_path), outdir=str(PDFS_FOLDER))
        current_app.logger.info(f"File processed successfully, PDF generated at {pdf_file}")
    except Exception as e:
        current_app.logger.error(f"Error processing file with manage_files: {e}")
        return jsonify({"error": "Error processing file"}), 500

    try:
        current_app.logger.info("Starting OCR process on PDF file.")
        LoadFile.ocr_pdf(pdf_file, language="eng")
        file_content = LoadFile.load_file(file_path=pdf_file, namespace=user_email)
        current_app.logger.info("OCR and file loading completed successfully.")
    except Exception as e:
        current_app.logger.error(f"Error during OCR or loading file: {e}")
        return jsonify({"error": "Error processing PDF file"}), 500

    try:
        milvus_conn = get_milvus_conn()
        milvus_storage = milvus_conn.use_collection()
        current_app.logger.info("Updating Milvus storage with file content.")
        milvus_conn.upsert_files(milvus_storage, file_content)
        current_app.logger.info("Milvus storage updated successfully.")
    except Exception as e:
        current_app.logger.error(f"Error updating Milvus storage: {e}")
        return jsonify({"error": "Error updating storage"}), 500

    try:
        current_app.logger.info("Updating agent RAG description.")
        agent.update_rag_description("zolkin_collection")
        current_app.logger.info("Agent RAG description updated successfully.")
    except Exception as e:
        current_app.logger.error(f"Error updating agent RAG description: {e}")
        return jsonify({"error": "Error updating agent description"}), 500

    current_app.logger.info("File upload process completed successfully.")
    return jsonify({"message": "File uploaded successfully"}), 200
