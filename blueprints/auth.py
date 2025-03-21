import os
from pathlib import Path

from redis import Redis
from authlib.common.security import generate_token
from flask import Blueprint, session, redirect, url_for, current_app

from core import (
    get_google_creds,
    ZolkinAgent,
    MilvusStorage,
    RedisSaver,
    set_agent,
    set_zolkin,
    set_user
)


auth_bp = Blueprint("google", __name__)

SCOPES = [
    "https://mail.google.com/",
    "https://www.googleapis.com/auth/calendar",
    "openid",
    "email",
    "profile",
]
CONF_URL = "https://accounts.google.com/.well-known/openid-configuration"

def get_redis_conn():
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    current_app.logger.debug(f"Connecting to Redis at {redis_url}")
    return Redis.from_url(redis_url, db=0)

@auth_bp.route("/")
def google():
    """Endpoint to start the Google OAuth2 flow."""
    current_app.logger.info("Starting Google OAuth2 flow")
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
    redirect_uri = url_for("google.google_auth", _external=True)
    session["nonce"] = generate_token()
    current_app.logger.debug(f"Generated nonce for session: {session['nonce']}")
    return oauth.google.authorize_redirect(redirect_uri, nonce=session["nonce"])

@auth_bp.route("/auth/")
def google_auth():
    """Endpoint to authenticate the user with Google."""
    current_app.logger.info("Google authentication callback received")
    oauth = current_app.extensions["authlib.integrations.flask_client"]
    try:
        token = oauth.google.authorize_access_token()
    except Exception as e:
        current_app.logger.error(f"Error authorizing access token: {e}")
        return "Authorization failed", 400

    try:
        user_info = token["userinfo"]
        user_mail = user_info["email"].rsplit("@", 1)[0].lower()
    except Exception as e:
        current_app.logger.error(f"Error extracting user info from token: {e}")
        return "User info extraction failed", 400

    token_file = Path(f"./secrets/{user_mail}.json")
    secrets_dir = token_file.parent
    secrets_dir.mkdir(parents=True, exist_ok=True)
    try:
        creds = get_google_creds(token_file, token, SCOPES)
        current_app.logger.debug("Google credentials obtained successfully")
    except Exception as e:
        current_app.logger.error(f"Error obtaining Google credentials: {e}")
        return "Credential error", 500

    user_info_data = {
        "name": user_info.get("name"),
        "email": user_info.get("email"),
        "picture": user_info.get("picture"),
    }

    try:
        user = oauth.google.parse_id_token(token, nonce=session.get("nonce"))
        session["user"] = user
    except Exception as e:
        current_app.logger.error(f"Error parsing ID token: {e}")
        return "ID token parsing failed", 400

    current_app.logger.info(f"User authenticated: {user_info_data.get('email')}")

    try:
        milvus_conn = MilvusStorage(collection_name="zolkin_collection")
        milvus_storage = milvus_conn.use_collection()
    except Exception as e:
        current_app.logger.error(f"Error initializing Milvus storage: {e}")
        return "Milvus initialization failed", 500

    try:
        zolkin_agent = ZolkinAgent(
            google_creds=creds,
            milvus_conn=milvus_conn,
            milvus_storage=milvus_storage,
            partition_key_field=user_info_data["email"],
        )
        zolkin_agent.init_tools()
        set_zolkin(user_info_data["email"], zolkin_agent)
    except Exception as e:
        current_app.logger.error(f"Error initializing Zolkin agent: {e}")
        return "Agent initialization failed", 500

    try:
        redis_conn = get_redis_conn()
        memory = RedisSaver(redis_conn)
        agent = zolkin_agent.create_agent(memory)
        set_agent(user_info_data["email"], agent)
        set_user(user_info_data["email"], user_info_data)
        current_app.logger.info(f"Agent and user data set for: {user_info_data['email']}")
    except Exception as e:
        current_app.logger.error(f"Error setting agent and user: {e}")
        return "Agent/user setup failed", 500

    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    current_app.logger.info(f"Redirecting user to frontend at {frontend_url}/chat")
    return redirect(f"{frontend_url}/chat")
