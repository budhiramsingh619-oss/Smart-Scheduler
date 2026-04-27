from copy import deepcopy
from datetime import datetime

from models.db import db, Task

PRIORITY_SCORE = {"High": 3, "Medium": 2, "Low": 1}


def _days_left(task_dict: dict) -> int:
    deadline = task_dict.get("deadline")
    if not deadline:
        return 999
    try:
        target = datetime.strptime(deadline, "%Y-%m-%d").date()
        return (target - datetime.today().date()).days
    except (TypeError, ValueError):
        return 999


def _calc_score(task: dict) -> float:
    ps = PRIORITY_SCORE.get(task.get("priority", "Medium"), 2)
    d = max(1, min(10, int(task.get("difficulty") or 5)))
    dl = _days_left(task)
    ds = 4 if dl < 0 else 3 if dl <= 1 else 2 if dl <= 3 else 1 if dl <= 7 else 0
    return round(ps * 2 + d * 0.5 + ds * 2, 2)


def _prepare(tasks: list) -> list:
    out = []
    for t in tasks:
        if t.get("completed"):
            continue
        task = deepcopy(t)
        dl = _days_left(task)
        if dl <= 1:
            task["priority"] = "High"
        elif dl <= 3 and task.get("priority") == "Low":
            task["priority"] = "Medium"
        dur = max(1, min(8, int(task.get("duration") or 1)))
        if int(task.get("difficulty") or 5) >= 8 and dur < 3:
            dur += 1
        task["duration"] = dur
        task["_score"] = _calc_score(task)
        task["_days"] = dl
        out.append(task)
    return sorted(out, key=lambda x: (-x["_score"], x["_days"], x.get("name", "")))


def generate_schedule(tasks: list, start_hour: int = 7, max_daily: int = 10) -> list:
    prepared = _prepare(tasks)
    schedule = []
    current = max(5, min(20, start_hour))
    day_end = 22
    worked = 0
    peak = set(range(current, min(current + 4, day_end)))

    for task in prepared:
        dur = max(1, min(8, int(task.get("duration") or 1)))
        diff = int(task.get("difficulty") or 5)

        if worked + dur > max_daily:
            break
        if diff >= 7 and current not in peak:
            future = [h for h in peak if h >= current]
            if future and future[0] + dur <= day_end:
                current = future[0]
        if current + dur > day_end:
            continue

        brk = 1 if dur <= 2 else 2
        schedule.append({
            "id": task["id"],
            "task": task["name"],
            "start": f"{current:02d}:00",
            "end": f"{current + dur:02d}:00",
            "priority": task.get("priority", "Medium"),
            "category": task.get("category") or "General",
            "difficulty": diff,
            "score": task["_score"],
            "deadline": task.get("deadline"),
        })
        current = current + dur + brk
        worked += dur
        if worked >= 3 and worked % 3 == 0:
            current += 1

    return schedule


def refresh_schedule(user_id: int, start_hour: int = 7) -> list:
    """Recalculate schedule and write scheduled_start/end back to DB."""
    from ml.model import best_time, train_model

    model = train_model(user_id)
    bt = best_time(model)
    sh = start_hour or bt["best_hour"]

    tasks = Task.query.filter_by(user_id=user_id, completed=False).all()
    task_dicts = [t.to_dict() for t in tasks]
    schedule = generate_schedule(task_dicts, start_hour=sh)

    # Clear existing schedule slots
    for t in tasks:
        t.scheduled_start = None
        t.scheduled_end = None

    # Write new slots
    slot_map = {item["id"]: item for item in schedule}
    for t in tasks:
        if t.id in slot_map:
            t.scheduled_start = slot_map[t.id]["start"]
            t.scheduled_end = slot_map[t.id]["end"]

    db.session.commit()
    return schedule
