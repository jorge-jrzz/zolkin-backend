from flask import Blueprint, jsonify, session


users_bp = Blueprint("users", __name__)

@users_bp.route("/user_info/", methods=["GET"])
def user_info():
    """Endpoint to get the user info."""
    if "user" not in session or "email" not in session["user"]:
        return jsonify({"error": "User not authenticated"}), 401
    user_email = session["user"]["email"]
    return jsonify({"email": user_email}), 200
