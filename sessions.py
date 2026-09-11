"""
EarLog - sessions.py

Turns raw connect/disconnect events into "focus sessions" (a connected
event paired with the next disconnected event = one session, with a
duration). Used by api.py to serve session and stats data.
"""

from datetime import datetime, timedelta, timezone

from db import get_connection


def _parse(ts: str) -> datetime:
    return datetime.fromisoformat(ts)


def get_sessions():
    """
    Returns a list of sessions, most recent first:
    [{"start": iso, "end": iso, "duration_minutes": float, "ongoing": bool}, ...]
    """
    conn = get_connection()
    rows = conn.execute(
        "SELECT timestamp, event_type FROM events ORDER BY timestamp ASC"
    ).fetchall()
    conn.close()

    sessions = []
    open_start = None

    for row in rows:
        if row["event_type"] == "connected":
            # A new "connected" while one is already open just resets the
            # start time to this most recent connect (defensive, in case
            # of duplicate/missed signals).
            open_start = row["timestamp"]
        elif row["event_type"] == "disconnected" and open_start is not None:
            start_dt = _parse(open_start)
            end_dt = _parse(row["timestamp"])
            duration_min = (end_dt - start_dt).total_seconds() / 60.0
            sessions.append(
                {
                    "start": open_start,
                    "end": row["timestamp"],
                    "duration_minutes": round(duration_min, 1),
                    "ongoing": False,
                }
            )
            open_start = None

    # If there's a still-open session (earbuds currently connected),
    # report it as ongoing using "now" as the provisional end.
    if open_start is not None:
        start_dt = _parse(open_start)
        now = datetime.now(timezone.utc)
        duration_min = (now - start_dt).total_seconds() / 60.0
        sessions.append(
            {
                "start": open_start,
                "end": None,
                "duration_minutes": round(duration_min, 1),
                "ongoing": True,
            }
        )

    sessions.reverse()  # most recent first
    return sessions


def get_stats():
    """
    Returns summary stats:
    {
      "today_minutes": float,
      "week_minutes": float,
      "longest_session_minutes": float,
      "total_sessions": int,
      "streak_days": int
    }
    """
    sessions = get_sessions()
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())

    today_minutes = 0.0
    week_minutes = 0.0
    longest = 0.0
    days_with_session = set()

    for s in sessions:
        start_dt = _parse(s["start"])
        today_minutes += s["duration_minutes"] if start_dt >= today_start else 0
        week_minutes += s["duration_minutes"] if start_dt >= week_start else 0
        longest = max(longest, s["duration_minutes"])
        days_with_session.add(start_dt.date())

    # Simple streak: count consecutive days ending today with at least
    # one session.
    streak = 0
    check_day = today_start.date()
    while check_day in days_with_session:
        streak += 1
        check_day = check_day - timedelta(days=1)

    return {
        "today_minutes": round(today_minutes, 1),
        "week_minutes": round(week_minutes, 1),
        "longest_session_minutes": round(longest, 1),
        "total_sessions": len(sessions),
        "streak_days": streak,
    }
