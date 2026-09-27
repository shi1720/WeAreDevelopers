"""Verifier-owned fresh-process transfer check; no exports/tokens are written.

Start identical disposable containers on 18091 and 18092, then run this file.
"""
import copy
import json
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def request(base, method, path, body=None, token=None, key=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    if key:
        headers["Idempotency-Key"] = key
    try:
        response = urlopen(Request(base + path, method=method, headers=headers,
                                  data=None if body is None else json.dumps(body).encode()), timeout=10)
    except HTTPError as error:
        response = error
    with response:
        raw = response.read()
        return response.status, json.loads(raw) if raw else None


def main():
    started = time.monotonic()
    source, destination = "http://127.0.0.1:18091", "http://127.0.0.1:18092"
    data = {"users": [{"id": "x", "email": "transfer@example.test", "password": "synthetic-transfer", "display_name": "Transfer"}],
            "restaurants": [{"id": "r", "name": "Transfer", "timezone": "America/New_York",
                             "slot_minutes": 30, "reservation_duration_minutes": 90,
                             "cancellation_cutoff_minutes": 60,
                             "opening_hours": [{"weekday": d, "opens": "17:00", "closes": "23:00"}
                                               for d in "mon tue wed thu fri sat sun".split()],
                             "tables": [{"id": "a", "label": "A", "capacity": 4}, {"id": "b", "label": "B", "capacity": 4}]}],
            "reservations": []}
    for base in (source, destination):
        assert request(base, "POST", "/_test/reset", data)[0] == 204
    login = {"email": "transfer@example.test", "password": "synthetic-transfer"}
    token = request(source, "POST", "/auth/login", login)[1]["token"]
    stale_token = request(destination, "POST", "/auth/login", login)[1]["token"]
    body = {"restaurant_id": "r", "table_id": "a", "starts_at_local": "2033-05-11T18:00", "party_size": 2}
    status, created = request(source, "POST", "/reservations", body, token, "creation")
    assert status == 201
    moves = {"moves": [{"reference": created["reference"], "table_id": "b"}]}
    status, moved = request(source, "POST", "/reservation-moves", moves, token, "moving")
    assert status == 201
    exported = request(source, "GET", "/_test/export")[1]
    retained = copy.deepcopy(exported)
    assert request(source, "POST", "/reservations/" + created["reference"] + "/cancel", {}, token)[0] == 200
    assert exported == retained
    for _ in range(2):
        assert request(destination, "POST", "/_test/import", exported)[0] == 204
        assert request(destination, "GET", "/reservations", token=stale_token)[0] == 401
        assert request(destination, "POST", "/auth/login", login)[0] == 200
        assert request(destination, "POST", "/reservations", body, token, "creation") == (200, created)
        assert request(destination, "POST", "/reservation-moves", moves, token, "moving") == (200, moved)
        assert request(destination, "GET", "/reservations/" + created["reference"], token=token)[1] == moved["reservations"][0]
    print("PASS fresh-process transfer, destination replacement, preserved credentials/session/identity/timestamps/create-and-batch receipts; repeated import; detached snapshot")
    print("duration_seconds=" + str(round(time.monotonic() - started, 3)))


if __name__ == "__main__":
    main()
