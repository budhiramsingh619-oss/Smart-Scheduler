import os
import google.generativeai as genai
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from models.db import Task, Activity, User
from services.insights import weekly_insights
from ml.model import best_time, train_model

ai_bp = Blueprint("ai", __name__)

# Gemini Setup
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

print("GEMINI KEY:", os.environ.get("GEMINI_API_KEY"))


def _build_context(uid: int) -> str:
    user = User.query.get(uid)

    tasks = (
        Task.query
        .filter_by(user_id=uid)
        .order_by(Task.deadline)
        .limit(15)
        .all()
    )

    activity = [
        a.to_dict()
        for a in Activity.query
        .filter_by(user_id=uid)
        .order_by(Activity.created_at)
        .all()
    ]

    trained_model = train_model(uid)

    bt = best_time(trained_model)

    insights = weekly_insights(activity)

    task_list = "\n".join(
        f"- [{t.priority}] {t.name} | Due: {t.deadline} | "
        f"{'Done' if t.completed else 'Pending'} | Category: {t.category}"
        for t in tasks
    )

    return f"""
You are an AI productivity assistant inside Smart Scheduler.

User: {user.username if user else 'Unknown'}

Best focus hour:
{bt['best_hour']}:00 ({round(bt['confidence'] * 100)}% confidence)

Weekly stats:
- Completion rate: {insights['completion_rate']}%
- Avg focus: {insights['avg_focus']}/10
- Trend: {insights['trend']}
- Performance: {insights['performance']}

Suggestion:
{insights['suggestion']}

Current tasks:
{task_list or 'No tasks yet.'}

Instructions:
- Be concise
- Be warm and actionable
- Give productivity advice
- Help with planning and scheduling
- If user wants a new task, end response with:
SUGGESTED_TASK: <task name>
"""


@ai_bp.post("/chat")
@jwt_required()
def chat():
    uid = int(get_jwt_identity())

    data = request.get_json(silent=True) or {}

    question = str(data.get("question") or "").strip()[:500]

    if not question:
        return jsonify({
            "answer": "Ask me about your tasks, schedule, focus, or weekly progress.",
            "suggested_task": None
        })

    try:
        system_prompt = _build_context(uid)

        prompt = f"""
{system_prompt}

User question:
{question}
"""

        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        raw = response.text



        suggested_task = None

        if "SUGGESTED_TASK:" in raw:
            parts = raw.split("SUGGESTED_TASK:", 1)

            raw = parts[0].strip()

            suggested_task = (
                parts[1]
                .strip()
                .split("\n")[0]
                .strip()
            )

        return jsonify({
            "answer": raw,
            "suggested_task": suggested_task
        })

    except Exception as e:
        import traceback
        traceback.print_exc()

    return jsonify({
        "answer": "Gemini quota exceeded. Please try again later.",
        "suggested_task": None
    }), 429