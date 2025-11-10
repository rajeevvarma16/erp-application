from flask import Blueprint, request, jsonify
from app import limiter
import os
from openai import OpenAI

chatbot_bp = Blueprint('chatbot', __name__)

@chatbot_bp.route("/api/chatbot", methods=["POST"])
@limiter.limit("10 per minute")
def chatbot():
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    data = request.get_json()
    user_query = data.get("query", "")

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "You are an ERP assistant."},
            {"role": "user", "content": user_query}
        ]
    )

    reply = response.choices[0].message.content
    return jsonify({"reply": reply})
