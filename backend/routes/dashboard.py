from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from models.db import Task, Activity
from services.insights import weekly_insights
from ml.model import best_time, train_model

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.get("/")
@jwt_required()
def dashboard():
    uid = int(get_jwt_identity())

    tasks = Task.query.filter_by(user_id=uid).all()
    total = len(tasks)
    completed = sum(1 for t in tasks if t.completed)

    activity = [a.to_dict() for a in Activity.query.filter_by(user_id=uid).order_by(Activity.created_at).all()]
    model = train_model(uid)
    bt = best_time(model)
    insights = weekly_insights(activity)

    # Focus by hour for chart
    from collections import defaultdict
    hour_map = defaultdict(lambda: {"sum": 0, "count": 0})
    for a in activity:
        hour_map[a["hour"]]["sum"] += a["focus"]
        hour_map[a["hour"]]["count"] += 1

    chart_data = [
        {"hour": h, "avg_focus": round(v["sum"] / v["count"], 2), "entries": v["count"]}
        for h, v in sorted(hour_map.items())
    ]

    if not chart_data:
        chart_data = [
            {"hour": 7, "avg_focus": 8.0, "entries": 0},
            {"hour": 9, "avg_focus": 8.5, "entries": 0},
            {"hour": 11, "avg_focus": 7.5, "entries": 0},
            {"hour": 15, "avg_focus": 6.0, "entries": 0},
            {"hour": 20, "avg_focus": 4.0, "entries": 0},
        ]

    return jsonify({
        "total_tasks": total,
        "completed_tasks": completed,
        "pending_tasks": total - completed,
        "completion_rate": round((completed / total) * 100, 2) if total else 0,
        "best_hour": bt["best_hour"],
        "best_hour_confidence": bt["confidence"],
        "insights": insights,
        "chart_data": chart_data,
    })
