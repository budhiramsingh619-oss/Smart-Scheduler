from __future__ import annotations
import threading
from models.db import Activity, Task
from flask import current_app

try:
    import pandas as pd
    import numpy as np
    from sklearn.ensemble import GradientBoostingClassifier
    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import Pipeline
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

PRIORITY_MAP = {"High": 3, "Medium": 2, "Low": 1}

_MODEL_CACHE: dict = {}
_LOCK = threading.Lock()

FALLBACK_DATA = [
    {"hour": 7,  "focus": 8, "difficulty": 5, "priority": "High",   "completed": 1, "day_of_week": 1},
    {"hour": 9,  "focus": 9, "difficulty": 6, "priority": "High",   "completed": 1, "day_of_week": 2},
    {"hour": 11, "focus": 7, "difficulty": 7, "priority": "Medium", "completed": 1, "day_of_week": 3},
    {"hour": 13, "focus": 6, "difficulty": 5, "priority": "Medium", "completed": 1, "day_of_week": 1},
    {"hour": 15, "focus": 6, "difficulty": 4, "priority": "Low",    "completed": 0, "day_of_week": 4},
    {"hour": 17, "focus": 5, "difficulty": 3, "priority": "Low",    "completed": 0, "day_of_week": 5},
    {"hour": 20, "focus": 3, "difficulty": 2, "priority": "Low",    "completed": 0, "day_of_week": 6},
]


class HeuristicModel:
    """Pure-Python fallback when scikit-learn is unavailable."""

    def predict_proba(self, rows):
        results = []
        vals = rows.values.tolist() if hasattr(rows, "values") else rows
        for row in vals:
            hour, focus, difficulty, priority_score, dow = row[:5]
            fc = max(0, min(10, float(focus))) / 10
            hc = 1 - min(abs(float(hour) - 10), 10) / 10
            pc = float(priority_score) / 3
            dp = max(0, min(10, float(difficulty))) / 25
            # Morning boost (7–11) and slight afternoon dip
            time_bonus = 0.05 if 7 <= hour <= 11 else -0.03 if hour >= 20 else 0
            prob = max(0.05, min(0.95, fc * 0.42 + hc * 0.24 + pc * 0.18 - dp + time_bonus + 0.12))
            results.append([1 - prob, prob])
        return results


def _load_activity(user_id: int) -> list[dict]:
    from sqlalchemy import text
    rows = (
        Activity.query
        .join(Task, Activity.task_id == Task.id, isouter=True)
        .filter(Activity.user_id == user_id)
        .with_entities(
            Activity.hour, Activity.focus, Activity.completed, Activity.created_at,
            Task.difficulty, Task.priority,
        )
        .order_by(Activity.created_at)
        .all()
    )
    result = []
    for r in rows:
        result.append({
            "hour": r.hour,
            "focus": r.focus,
            "completed": 1 if r.completed else 0,
            "difficulty": r.difficulty or 5,
            "priority": r.priority or "Medium",
            "day_of_week": r.created_at.weekday() if r.created_at else 0,
        })
    return result


def _normalize(rows: list[dict]) -> list[dict]:
    out = []
    for r in rows:
        priority = r.get("priority") if r.get("priority") in PRIORITY_MAP else "Medium"
        out.append({
            "hour": max(0, min(23, int(r.get("hour") or 10))),
            "focus": max(0, min(10, int(r.get("focus") or 6))),
            "difficulty": max(1, min(10, int(r.get("difficulty") or 5))),
            "priority": priority,
            "completed": 1 if int(r.get("completed") or 0) == 1 else 0,
            "day_of_week": int(r.get("day_of_week") or 0),
        })
    return out


def train_model(user_id: int):
    with _LOCK:
        if user_id in _MODEL_CACHE:
            return _MODEL_CACHE[user_id]

        if len(_MODEL_CACHE) > 100:
            oldest = next(iter(_MODEL_CACHE))
            del _MODEL_CACHE[oldest]

    try:
        rows = _normalize(_load_activity(user_id))
    except Exception:
        rows = []

    if len(rows) < 5 or len({r["completed"] for r in rows}) < 2:
        rows = FALLBACK_DATA

    if not ML_AVAILABLE:
        model = HeuristicModel()
        with _LOCK:
            _MODEL_CACHE[user_id] = model
        return model

    df = pd.DataFrame(rows)
    df["priority_score"] = df["priority"].map(PRIORITY_MAP).fillna(2)
    # Add cyclic time encoding for hour
    df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
    df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)

    features = ["hour", "focus", "difficulty", "priority_score", "day_of_week", "hour_sin", "hour_cos"]
    X = df[features]
    y = df["completed"]

    model = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", GradientBoostingClassifier(n_estimators=80, max_depth=3, learning_rate=0.1, random_state=42)),
    ])
    model.fit(X, y)

    with _LOCK:
        _MODEL_CACHE[user_id] = model

    return model


def _make_frame(hour, focus, difficulty, priority_score, day_of_week=0):
    if ML_AVAILABLE:
        import pandas as pd
        import numpy as np
        return pd.DataFrame([{
            "hour": hour, "focus": focus, "difficulty": difficulty,
            "priority_score": priority_score, "day_of_week": day_of_week,
            "hour_sin": np.sin(2 * np.pi * hour / 24),
            "hour_cos": np.cos(2 * np.pi * hour / 24),
        }])
    return [[hour, focus, difficulty, priority_score, day_of_week, 0, 0]]


def best_time(model) -> dict:
    best_score = 0.0
    best_hour = 8
    from datetime import datetime
    dow = datetime.now().weekday()
    for hour in range(6, 22):
        for focus in range(6, 10):
            frame = _make_frame(hour, focus, 5, 2, dow)
            prob = model.predict_proba(frame)[0][1]
            if prob > best_score:
                best_score = prob
                best_hour = hour
    return {"best_hour": best_hour, "confidence": round(float(best_score), 2)}


def predict_productivity(model, hour: int, focus: int, difficulty: int = 5, priority: str = "Medium") -> float:
    ps = PRIORITY_MAP.get(priority, 2)
    from datetime import datetime
    dow = datetime.now().weekday()
    frame = _make_frame(hour, focus, difficulty, ps, dow)
    return round(float(model.predict_proba(frame)[0][1]), 2)


def invalidate_cache(user_id: int):
    with _LOCK:
        _MODEL_CACHE.pop(user_id, None)
