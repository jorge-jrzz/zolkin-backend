from langchain_core.messages import HumanMessage
from flask import Blueprint, request, jsonify, session

from core import get_agent


chat_bp = Blueprint("chat", __name__)

@chat_bp.route("/", methods=["GET"])
def chat():
    if "user" not in session or "email" not in session["user"]:
        return jsonify({"error": "User not authenticated"}), 401
    user_email = session["user"]["email"]

    # Obtener el agente desde agent_manager
    zolkin_agent = get_agent(user_email)
    if not zolkin_agent:
        return jsonify({"error": "Agent not found in cache"}), 500

    prompt = request.args.get("prompt")
    thread_id = request.args.get("thread_id")
    if not prompt or not thread_id:
        return jsonify({"error": "Missing prompt or thread_id"}), 400

    config = {"configurable": {"thread_id": thread_id}}
    response = zolkin_agent.invoke({"messages": [HumanMessage(content=prompt)]}, config)

    return jsonify({"response": response["messages"][-1].content}), 200
