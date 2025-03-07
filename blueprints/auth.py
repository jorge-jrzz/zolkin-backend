import os

from redis import Redis
from flask import current_app
from authlib.common.security import generate_token
from flask import Blueprint, session, redirect, url_for

from core import get_google_creds, ZolkinAgent, MilvusStorage, RedisSaver, set_agent


auth_bp = Blueprint("auth", __name__)

SCOPES = [
    "https://mail.google.com/",
    "https://www.googleapis.com/auth/calendar",
    "openid",
    "email",
    "profile",
]
CONF_URL = "https://accounts.google.com/.well-known/openid-configuration"


def get_redis_conn():
    return Redis().from_url(os.getenv("REDIS_URL"), db=0)


@auth_bp.route("/google/")
def google():
    """Endpoint to start the Google OAuth2 flow."""
    oauth = current_app.extensions["authlib.integrations.flask_client"]
    oauth.register(
        name="google",
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
        server_metadata_url=CONF_URL,
        access_type="offline",
        prompt="consent",
        client_kwargs={"scope": " ".join(SCOPES)},
    )
    redirect_uri = url_for("auth.google_auth", _external=True)
    session["nonce"] = generate_token()
    return oauth.google.authorize_redirect(redirect_uri, nonce=session["nonce"])


@auth_bp.route("/google/auth/")
def google_auth():
    """Endpoint to authenticate the user with Google."""
    oauth = current_app.extensions["authlib.integrations.flask_client"]
    token = oauth.google.authorize_access_token()
    user_mail = token["userinfo"]["email"].rsplit("@", 1)[0].lower()
    token_file = f"./secrets/{user_mail}.json"
    os.makedirs(os.path.dirname("secrets/"), exist_ok=True)
    creds = get_google_creds(token_file, token, SCOPES)
    print(creds)
    print("=" * 10)
    user_info_data = {
        "name": token["userinfo"]["name"],
        "email": token["userinfo"]["email"],
        "picture": token["userinfo"]["picture"],
    }
    user = oauth.google.parse_id_token(token, nonce=session["nonce"])
    session["user"] = user

    # Inicializar agente y almacenamiento
    milvus_conn = MilvusStorage(collection_name="zolkin_collection")
    milvus_storage = milvus_conn.use_collection()

    zolkin_agent = ZolkinAgent(
        google_creds=creds,
        milvus_conn=milvus_conn,
        milvus_storage=milvus_storage,
        partition_key_field=user_info_data["email"],
    )
    zolkin_agent.init_tools()

    redis_conn = get_redis_conn()
    memory = RedisSaver(redis_conn)
    zolkin_agent = zolkin_agent.create_agent(memory)
    set_agent(user_info_data["email"], zolkin_agent)

    return redirect(f"{os.getenv('FRONTEND_URL')}/chat")
