import os
import json
import re
import base64
from datetime import datetime, timezone, timedelta

from flask import Blueprint, request, jsonify, redirect, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

from models.db import db, User, Task

google_bp = Blueprint("google", __name__)

SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar",
]

# Keywords that suggest a task / action item inside an email
TASK_KEYWORDS = [
    "please complete", "please finish", "deadline", "due by", "due date",
    "action required", "action item", "todo", "to-do", "to do",
    "follow up", "follow-up", "reminder", "submit", "review by",
    "respond by", "please review", "kindly complete", "asap",
    "urgent", "important task", "assignment", "deliverable",
]

PRIORITY_KEYWORDS = {
    "High": ["urgent", "asap", "critical", "immediately", "high priority", "important"],
    "Low": ["whenever", "low priority", "no rush", "optional", "fyi"],
}


def _build_flow():
    return Flow.from_client_config(
        {
            "web": {
                "client_id": current_app.config["GOOGLE_CLIENT_ID"],
                "client_secret": current_app.config["GOOGLE_CLIENT_SECRET"],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=SCOPES,
        redirect_uri=current_app.config["GOOGLE_REDIRECT_URI"],
    )


def _credentials_from_user(user: User) -> Credentials:
    creds = Credentials(
        token=user.google_access_token,
        refresh_token=user.google_refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=current_app.config["GOOGLE_CLIENT_ID"],
        client_secret=current_app.config["GOOGLE_CLIENT_SECRET"],
        scopes=SCOPES,
    )
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        user.google_access_token = creds.token
        if creds.expiry:
            user.google_token_expiry = creds.expiry
        db.session.commit()
    return creds


def _detect_priority(text: str) -> str:
    lower = text.lower()
    for priority, words in PRIORITY_KEYWORDS.items():
        if any(w in lower for w in words):
            return priority
    return "Medium"


def _extract_deadline(text: str):
    """Very simple date extraction — looks for 'due DATE' patterns."""
    patterns = [
        r"due\s+(?:by\s+)?(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})",
        r"deadline[:\s]+(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})",
        r"by\s+(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            raw = match.group(1)
            for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y", "%d/%m/%y"):
                try:
                    return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
                except ValueError:
                    continue
    # Default: 7 days from today
    return (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")


def _decode_body(payload) -> str:
    """Recursively decode Gmail message body to plain text."""
    body = ""
    mime = payload.get("mimeType", "")
    if mime == "text/plain":
        data = payload.get("body", {}).get("data", "")
        if data:
            body = base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="ignore")
    elif mime.startswith("multipart"):
        for part in payload.get("parts", []):
            body += _decode_body(part)
    return body


# ── OAUTH FLOW ─────────────────────────────────────────────────────────────


@google_bp.get("/login")
@jwt_required()
def google_login():
    flow = _build_flow()
    flow.code_challenge_method = None  # Disable PKCE for server-side
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
        state=get_jwt_identity(),
    )
    return jsonify({"auth_url": auth_url})


@google_bp.get("/callback")
def google_callback():
    code = request.args.get("code")
    state = request.args.get("state")  # user_id encoded as state

    if not code or not state:
        return redirect(f"{os.environ.get('FRONTEND_URL','http://localhost:5173')}?error=oauth_failed")

    flow = _build_flow()
    flow.fetch_token(code=code)
    creds = flow.credentials

    # Fetch user info
    service = build("oauth2", "v2", credentials=creds)
    info = service.userinfo().get().execute()
    email = info.get("email")

    user = User.query.get(int(state))
    if not user:
        return redirect(f"{os.environ.get('FRONTEND_URL','http://localhost:5173')}?error=user_not_found")

    user.email = email or user.email
    user.google_access_token = creds.token
    user.google_refresh_token = creds.refresh_token
    if creds.expiry:
        user.google_token_expiry = creds.expiry
    db.session.commit()

    frontend = os.environ.get("FRONTEND_URL", "http://localhost:5173")
    return redirect(f"{frontend}?google_connected=true")


# ── GMAIL SYNC ─────────────────────────────────────────────────────────────


@google_bp.post("/sync-gmail")
@jwt_required()
def sync_gmail():
    user = User.query.get(int(get_jwt_identity()))
    if not user or not user.google_access_token:
        return jsonify({"error": "Google account not connected."}), 403

    try:
        creds = _credentials_from_user(user)
        gmail = build("gmail", "v1", credentials=creds)

        # Fetch last 50 unread emails from inbox
        results = gmail.users().messages().list(
            userId="me",
            q="is:unread in:inbox",
            maxResults=50,
        ).execute()

        messages = results.get("messages", [])
        created_tasks = []
        skipped = 0

        existing_ids = {t.gmail_message_id for t in Task.query.filter_by(user_id=user.id).all() if t.gmail_message_id}

        for msg_ref in messages:
            msg_id = msg_ref["id"]
            if msg_id in existing_ids:
                skipped += 1
                continue

            msg = gmail.users().messages().get(userId="me", id=msg_id, format="full").execute()

            headers = {h["name"]: h["value"] for h in msg["payload"].get("headers", [])}
            subject = headers.get("Subject", "(No Subject)")
            sender = headers.get("From", "")
            body = _decode_body(msg["payload"])
            full_text = f"{subject} {body}"

            # Check if this email looks like a task
            lower_text = full_text.lower()
            is_task = any(kw in lower_text for kw in TASK_KEYWORDS)
            if not is_task:
                skipped += 1
                continue

            priority = _detect_priority(full_text)
            deadline = _extract_deadline(full_text)

            # Truncate subject for task name
            task_name = subject[:160].strip() or "Email task"
            category = "Email"

            task = Task(
                user_id=user.id,
                name=task_name,
                category=category,
                deadline=deadline,
                priority=priority,
                duration=1,
                difficulty=5,
                notes=f"From: {sender}\n\n{body[:500]}",
                source="gmail",
                gmail_message_id=msg_id,
            )
            db.session.add(task)
            created_tasks.append(task_name)

        db.session.commit()

        return jsonify({
            "synced": len(created_tasks),
            "skipped": skipped,
            "tasks_created": created_tasks,
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── GOOGLE CALENDAR SYNC ───────────────────────────────────────────────────


@google_bp.post("/push-calendar")
@jwt_required()
def push_to_calendar():
    user = User.query.get(int(get_jwt_identity()))
    if not user or not user.google_access_token:
        return jsonify({"error": "Google account not connected."}), 403

    try:
        creds = _credentials_from_user(user)
        cal = build("calendar", "v3", credentials=creds)

        calendar_id = user.google_calendar_id or "primary"

        tasks = Task.query.filter_by(user_id=user.id, completed=False).all()
        pushed = 0
        updated = 0

        for task in tasks:
            if not task.deadline or not task.scheduled_start:
                continue

            start_str = f"{task.deadline}T{task.scheduled_start}:00"
            end_str = f"{task.deadline}T{task.scheduled_end or task.scheduled_start}:00"

            event_body = {
                "summary": f"[{task.priority}] {task.name}",
                "description": f"Category: {task.category}\nDifficulty: {task.difficulty}/10\nDuration: {task.duration}h\n\n{task.notes or ''}",
                "start": {"dateTime": start_str, "timeZone": user.timezone or "Asia/Kolkata"},
                "end": {"dateTime": end_str, "timeZone": user.timezone or "Asia/Kolkata"},
                "colorId": "11" if task.priority == "High" else "5" if task.priority == "Medium" else "2",
                "reminders": {
                    "useDefault": False,
                    "overrides": [
                        {"method": "email", "minutes": 60},
                        {"method": "popup", "minutes": 30},
                    ],
                },
            }

            if task.google_event_id:
                try:
                    cal.events().update(
                        calendarId=calendar_id,
                        eventId=task.google_event_id,
                        body=event_body,
                    ).execute()
                    updated += 1
                except Exception:
                    # Event may have been deleted from Calendar — re-create it
                    task.google_event_id = None

            if not task.google_event_id:
                created = cal.events().insert(
                    calendarId=calendar_id, body=event_body
                ).execute()
                task.google_event_id = created["id"]
                pushed += 1

        db.session.commit()
        return jsonify({"pushed": pushed, "updated": updated})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@google_bp.delete("/disconnect")
@jwt_required()
def disconnect_google():
    user = User.query.get(int(get_jwt_identity()))
    if not user:
        return jsonify({"error": "Not found."}), 404
    user.google_access_token = None
    user.google_refresh_token = None
    user.google_token_expiry = None
    db.session.commit()
    return jsonify({"message": "Google account disconnected."})
