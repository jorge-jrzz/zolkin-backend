"""Blueprint for chat route."""
from langchain_core.messages import HumanMessage
from flask import Blueprint, request, jsonify, session, current_app

from core import get_agent


chat_bp = Blueprint("chat", __name__)

@chat_bp.route("/", methods=["GET"])
def chat():
    if "user" not in session or "email" not in session["user"]:
        current_app.logger.warning("User not authenticated in chat endpoint")
        return jsonify({"error": "User not authenticated"}), 401
    user_email = session["user"]["email"]
    current_app.logger.info(f"Chat request received for user: {user_email}")

    # Obtener el agente desde agent_manager
    zolkin_agent = get_agent(user_email)
    if not zolkin_agent:
        current_app.logger.error(f"Agent not found in cache for user: {user_email}")
        return jsonify({"error": "Agent not found in cache"}), 500

    prompt = request.args.get("prompt")
    thread_id = request.args.get("thread_id")
    if not prompt or not thread_id:
        current_app.logger.warning("Missing prompt or thread_id in request")
        return jsonify({"error": "Missing prompt or thread_id"}), 400

    current_app.logger.debug(f"Received prompt: {prompt}, Thread ID: {thread_id}")
    config = {"configurable": {"thread_id": thread_id}}

    try:
        response = zolkin_agent.invoke({"messages": [HumanMessage(content=prompt)]}, config)
    except Exception as e:
        current_app.logger.error(f"Error invoking agent for user {user_email}: {e}")
        return jsonify({"error": "Error processing request"}), 500

    if "messages" not in response or not response["messages"]:
        current_app.logger.error("No messages found in agent response")
        return jsonify({"error": "Agent response invalid"}), 500

    final_response = response["messages"][-1].content
    current_app.logger.info("Chat request processed successfully")
    return jsonify({"response": final_response}), 200
