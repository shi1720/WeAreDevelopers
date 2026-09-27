"""Restaurant wall-clock grids with absolute, DST-safe booking intervals."""

import re
from datetime import date as Date, datetime, timedelta, timezone as tz
from zoneinfo import ZoneInfo

from .validation import APIError

UTC = tz.utc
_LOCAL = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}\Z")
_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}\Z")
_WEEKDAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")


def _local_value(value):
    if not isinstance(value, str):
        raise APIError(400, "malformed_request", "Local start must be a string")
    if not _LOCAL.fullmatch(value):
        raise APIError(422, "validation_failed", "Use YYYY-MM-DDTHH:MM")
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        raise APIError(422, "validation_failed", "Invalid local date or time") from None


def _date_value(value):
    if not isinstance(value, str) or not _DATE.fullmatch(value):
        raise APIError(422, "validation_failed", "Use YYYY-MM-DD")
    try:
        return Date.fromisoformat(value)
    except ValueError:
        raise APIError(422, "validation_failed", "Invalid calendar date") from None


def resolve_local(timezone: str, local: str) -> datetime:
    """Choose the first occurrence of folds; round-trip to reject gaps."""
    naive = _local_value(local)
    zone = ZoneInfo(timezone)
    aware = naive.replace(tzinfo=zone, fold=0)
    try:
        restored = aware.astimezone(UTC).astimezone(zone)
    except (OverflowError, ValueError):
        raise APIError(422, "validation_failed", "Local time is outside supported range") from None
    if restored.replace(tzinfo=None) != naive:
        raise APIError(422, "invalid_local_time", "This local time does not exist")
    return aware


def _hours(restaurant, day):
    weekday = _WEEKDAYS[day.weekday()]
    return next((h for h in restaurant["opening_hours"] if h["weekday"] == weekday), None)


def _minute(value):
    hour, minute = value.split(":")
    return int(hour) * 60 + int(minute)


def booking_interval(restaurant: dict, starts_at_local: str) -> tuple[datetime, datetime]:
    start = resolve_local(restaurant["timezone"], starts_at_local)
    hours = _hours(restaurant, start.date())
    if hours is None:
        raise APIError(422, "outside_opening_hours", "Restaurant is closed on this day")
    minute = start.hour * 60 + start.minute
    opening, closing = _minute(hours["opens"]), _minute(hours["closes"])
    try:
        end = (start.astimezone(UTC) + timedelta(minutes=restaurant["reservation_duration_minutes"])).astimezone(start.tzinfo)
        # A boundary inside a spring gap maps to its transition-forward instant.
        # Boundaries are limits, not bookable starts. A repeated close uses fold=0.
        close = datetime.combine(start.date(), datetime.strptime(hours["closes"], "%H:%M").time(), start.tzinfo)
        end_after_close = end.astimezone(UTC) > close.astimezone(UTC)
    except (OverflowError, ValueError):
        raise APIError(422, "outside_opening_hours", "Booking ends outside supported opening hours") from None
    if minute < opening or minute >= closing or end_after_close:
        raise APIError(422, "outside_opening_hours", "Booking must fit within opening hours")
    if (minute - opening) % restaurant["slot_minutes"]:
        raise APIError(422, "not_on_slot_grid", "Start must be on the restaurant slot grid")
    return start, end


def iter_slots(restaurant: dict, date: str):
    day = _date_value(date)
    hours = _hours(restaurant, day)
    if hours is None:
        return
    for minute in range(_minute(hours["opens"]), _minute(hours["closes"]), restaurant["slot_minutes"]):
        local = f"{date}T{minute // 60:02d}:{minute % 60:02d}"
        try:
            yield booking_interval(restaurant, local)
        except APIError as error:
            if error.code not in ("invalid_local_time", "outside_opening_hours"):
                raise
