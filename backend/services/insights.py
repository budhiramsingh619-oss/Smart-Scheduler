from datetime import datetime, timedelta
import statistics


def weekly_insights(activity: list) -> dict:
    week_ago = datetime.now() - timedelta(days=7)

    recent = [
        a for a in activity
        if datetime.fromisoformat(a["created_at"].replace("Z", "+00:00")).replace(tzinfo=None) >= week_ago
    ]

    total = len(recent)
    if total == 0:
        return {
            "completed_tasks": 0, "missed_tasks": 0, "completion_rate": 0,
            "avg_focus": 0, "productivity_score": 0, "focus_consistency": 10,
            "high_focus_ratio": 0, "trend": "No Data", "performance": "No Data",
            "suggestion": "Start completing tasks to generate insights.",
        }

    completed = sum(1 for a in recent if a.get("completed"))
    missed = total - completed
    cr = round((completed / total) * 100, 2)

    focus_vals = [max(0, min(10, int(a.get("focus") or 0))) for a in recent]
    avg_f = round(sum(focus_vals) / total, 2)
    high_f = round(sum(1 for f in focus_vals if f >= 7) / total * 100, 2)

    fc = round(max(0, 10 - statistics.stdev(focus_vals)), 2) if len(focus_vals) > 1 else 10
    ps = round(min(100, cr * 0.6 + avg_f * 3 + fc), 2)

    trend = "Stable"
    mid = total // 2
    f1, f2 = focus_vals[:mid], focus_vals[mid:]
    if f1 and f2:
        a1, a2 = sum(f1) / len(f1), sum(f2) / len(f2)
        if a2 > a1 + 0.25:
            trend = "Improving"
        elif a2 < a1 - 0.25:
            trend = "Declining"

    if cr >= 85 and avg_f >= 7:
        perf = "Excellent"
        sug = "Great work. Keep scheduling complex tasks during your strongest hours."
    elif cr >= 65:
        perf = "Good"
        sug = "You are doing well. Batch similar tasks to reduce context switching."
    elif cr >= 40:
        perf = "Average"
        sug = "Use shorter work sessions and reduce the number of active tasks."
    else:
        perf = "Needs Improvement"
        sug = "Reduce workload and focus on a few key tasks first."

    if avg_f < 5:
        sug += " Your focus trend suggests fewer distractions would help."
    if fc < 5:
        sug += " A more consistent work routine could improve reliability."
    if high_f < 40:
        sug += " Move demanding tasks into your peak energy hours."

    return {
        "completed_tasks": completed, "missed_tasks": missed, "completion_rate": cr,
        "avg_focus": avg_f, "productivity_score": ps, "focus_consistency": fc,
        "high_focus_ratio": high_f, "trend": trend, "performance": perf, "suggestion": sug,
    }
