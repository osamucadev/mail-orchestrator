from __future__ import annotations

from datetime import datetime, timezone


def format_relative_time(sent_at: datetime, now: datetime | None = None) -> str:
    if now is None:
        now = datetime.now(timezone.utc)
    if sent_at.tzinfo is None:
        sent_at = sent_at.replace(tzinfo=timezone.utc)
    delta = now - sent_at
    seconds = int(delta.total_seconds())
    if seconds < 0:
        seconds = 0
    minutes = seconds // 60
    hours = minutes // 60
    days = hours // 24
    if minutes < 1:
        return "just now"
    if minutes < 60:
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    if hours < 24:
        return f"{hours} hour{'s' if hours != 1 else ''} ago"

    remaining_hours = hours % 24
    
    if remaining_hours == 0:
        return f"{days} day{'s' if days != 1 else ''} ago"
    else:
        return f"{days} day{'s' if days != 1 else ''} and {remaining_hours} hour{'s' if remaining_hours != 1 else ''} ago"


def pick_status_emoji(elapsed_minutes: int, thresholds: dict) -> str:
    """
    thresholds expects:
    t_white_minutes, t_blue_minutes, t_yellow_minutes, t_red_minutes
    """
    t_white = int(thresholds["t_white_minutes"])
    t_blue = int(thresholds["t_blue_minutes"])
    t_yellow = int(thresholds["t_yellow_minutes"])
    t_red = int(thresholds["t_red_minutes"])

    if elapsed_minutes <= t_white:
        return "⚪"
    if elapsed_minutes <= t_blue:
        return "🔵"
    if elapsed_minutes <= t_yellow:
        return "🟡"
    if elapsed_minutes <= t_red:
        return "🔴"
    return "🔴"
