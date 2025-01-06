"""Zolkin API."""

import os
from typing import List

from redis import Redis
from flask_cors import CORS
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from langchain_core.messages import HumanMessage
from authlib.common.security import generate_token
from authlib.integrations.flask_client import OAuth
from flask import Flask, url_for, redirect, session, jsonify, request

from core import get_google_creds, manage_files, LoadFile, ZolkinAgent, MilvusStorage, RedisSaver


load_dotenv()
BASE_DIR = "/app/"
UPLOAD_FOLDER = BASE_DIR+'files/uploads/'
PDFS_FOLDER = BASE_DIR+'files/pdfs/'
SCOPES = [
    "https://mail.google.com/", 
    "https://www.googleapis.com/auth/calendar", 
    "openid", 
    "email", 
    "profile"
]
CONF_URL = 'https://accounts.google.com/.well-known/openid-configuration'
ALLOWED_EXTENSIONS = [
    'pdf', 'png', 'jpg', 'jpeg', 'ppt', 'pptx', 'doc', 'docx'
]

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default_secret_key')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
oauth = OAuth(app)
CORS(app, resources={r"/*": {"origins": os.getenv('FRONTEND_URL')}}, supports_credentials=True)

# Diccionarios globales para almacenar agentes por usuario (clave: email)
active_agents = {}   # almacenará el agente ZolkinAgent por email
active_zolkin_agents = {}  # almacenará la instancia creada con memory y demás
active_user_data = {} # almacenar datos de usuario por email
active_milvus_storage = {} # milvus storage por email

redis_conn = Redis(host="redis", port=6379, db=0)
# Instancia global de MilvusStorage (colección base)
milvus_conn = MilvusStorage(collection_name="zolkin_collection")
memory = RedisSaver(redis_conn)


def allowed_file(filename: str, extensions: List[str]) -> bool:
    """
    Function to check if the file format is allowed.

    Args:
        extensions (List[str]): The list of allowed extensions.
        filename (str): The name of the file.

    Returns:
        bool: True if the file format is allowed, False otherwise.
    """
    # Primero crea una lista con el nombre del archivo y la extensión
    # Selecciona el segundo elemento de la lista, que es la extensión y la convierte a minúsculas
    # Comprueba si la extensión está en la lista de extensiones permitidas
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in extensions


@app.route('/')
def index():
    """Check if the server is running."""
    return "Hello World"


@app.post('/upload_file/')
def upload_file():
    """Endpoint to upload a file to the server."""
    # Obtenemos el email del usuario actual
    if 'user' not in session or 'email' not in session['user']:
        return jsonify({"error": "User not authenticated"}), 401
    user_email = session['user']['email']
    # Verificamos si existe un agente asociado a este usuario
    if user_email not in active_agents:
        return jsonify({"error": "Agent not initialized for this user"}), 400
    agent = active_agents[user_email]
    milvus_storage = active_milvus_storage[user_email]
    user_info_data = active_user_data[user_email]
    if 'file' not in request.files:
        return jsonify({"error": "No file has been sent: 'file'"}), 400
    elif request.form.get("filename") is None:
        return jsonify({"error": "No filename of file has been sent"}), 401
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file has been sent: 'file'"}), 401
    if file and allowed_file(file.filename, ALLOWED_EXTENSIONS):
        new_filename = f"{request.form.get('filename')}.{file.filename.rsplit('.', 1)[1].lower()}"
        filename = secure_filename(new_filename)
        os.makedirs(os.path.dirname(UPLOAD_FOLDER), exist_ok=True)
        path_file = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(path_file)
        # Empieza RAG
        os.makedirs(os.path.dirname(PDFS_FOLDER), exist_ok=True)
        pdf_file = manage_files(path_file, outdir=PDFS_FOLDER)
        LoadFile.ocr_pdf(pdf_file)
        file_content = LoadFile.load_file(
            file_path=pdf_file,
            namespace=user_info_data["email"]
        )
        milvus_conn.upsert_files(milvus_storage, file_content)
        agent.update_rag_description("zolkin_collection")
        return jsonify({"message": "File uploaded successfully"}), 200
    else:
        return jsonify({"error": "Invalid file format: 'file'"}), 400


@app.route('/google/')
def google():
    """Endpoint to start the Google OAuth2 flow."""
    oauth.register(
        name='google',
        client_id=os.getenv('GOOGLE_CLIENT_ID'),
        client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
        server_metadata_url=CONF_URL,
        access_type="offline",
        prompt="consent",
        client_kwargs={
            'scope': " ".join(SCOPES),
        }
    )
    redirect_uri = url_for('google_auth', _external=True)
    session['nonce'] = generate_token()
    return oauth.google.authorize_redirect(redirect_uri, nonce=session['nonce'])


@app.route('/google/auth/')
def google_auth():
    """Endpoint to authenticate the user with Google."""
    token = oauth.google.authorize_access_token()
    user_mail = token["userinfo"]["email"].rsplit('@', 1)[0].lower()
    token_file= f"./secrets/{user_mail}.json"
    os.makedirs(os.path.dirname("secrets/"), exist_ok=True)
    creds = get_google_creds(token_file, token, SCOPES)
    user_info_data = {
        "name": token["userinfo"]["name"], 
        "email": token["userinfo"]["email"], 
        "picture": token["userinfo"]["picture"]
    }
    user = oauth.google.parse_id_token(token, nonce=session['nonce'])
    session['user'] = user
    # Guardamos la info del usuario en el diccionario global
    active_user_data[user_info_data["email"]] = user_info_data
    # Empieza agente para este usuario
    milvus_storage = milvus_conn.use_collection()
    active_milvus_storage[user_info_data["email"]] = milvus_storage
    agent = ZolkinAgent(
        google_creds=creds,
        milvus_conn=milvus_conn,
        milvus_storage=milvus_storage, 
        partition_key_field=user_info_data["email"]
    ).init_tools()
    zolkin_agent = agent.create_agent(memory)
    # Guardamos el agente en el diccionario global
    active_agents[user_info_data["email"]] = agent
    active_zolkin_agents[user_info_data["email"]] = zolkin_agent
    return redirect(f"{os.getenv('FRONTEND_URL')}/chat")


@app.route('/user_info/')
def user_info():
    """Endpoint to get the user info."""
    if 'user' not in session or 'email' not in session['user']:
        return jsonify({"error": "User not authenticated"}), 401
    user_email = session['user']['email']
    if user_email in active_user_data:
        return jsonify(active_user_data[user_email]), 200
    else:
        return jsonify({"error": "No user data found"}), 404


@app.route('/chat/')
def chat():
    """Endpoint to interact with the Zolkin Agent."""
    # Obtenemos el email del usuario actual
    if 'user' not in session or 'email' not in session['user']:
        return jsonify({"error": "User not authenticated"}), 401
    user_email = session['user']['email']
    if user_email not in active_zolkin_agents:
        return jsonify({"error": "Agent not initialized"}), 400
    zolkin_agent = active_zolkin_agents[user_email]
    if request.args.get("prompt") is None or request.args.get("thread_id") is None:
        return jsonify({"error": "No prompt or thread_id has been sent"}), 401
    config = {"configurable": {"thread_id": request.args.get("thread_id")}}
    response = zolkin_agent.invoke({
            "messages": [HumanMessage(content=request.args.get("prompt"))]
        },
        config
    )
    return jsonify({"response": response["messages"][-1].content}), 200


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5002)
