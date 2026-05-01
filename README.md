<<<<<<< HEAD
# Smart Scheduler AI

A full-stack AI productivity system built with **React + Vite** (frontend) and **Flask + PostgreSQL** (backend).

## Features

- **Multi-user authentication** with JWT
- **AI-powered scheduling** using your historical focus and activity data
- **Gmail sync** — automatically create tasks from emails with action keywords
- **Google Calendar sync** — push your entire schedule as colour-coded events
- **AI Assistant** — right-side panel with text and voice input/output (Claude API)
- **Productivity analytics** — weekly insights, focus by hour chart, trend detection
- **Deadline reminders** — urgency-sorted list with days remaining

---

## Project Structure

```
smart-scheduler/
├── backend/
│   ├── app.py                  # Flask entry point
│   ├── requirements.txt
│   ├── .env.example
│   ├── models/
│   │   └── db.py               # SQLAlchemy models (User, Task, Activity)
│   ├── routes/
│   │   ├── auth.py             # Register, login, JWT
│   │   ├── tasks.py            # Task CRUD
│   │   ├── schedule.py         # Schedule generation
│   │   ├── dashboard.py        # Analytics + chart data
│   │   ├── google_oauth.py     # Gmail sync + Google Calendar push
│   │   └── ai_assistant.py     # Claude AI chat endpoint
│   ├── services/
│   │   ├── scheduler.py        # Scheduling algorithm
│   │   └── insights.py         # Weekly productivity insights
│   └── ml/
│       └── model.py            # GradientBoosting ML model + heuristic fallback
│
└── frontend/
    ├── index.html
    ├── vite.config.js
    ├── package.json
    └── src/
        ├── main.jsx
        ├── App.jsx
        ├── index.css
        ├── context/
        │   └── AuthContext.jsx
        ├── hooks/
        │   └── useVoice.js      # Web Speech API (voice input + TTS)
        ├── services/
        │   └── api.js           # Axios API calls
        ├── pages/
        │   ├── AuthPage.jsx
        │   ├── AppShell.jsx
        │   ├── Dashboard.jsx
        │   ├── SchedulePage.jsx
        │   ├── CalendarPage.jsx
        │   ├── ProductivityPage.jsx
        │   ├── RemindersPage.jsx
        │   └── IntegrationsPage.jsx
        └── components/
            ├── Sidebar.jsx      # Sidebar + Topbar + all shared UI
            ├── AIPanel.jsx      # Right-side AI chat with voice
            └── *.jsx            # Re-export stubs
```

---

## Setup

### 1. PostgreSQL

```bash
# Create the database
psql -U postgres -c "CREATE DATABASE smart_scheduler;"
```

### 2. Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and fill in environment variables
cp .env.example .env
# Edit .env with your values (see below)

# Run
python app.py
# Backend runs on http://localhost:5000
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
# Frontend runs on http://localhost:5173
```

---

## Environment Variables (backend/.env)

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `JWT_SECRET_KEY` | Random secret for JWT signing |
| `GOOGLE_CLIENT_ID` | From Google Cloud Console |
| `GOOGLE_CLIENT_SECRET` | From Google Cloud Console |
| `GOOGLE_REDIRECT_URI` | `http://localhost:5000/auth/google/callback` |
| `ANTHROPIC_API_KEY` | From console.anthropic.com |
| `FRONTEND_URL` | `http://localhost:5173` |

---

## Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project (or use existing)
3. Enable these APIs:
   - **Gmail API**
   - **Google Calendar API**
   - **Google People API**
4. Go to **OAuth consent screen** → add scopes:
   - `gmail.readonly`
   - `calendar`
   - `userinfo.email`
   - `userinfo.profile`
5. Go to **Credentials** → Create **OAuth 2.0 Client ID**
   - Type: **Web application**
   - Authorised redirect URI: `http://localhost:5000/auth/google/callback`
6. Copy Client ID and Client Secret into your `.env`

---

## How Gmail Sync Works

1. Reads your **last 50 unread inbox emails** (read-only, never modifies Gmail)
2. Detects emails with action keywords: `deadline`, `urgent`, `asap`, `please complete`, `review by`, `submit`, `follow up`, etc.
3. Extracts the **subject as task name**, **priority** from urgency words, **deadline** from date patterns in body
4. Creates tasks with `source=gmail` — visible in the Reminders page with a 📧 badge
5. Already-synced emails are tracked by message ID — never duplicated

---

## How Calendar Sync Works

1. Pushes all pending tasks that have a **scheduled time slot** to your Google Calendar
2. Events are **colour-coded** by priority (red = High, yellow = Medium, green = Low)
3. Each event includes **email + popup reminders** (60 min and 30 min before)
4. Re-running sync **updates** existing events rather than creating duplicates

---

## AI Assistant

The right-side panel connects to the **Claude API** (claude-sonnet-4-20250514). It receives:
- All your current tasks with priorities and deadlines
- Today's schedule
- Your best focus hour (from ML model)
- Weekly insights (completion rate, trend, performance)

Voice input uses the **Web Speech API** (Chrome/Edge). Voice output via **Web Speech Synthesis**.

---

## ML Model

Uses a **Gradient Boosting Classifier** (scikit-learn) trained on your activity history:
- Features: hour of day, focus rating, difficulty, priority, day of week, cyclic hour encoding
- Falls back to a pure-Python heuristic if scikit-learn is unavailable
- Retrains per user on demand, cached in memory

---

## Production Notes

- Set `JWT_ACCESS_TOKEN_EXPIRES` to a real duration (e.g. `timedelta(days=7)`)
- Use **gunicorn** for the Flask backend: `gunicorn app:create_app()`
- Build the frontend: `npm run build` → serve `dist/` via nginx
- Store `DATABASE_URL` as a proper environment secret
- Add HTTPS before deploying Google OAuth to production (required by Google)
=======
# Smart-Scheduler
>>>>>>> 6f6301d93b82d2d98409e0401aa1cb8f5bf2368e
