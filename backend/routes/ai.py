from flask import Blueprint, request, jsonify
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

ai_bp = Blueprint("ai", __name__)

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-1.5-flash")


@ai_bp.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()

        message = data.get("message")

        response = model.generate_content(message)

        return jsonify({
            "reply": response.text
        })

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500