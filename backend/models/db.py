from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(200), unique=True, nullable=True)
    password_hash = db.Column(db.Text, nullable=True)  # null for OAuth-only users

    # Google OAuth tokens
    google_access_token = db.Column(db.Text, nullable=True)
    google_refresh_token = db.Column(db.Text, nullable=True)
    google_token_expiry = db.Column(db.DateTime, nullable=True)
    google_calendar_id = db.Column(db.String(200), nullable=True)

    # Preferences
    timezone = db.Column(db.String(60), default="Asia/Kolkata")
    notification_email = db.Column(db.Boolean, default=True)
    notification_deadline = db.Column(db.Boolean, default=True)
    notification_weekly = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    tasks = db.relationship("Task", backref="user", lazy=True, cascade="all, delete-orphan")
    activities = db.relationship("Activity", backref="user", lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "timezone": self.timezone,
            "google_connected": bool(self.google_access_token),
            "created_at": self.created_at.isoformat(),
        }


class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(80), default="General")
    deadline = db.Column(db.String(10), nullable=True)   # ISO date YYYY-MM-DD
    priority = db.Column(db.String(10), default="Medium")
    duration = db.Column(db.Integer, default=1)
    difficulty = db.Column(db.Integer, default=5)
    notes = db.Column(db.Text, nullable=True)

    completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime, nullable=True)

    # Scheduling
    scheduled_start = db.Column(db.String(10), nullable=True)
    scheduled_end = db.Column(db.String(10), nullable=True)

    # Google Calendar
    google_event_id = db.Column(db.String(200), nullable=True)

    # Source tracking
    source = db.Column(db.String(20), default="manual")  # manual | gmail
    gmail_message_id = db.Column(db.String(200), nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    activities = db.relationship("Activity", backref="task", lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "deadline": self.deadline,
            "priority": self.priority,
            "duration": self.duration,
            "difficulty": self.difficulty,
            "notes": self.notes,
            "completed": self.completed,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "scheduled_start": self.scheduled_start,
            "scheduled_end": self.scheduled_end,
            "source": self.source,
            "google_event_id": self.google_event_id,
            "created_at": self.created_at.isoformat(),
        }


class Activity(db.Model):
    __tablename__ = "activity"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True)

    hour = db.Column(db.Integer, nullable=False)
    focus = db.Column(db.Integer, default=7)
    completed = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "task_id": self.task_id,
            "hour": self.hour,
            "focus": self.focus,
            "completed": self.completed,
            "created_at": self.created_at.isoformat(),
        }
