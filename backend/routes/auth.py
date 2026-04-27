from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

from models.db import db, User

auth_bp = Blueprint("auth", __name__)


def _clean(value, limit=80):
    return str(value or "").strip()[:limit]


@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    username = _clean(data.get("username"), 40)
    password = str(data.get("password") or "")
    email = _clean(data.get("email"), 200) or None

    if len(username) < 3:
        return jsonify({"error": "Username must be at least 3 characters."}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters."}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already taken."}), 409

    if email and User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered."}), 409

    user = User(
        username=username,
        email=email,
        password_hash=generate_password_hash(password),
    )
    db.session.add(user)
    db.session.commit()

    token = create_access_token(identity=str(user.id))
    return jsonify({"token": token, "user": user.to_dict()}), 201


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    username = _clean(data.get("username"), 40)
    password = str(data.get("password") or "")

    user = User.query.filter_by(username=username).first()
    if not user or not user.password_hash or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "Invalid username or password."}), 401

    token = create_access_token(identity=str(user.id))
    return jsonify({"token": token, "user": user.to_dict()})


@auth_bp.get("/me")
@jwt_required()
def me():
    user = User.query.get(int(get_jwt_identity()))
    if not user:
        return jsonify({"error": "User not found."}), 404
    return jsonify(user.to_dict())


@auth_bp.patch("/preferences")
@jwt_required()
def update_preferences():
    user = User.query.get(int(get_jwt_identity()))
    if not user:
        return jsonify({"error": "User not found."}), 404

    data = request.get_json(silent=True) or {}
    if "timezone" in data:
        user.timezone = _clean(data["timezone"], 60)
    if "notification_email" in data:
        user.notification_email = bool(data["notification_email"])
    if "notification_deadline" in data:
        user.notification_deadline = bool(data["notification_deadline"])
    if "notification_weekly" in data:
        user.notification_weekly = bool(data["notification_weekly"])

    db.session.commit()
    return jsonify(user.to_dict())
