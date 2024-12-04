import os
from typing import List

from dotenv import load_dotenv
from flask import Flask, url_for, redirect, session, jsonify, request
from authlib.integrations.flask_client import OAuth
from authlib.common.security import generate_token
from werkzeug.utils import secure_filename
from flask_cors import CORS
from langchain_core.messages import HumanMessage

from core import get_google_creds, manage_files, LoadFile, ZolkinAgent, MilvusStorage, RedisSaver

from redis import Redis


load_dotenv()
SCOPES = ["https://mail.google.com/", "https://www.googleapis.com/auth/calendar", "openid", "email", "profile"]
CONF_URL = 'https://accounts.google.com/.well-known/openid-configuration'

app = Flask(__name__)
app.secret_key = os.urandom(12)
oauth = OAuth(app)
CORS(app)

UPLOAD_FOLDER = './uploads'
ALLOWED_EXTENSIONS = ['txt', 'html', 'md', 'java', 'py', 'c', 'cpp', 'js', 'pdf', 
                      'png', 'jpg', 'jpeg', 'ppt', 'pptx', 'doc', 'docx']
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

milvus_conn = MilvusStorage(collection_name="zolkin_collection")
milvus_storage = None
redis_conn = Redis(host="localhost", port=6379, db=0)
memory = RedisSaver(redis_conn)
agent: ZolkinAgent = None
zolkin_agent = None
user_info_data = None
creds = None


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
    return "Hello World"


@app.post('/upload_file/')
def upload_file():
    global user_info_data, milvus_conn, milvus_storage, agent
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
        path_file = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(path_file)
        # Empieza RAG
        manage_files(path_file, dst_path=f"./pdfs/{filename}")
        LoadFile.ocr_pdf(f"./pdfs/{filename}")
        file_content = LoadFile.load_file(
            file_path = f"./pdfs/{filename}", 
            namespace = user_info_data["email"]
        )
        milvus_conn.upsert_files(milvus_storage, file_content)
        agent.update_rag_description("zolkin_collection")
        return jsonify({"message": "File uploaded successfully"}), 200
    else:
        return jsonify({"error": "Invalid file format: 'file'"}), 400


@app.route('/google/')
def google():
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
    print(redirect_uri)
    session['nonce'] = generate_token()
    return oauth.google.authorize_redirect(redirect_uri, nonce=session['nonce'])


@app.route('/google/auth/')
def google_auth():
    global creds, user_info_data, milvus_storage, milvus_conn, agent, zolkin_agent, memory
    token = oauth.google.authorize_access_token()
    creds = get_google_creds("./secrets/token.json", token, SCOPES)
    user_info_data = {
        "name": token["userinfo"]["name"], 
        "email": token["userinfo"]["email"], 
        "picture": token["userinfo"]["picture"]
    }
    user = oauth.google.parse_id_token(token, nonce=session['nonce'])
    session['user'] = user
    # Empieza Agente
    milvus_storage = milvus_conn.use_collection()
    agent = ZolkinAgent(
        google_creds=creds,
        milvus_conn=milvus_conn,
        milvus_storage=milvus_storage, 
        partition_key_field=user_info_data["email"]
    ).init_tools()
    zolkin_agent = agent.create_agent(memory)
    return redirect('http://localhost:5173/chat')


@app.route('/user_info/')
def user_info():
    return jsonify(user_info_data), 200


@app.route('/chat/')
def chat():
    global zolkin_agent
    if zolkin_agent is None:
        return jsonify({"error": "Agent not initialized"}), 400
    elif request.args.get("prompt") is None or request.args.get("thread_id") is None:
        return jsonify({"error": "No prompt has been sent"}), 401
    config = {"configurable": {"thread_id": request.args.get("thread_id")}}
    response = zolkin_agent.invoke(
        {
            "messages": [HumanMessage(content=request.args.get("prompt"))]
        }, 
        config
    )
    return jsonify({"response": response["messages"][-1].content}), 200


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5002)
