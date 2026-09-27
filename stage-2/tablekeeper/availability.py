"""Read-only availability over a caller-provided consistent state snapshot."""

from datetime import datetime, timezone

from .temporal import iter_slots
from .validation import APIError


def overlaps(start: datetime, end: datetime, reservation: dict) -> bool:
    """Half-open interval overlap, compared as instants even within a DST fold."""
    other_start = datetime.fromisoformat(reservation["starts_at"]).astimezone(timezone.utc)
    other_end = datetime.fromisoformat(reservation["ends_at"]).astimezone(timezone.utc)
    return start.astimezone(timezone.utc) < other_end and other_start < end.astimezone(timezone.utc)


def get_availability(restaurant: dict, reservations: list[dict], date: str, party_size: int) -> dict:
    if type(party_size) is not int or party_size < 1:
        raise APIError(422, "validation_failed", "Party size must be a positive integer")
    occupied = {}
    for reservation in reservations:
        if reservation["restaurant_id"] == restaurant["id"] and reservation["status"] == "confirmed":
            occupied.setdefault(reservation["table_id"], []).append(reservation)
    slots = []
    for start, end in iter_slots(restaurant, date):
        available = [table["id"] for table in restaurant["tables"]
                     if table["capacity"] >= party_size and not any(
                         overlaps(start, end, reservation)
                         for reservation in occupied.get(table["id"], ()))]
        slots.append({"starts_at_local": start.isoformat(timespec="minutes")[:16],
                      "starts_at": start.isoformat(), "available_table_ids": available})
    return {"restaurant_id": restaurant["id"], "date": date,
            "timezone": restaurant["timezone"], "slots": slots}
