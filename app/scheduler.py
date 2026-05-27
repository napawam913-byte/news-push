from __future__ import annotations

import random
from datetime import datetime, time, timedelta

from app.config import Settings


def is_active_now(settings: Settings, now: datetime | None = None) -> bool:
    current = now or datetime.now().astimezone()
    if settings.workday_only and current.weekday() >= 5:
        return False

    start_hour = _clamp_start_hour(settings.active_start_hour)
    end_hour = _clamp_end_hour(settings.active_end_hour)
    current_hour = current.hour + current.minute / 60 + current.second / 3600

    if end_hour == 24:
        return start_hour <= current_hour < 24
    if start_hour <= end_hour:
        return start_hour <= current_hour < end_hour
    return current_hour >= start_hour or current_hour < end_hour


def seconds_until_next_active_window(settings: Settings, now: datetime | None = None) -> int:
    current = now or datetime.now().astimezone()
    if is_active_now(settings, current):
        return 0

    start_hour = _clamp_start_hour(settings.active_start_hour)
    for day_offset in range(8):
        candidate_date = (current + timedelta(days=day_offset)).date()
        candidate = datetime.combine(
            candidate_date,
            time(hour=start_hour),
            tzinfo=current.tzinfo,
        )
        if candidate <= current:
            continue
        if settings.workday_only and candidate.weekday() >= 5:
            continue
        return max(60, int((candidate - current).total_seconds()))

    return 3600


def next_interval_seconds(settings: Settings) -> int:
    minimum = max(1, settings.interval_min_seconds)
    maximum = max(minimum, settings.interval_max_seconds)
    return random.randint(minimum, maximum)


def format_duration(seconds: int) -> str:
    hours, remainder = divmod(max(0, seconds), 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours}h{minutes:02d}m"
    if minutes:
        return f"{minutes}m{seconds:02d}s"
    return f"{seconds}s"


def _clamp_start_hour(hour: int) -> int:
    return min(max(hour, 0), 23)


def _clamp_end_hour(hour: int) -> int:
    return min(max(hour, 1), 24)
