"""Read-only availability over a caller-provided consistent state snapshot."""

from datetime import datetime, timezone

from .temporal import iter_slots
from .validation import APIError
from .policies import base_terms, effective_restaurant


def overlaps(start: datetime, end: datetime, reservation: dict) -> bool:
    """Half-open interval overlap, compared as instants even within a DST fold."""
    other_start = datetime.fromisoformat(reservation["starts_at"]).astimezone(timezone.utc)
    other_end = datetime.fromisoformat(reservation["ends_at"]).astimezone(timezone.utc)
    return start.astimezone(timezone.utc) < other_end and other_start < end.astimezone(timezone.utc)


def get_availability(restaurant: dict, reservations: list[dict], date: str, party_size: int, *, policy=None, explain=False, closures=()) -> dict:
    if type(party_size) is not int or party_size < 1:
        raise APIError(422, "validation_failed", "Party size must be a positive integer")
    restaurant = effective_restaurant(restaurant, policy if policy is not None else base_terms(restaurant))
    occupied = {}
    for closure in closures:
        if closure["restaurant_id"] == restaurant["id"]:
            occupied.setdefault(closure["table_id"], []).append({"starts_at": closure["from"], "ends_at": closure["to"]})
    for reservation in reservations:
        if reservation["restaurant_id"] == restaurant["id"] and reservation["status"] == "confirmed":
            for table_id in reservation.get("table_ids", [reservation.get("table_id")]):
                occupied.setdefault(table_id, []).append(reservation)
    slots = []
    for start, end in iter_slots(restaurant, date):
        decisions = []
        for table in restaurant["tables"]:
            capacity = table["capacity"] >= party_size
            no_overlap = not any(overlaps(start, end, reservation)
                                 for reservation in occupied.get(table["id"], ()))
            decisions.append({"table_id": table["id"], "policy_version": restaurant.get("policy_version", 0),
                              "available": capacity and no_overlap,
                              "rules": [{"rule": "capacity", "holds": capacity},
                                        {"rule": "no_overlap", "holds": no_overlap}]})
        available = [decision["table_id"] for decision in decisions if decision["available"]]
        capacities = {table["id"]: table["capacity"] for table in restaurant["tables"]}
        options = [{"table_ids": [tid], "capacity": capacities[tid]} for tid in available]
        for pair in restaurant.get("combinable", []):
            capacity = sum(capacities[tid] for tid in pair)
            if capacity >= party_size and not any(
                    overlaps(start, end, reservation)
                    for tid in pair for reservation in occupied.get(tid, ())):
                options.append({"table_ids": list(pair), "capacity": capacity})
        slots.append({"starts_at_local": start.isoformat(timespec="minutes")[:16],
                      "starts_at": start.isoformat(), "available_table_ids": available,
                      "available_options": options})
        if explain:
            slots[-1]["explain"] = decisions
    return {"restaurant_id": restaurant["id"], "date": date,
            "timezone": restaurant["timezone"], "slots": slots}
