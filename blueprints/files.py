import os

from werkzeug.utils import secure_filename
from flask import Blueprint, request, jsonify, session

from core import get_agent
from core import manage_files, LoadFile, MilvusStorage


files_bp = Blueprint("files", __name__)

BASE_DIR = "/app/"
UPLOAD_FOLDER = BASE_DIR + "files/uploads/"
PDFS_FOLDER = BASE_DIR + "files/pdfs/"
ALLOWED_EXTENSIONS = ["pdf", "png", "jpg", "jpeg", "ppt", "pptx", "doc", "docx"]


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_milvus_conn():
    return MilvusStorage(collection_name="zolkin_collection")


@files_bp.route("/upload_file/", methods=["POST"])
def upload_file():
    if "user" not in session or "email" not in session["user"]:
        return jsonify({"error": "User not authenticated"}), 401
    user_email = session["user"]["email"]

    if "file" not in request.files:
        return jsonify({"error": "No file has been sent: 'file'"}), 400
    if not request.form.get("filename"):
        return jsonify({"error": "No filename provided"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400
    if not allowed_file(file.filename):
        return jsonify({"error": "Invalid file format"}), 400

    new_filename = (
        f"{request.form.get('filename')}.{file.filename.rsplit('.', 1)[1].lower()}"
    )
    filename = secure_filename(new_filename)
    os.makedirs(os.path.dirname(UPLOAD_FOLDER), exist_ok=True)
    path_file = os.path.join(UPLOAD_FOLDER, filename)
    file.save(path_file)

    # Obtener el agente desde agent_manager
    agent = get_agent(user_email)
    if not agent:
        return jsonify({"error": "Agent not found in cache"}), 500

    # RAG
    os.makedirs(os.path.dirname(PDFS_FOLDER), exist_ok=True)
    pdf_file = manage_files(path_file, outdir=PDFS_FOLDER)
    LoadFile.ocr_pdf(pdf_file)
    file_content = LoadFile.load_file(file_path=pdf_file, namespace=user_email)

    milvus_conn = get_milvus_conn()
    milvus_storage = milvus_conn.use_collection()
    milvus_conn.upsert_files(milvus_storage, file_content)
    agent.update_rag_description("zolkin_collection")

    return jsonify({"message": "File uploaded successfully"}), 200
