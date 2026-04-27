from flask import jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask import Blueprint

from models.db import Activity, Task
from services.scheduler import refresh_schedule
from ml.model import best_time, train_model

schedule_bp = Blueprint("schedule", __name__)


@schedule_bp.get("/")
@jwt_required()
def get_schedule():
    uid = int(get_jwt_identity())
    activity = [a.to_dict() for a in Activity.query.filter_by(user_id=uid).all()]
    model = train_model(uid)
    bt = best_time(model)
    schedule = refresh_schedule(uid, start_hour=bt["best_hour"])
    return jsonify({"schedule": schedule, "best_hour": bt["best_hour"], "confidence": bt["confidence"]})


@schedule_bp.post("/regenerate")
@jwt_required()
def regenerate():
    uid = int(get_jwt_identity())
    model = train_model(uid)
    bt = best_time(model)
    schedule = refresh_schedule(uid, start_hour=bt["best_hour"])
    return jsonify({"schedule": schedule, "best_hour": bt["best_hour"]})
