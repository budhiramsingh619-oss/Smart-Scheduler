from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from models.db import db, Task, Activity
from services.scheduler import refresh_schedule

tasks_bp = Blueprint("tasks", __name__)

VALID_PRIORITIES = {"High", "Medium", "Low"}


def _clean_text(v, limit=200):
    return str(v or "").strip()[:limit]


def _clean_int(v, default, lo, hi):
    try:
        return max(lo, min(hi, int(v)))
    except (TypeError, ValueError):
        return default


def _valid_date(v):
    if not v:
        return None
    try:
        return datetime.strptime(str(v), "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
        return None


@tasks_bp.get("/")
@jwt_required()
def get_tasks():
    uid = int(get_jwt_identity())
    tasks = Task.query.filter_by(user_id=uid).order_by(
        Task.completed.asc(), Task.deadline.asc().nullslast(), Task.created_at.desc()
    ).all()
    return jsonify([t.to_dict() for t in tasks])


@tasks_bp.post("/")
@jwt_required()
def add_task():
    uid = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}

    name = _clean_text(data.get("name"), 160)
    category = _clean_text(data.get("category") or "General", 60) or "General"
    deadline = _valid_date(data.get("deadline"))
    priority = data.get("priority") if data.get("priority") in VALID_PRIORITIES else "Medium"
    duration = _clean_int(data.get("duration"), 1, 1, 8)
    difficulty = _clean_int(data.get("difficulty"), 5, 1, 10)
    notes = _clean_text(data.get("notes"), 1000)

    if not name:
        return jsonify({"error": "Task name is required."}), 400
    if not deadline:
        return jsonify({"error": "A valid deadline (YYYY-MM-DD) is required."}), 400

    task = Task(
        user_id=uid, name=name, category=category, deadline=deadline,
        priority=priority, duration=duration, difficulty=difficulty, notes=notes,
    )
    db.session.add(task)
    db.session.commit()

    refresh_schedule(uid)

    return jsonify(task.to_dict()), 201


@tasks_bp.patch("/<int:task_id>")
@jwt_required()
def update_task(task_id):
    uid = int(get_jwt_identity())
    task = Task.query.filter_by(id=task_id, user_id=uid).first_or_404()
    data = request.get_json(silent=True) or {}

    if "name" in data:
        task.name = _clean_text(data["name"], 160)
    if "category" in data:
        task.category = _clean_text(data["category"], 60) or "General"
    if "deadline" in data:
        task.deadline = _valid_date(data["deadline"])
    if "priority" in data and data["priority"] in VALID_PRIORITIES:
        task.priority = data["priority"]
    if "duration" in data:
        task.duration = _clean_int(data["duration"], 1, 1, 8)
    if "difficulty" in data:
        task.difficulty = _clean_int(data["difficulty"], 5, 1, 10)
    if "notes" in data:
        task.notes = _clean_text(data["notes"], 1000)

    db.session.commit()
    refresh_schedule(uid)
    return jsonify(task.to_dict())


@tasks_bp.post("/<int:task_id>/complete")
@jwt_required()
def complete_task(task_id):
    uid = int(get_jwt_identity())
    task = Task.query.filter_by(id=task_id, user_id=uid).first_or_404()
    data = request.get_json(silent=True) or {}

    focus = _clean_int(data.get("focus"), 7, 1, 10)
    new_state = not task.completed

    task.completed = new_state
    task.completed_at = datetime.now(timezone.utc) if new_state else None

    activity = Activity(
        user_id=uid,
        task_id=task.id,
        hour=datetime.now().hour,
        focus=focus,
        completed=new_state,
    )
    db.session.add(activity)
    db.session.commit()

    refresh_schedule(uid)
    return jsonify({"completed": new_state, "task": task.to_dict()})


@tasks_bp.delete("/<int:task_id>")
@jwt_required()
def delete_task(task_id):
    uid = int(get_jwt_identity())
    task = Task.query.filter_by(id=task_id, user_id=uid).first_or_404()
    db.session.delete(task)
    db.session.commit()
    refresh_schedule(uid)
    return jsonify({"deleted": task_id})
