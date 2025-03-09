"""Blueprint for user info."""
from flask import Blueprint, jsonify, session, current_app

from core import get_user


users_bp = Blueprint("user_info", __name__)

@users_bp.route("/", methods=["GET"])
def user_info():
    """Endpoint to get the user info."""
    if "user" not in session or "email" not in session["user"]:
        current_app.logger.warning("User not authenticated when accessing user_info endpoint.")
        return jsonify({"error": "User not authenticated"}), 401

    user_email = session["user"]["email"]
    current_app.logger.info(f"Fetching user info for user: {user_email}")

    user = get_user(user_email)
    if user is None:
        current_app.logger.error(f"User not found for email: {user_email}")
        return jsonify({"error": "User not found"}), 404

    current_app.logger.info(f"User info retrieved successfully for {user_email}")
    return jsonify(user), 200
