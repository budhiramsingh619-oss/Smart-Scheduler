import os
import anthropic
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from models.db import Task, Activity, User
from services.insights import weekly_insights
from ml.model import best_time, train_model

ai_bp = Blueprint("ai", __name__)
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))


def _build_context(uid: int) -> str:
    user = User.query.get(uid)
    tasks = Task.query.filter_by(user_id=uid).order_by(Task.deadline).limit(15).all()
    activity = [a.to_dict() for a in Activity.query.filter_by(user_id=uid).order_by(Activity.created_at).all()]
    model = train_model(uid)
    bt = best_time(model)
    insights = weekly_insights(activity)

    task_list = "\n".join(
        f"- [{t.priority}] {t.name} | Due: {t.deadline} | {'Done' if t.completed else 'Pending'} | Category: {t.category}"
        for t in tasks
    )

    return f"""You are an AI productivity assistant inside Smart Scheduler.
User: {user.username if user else 'Unknown'}
Best focus hour: {bt['best_hour']}:00 ({round(bt['confidence']*100)}% confidence)
Weekly: completion {insights['completion_rate']}%, avg focus {insights['avg_focus']}/10, trend: {insights['trend']}, performance: {insights['performance']}
Suggestion: {insights['suggestion']}

Current tasks:
{task_list or 'No tasks yet.'}

Be concise, warm, and actionable. If the user wants to create a task, end with: SUGGESTED_TASK: <task name>"""


@ai_bp.post("/chat")
@jwt_required()
def chat():
    uid = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}
    question = str(data.get("question") or "").strip()[:500]

    if not question:
        return jsonify({"answer": "Ask me about your tasks, schedule, focus, or weekly progress."})

    try:
        system_prompt = _build_context(uid)
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=800,
            system=system_prompt,
            messages=[{"role": "user", "content": question}],
        )
        raw = message.content[0].text
        suggested_task = None

        if "SUGGESTED_TASK:" in raw:
            parts = raw.split("SUGGESTED_TASK:", 1)
            raw = parts[0].strip()
            suggested_task = parts[1].strip().split("\n")[0].strip()

        return jsonify({"answer": raw, "suggested_task": suggested_task})

    except Exception as e:
        return jsonify({"answer": f"AI error: {str(e)}", "suggested_task": None}), 500
