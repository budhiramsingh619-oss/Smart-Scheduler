import os
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv

load_dotenv()

from models.db import db
from routes.auth import auth_bp
from routes.tasks import tasks_bp
from routes.schedule import schedule_bp
from routes.dashboard import dashboard_bp
from routes.google_oauth import google_bp
from routes.ai_assistant import ai_bp
def create_app():
    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URL"]
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = os.environ["JWT_SECRET_KEY"]
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = False  # long-lived for simplicity; tighten in prod

    app.config["GOOGLE_CLIENT_ID"] = os.environ.get("GOOGLE_CLIENT_ID", "")
    app.config["GOOGLE_CLIENT_SECRET"] = os.environ.get("GOOGLE_CLIENT_SECRET", "")
    app.config["GOOGLE_REDIRECT_URI"] = os.environ.get(
        "GOOGLE_REDIRECT_URI", "http://localhost:5000/auth/google/callback"
    )

    db.init_app(app)
    JWTManager(app)
    CORS(app, origins=["http://localhost:5173"], supports_credentials=True)

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(tasks_bp, url_prefix="/tasks")
    app.register_blueprint(schedule_bp, url_prefix="/schedule")
    app.register_blueprint(dashboard_bp, url_prefix="/dashboard")
    app.register_blueprint(google_bp, url_prefix="/auth/google")
    app.register_blueprint(ai_bp, url_prefix="/ai")

    with app.app_context():
        db.create_all()

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)
