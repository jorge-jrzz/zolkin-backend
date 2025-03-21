"""API REST for Zolkin"""
import os
import logging

from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
from authlib.integrations.flask_client import OAuth

from config import DevelopmentConfig
from blueprints import (
    auth_bp,
    files_bp,
    chat_bp,
    users_bp
)


load_dotenv()

# Inicialización de la app
app = Flask(__name__)
app.config.from_object(DevelopmentConfig())

handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)

oauth = OAuth(app)
CORS(
    app,
    resources={r"/*": {"origins": os.getenv("FRONTEND_URL")}},
    supports_credentials=True,
)


@app.route("/")
def index():
    """Check if the server is running."""
    return "Hello World"


app.register_blueprint(auth_bp, url_prefix="/google")
app.register_blueprint(files_bp, url_prefix="/upload_file")
app.register_blueprint(chat_bp, url_prefix="/chat")
app.register_blueprint(users_bp, url_prefix="/user_info")


if __name__ == "__main__":
    app.run(
        host=app.config['HOST'],
        port=app.config['PORT'],
    )
