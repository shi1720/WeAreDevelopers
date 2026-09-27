"""Independent, spec-derived HTTP checks. Run against a disposable service only.

TABLEKEEPER_BASE_URL=http://127.0.0.1:8080 python -m unittest discover \
    -s stage-1/tests -p 'independent_*.py' -v
No service imports; exports and tokens remain in memory and are never printed.
"""
import calendar
import copy
import json
import os
import re
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


BASE = os.environ.get("TABLEKEEPER_BASE_URL", "http://127.0.0.1:8080").rstrip("/")
PASSWORD = "synthetic-only-passphrase"
WEEKDAYS = "mon tue wed thu fri sat sun".split()


def fixture(zone="Etc/UTC", duration=60, slot=30, cutoff=0):
    return {
        "users": [{"id": "user-a", "email": "ada@example.test", "password": PASSWORD,
                   "display_name": "Ada"},
                  {"id": "user-b", "email": "bea@example.test", "password": PASSWORD,
                   "display_name": "Bea"}],
        "restaurants": [{"id": "r-independent", "name": "Independent Hearth", "timezone": zone,
                         "slot_minutes": slot, "reservation_duration_minutes": duration,
                         "cancellation_cutoff_minutes": cutoff,
                         "opening_hours": [{"weekday": day, "opens": "00:00", "closes": "23:59"}
                                           for day in WEEKDAYS],
                         "tables": [{"id": "table-z", "label": "Window", "capacity": 2},
                                    {"id": "table-a", "label": "Garden", "capacity": 4},
                                    {"id": "table-m", "label": "Hearth", "capacity": 8}]}],
        "reservations": [],
    }


class IndependentContract(unittest.TestCase):
    def request(self, method, path, body=None, token=None, key=None, raw=None):
        headers = {"Content-Type": "application/json; charset=utf-8"}
        if token is not None:
            headers["Authorization"] = "Bearer " + token
        if key is not None:
            headers["Idempotency-Key"] = key
        data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
        started = time.monotonic()
        try:
            response = urlopen(Request(BASE + path, data=data, headers=headers, method=method),
                               timeout=10 if path.startswith("/_test/") else 5)
        except HTTPError as error:
            response = error
        with response:
            payload = response.read()
            status = response.status
            content_type = response.headers.get("Content-Type", "")
        elapsed = time.monotonic() - started
        self.assertLess(elapsed, 10 if path.startswith("/_test/") else 5, "request timeout budget")
        if payload:
            self.assertIn("application/json", content_type)
            self.assertIn("charset=utf-8", content_type.lower().replace(" ", ""))
            decoded = json.loads(payload)
        else:
            decoded = None
        if status >= 400:
            self.assertIsInstance(decoded.get("error", {}).get("message"), str)
            self.assertTrue(decoded["error"]["message"])
        self.assertLess(status, 500, "service returned 5xx")
        return status, decoded

    def expect(self, status, method, path, body=None, token=None, key=None, code=None, raw=None):
        actual, result = self.request(method, path, body, token, key, raw)
        # Never include successful authentication/export bodies in assertion diagnostics.
        self.assertEqual(actual, status, f"{method} {path}: status {actual}; error={result.get('error') if isinstance(result, dict) else None}")
        if code:
            self.assertEqual(result["error"]["code"], code)
        return result

    def reset(self, data=None):
        self.expect(204, "POST", "/_test/reset", data or fixture())

    def login(self, email="ada@example.test"):
        return self.expect(200, "POST", "/auth/login", {"email": email, "password": PASSWORD})["token"]

    def setUp(self):
        self.reset()
        self.a = self.login()
        self.b = self.login("bea@example.test")

    def booking(self, table="table-z", local="2032-06-17T18:00", party=2, **extra):
        return dict(restaurant_id="r-independent", table_id=table,
                    starts_at_local=local, party_size=party, **extra)

    def create(self, key="create", **kwargs):
        return self.expect(201, "POST", "/reservations", self.booking(**kwargs), self.a, key)

    def availability(self, date="2032-06-17", party=2, **extra):
        return self.expect(200, "GET", "/availability?" + urlencode(dict(
            restaurant_id="r-independent", date=date, party_size=party, **extra)))

    def snapshot(self):
        return self.expect(200, "GET", "/_test/export")

    def concurrent(self, count, operation):
        barrier = threading.Barrier(count)
        def run(index):
            barrier.wait(timeout=10)
            return operation(index)
        with ThreadPoolExecutor(max_workers=count) as pool:
            return list(pool.map(run, range(count)))

    def test_health_public_configuration_and_closed_day(self):
        self.assertEqual(self.expect(200, "GET", "/health"), {"status": "ok"})
        restaurants = self.expect(200, "GET", "/restaurants?ignored=1")["restaurants"]
        self.assertEqual(restaurants[0]["timezone"], "Etc/UTC")
        detail = self.expect(200, "GET", "/restaurants/r-independent")
        self.assertEqual([x["id"] for x in detail["tables"]], ["table-z", "table-a", "table-m"])
        self.expect(404, "GET", "/restaurants/absent", code="not_found")
        data = fixture()
        data["restaurants"][0]["opening_hours"] = []
        self.reset(data)
        self.assertEqual(self.availability()["slots"], [])

    def test_auth_validation_multiple_sessions_and_reset_revocation(self):
        second = self.login()
        for token in (self.a, second):
            self.expect(200, "GET", "/reservations", token=token)
        for token in (None, "not-a-session"):
            self.expect(401, "GET", "/reservations", token=token, code="unauthenticated")
        self.expect(401, "POST", "/auth/login", {"email": "absent@example.test", "password": PASSWORD}, code="unauthenticated")
        self.expect(401, "POST", "/auth/login", {"email": "ada@example.test", "password": "wrong-value"}, code="unauthenticated")
        valid = {"email": "new@example.test", "password": PASSWORD, "display_name": "New", "unknown": [1]}
        self.expect(201, "POST", "/auth/signup", valid)
        self.expect(409, "POST", "/auth/signup", valid, code="email_taken")
        for changes in ({"email": "no-at"}, {"password": "short"}):
            self.expect(422, "POST", "/auth/signup", dict(valid, **changes), code="validation_failed")
        self.reset()
        self.expect(401, "GET", "/reservations", token=self.a, code="unauthenticated")

    def test_strict_body_query_and_error_types(self):
        for party in (True, False, "2", 0, -1, 1.5, None, [], {}):
            with self.subTest(party=party):
                self.expect(422, "POST", "/reservations", self.booking(party=party), self.a, "invalid", "validation_failed")
        for local in ("2032-06-17T18:00Z", "2032-06-17T18:00:00", "2032-06-17 18:00", "2032-02-30T18:00"):
            self.expect(422, "POST", "/reservations", self.booking(local=local), self.a, "invalid", "validation_failed")
        for field, value in (("restaurant_id", 12), ("table_id", []), ("starts_at_local", True)):
            body = self.booking(); body[field] = value
            self.expect(400, "POST", "/reservations", body, self.a, "invalid", "malformed_request")
        for raw in (b"{", b"[1]", b"null"):
            self.expect(400, "POST", "/reservations", token=self.a, key="invalid", raw=raw, code="malformed_request")
        self.expect(422, "POST", "/reservations", {}, self.a, "invalid", "validation_failed")
        for party in ("1e9", "4.0", "+4", "-1", "0", ""):
            self.expect(422, "GET", "/availability?" + urlencode(dict(restaurant_id="r-independent", date="2032-06-17", party_size=party)), code="validation_failed")
        for query in ("", "restaurant_id=r-independent&date=2032-06-17", "restaurant_id=r-independent&date=2032-02-30&party_size=2"):
            self.expect(422, "GET", "/availability?" + query, code="validation_failed")

    def test_idempotency_boundaries_value_equality_and_precedence(self):
        for key in (None, ""):
            self.expect(400, "POST", "/reservations", self.booking(), self.a, key, "missing_idempotency_key")
        self.expect(422, "POST", "/reservations", self.booking(), self.a, "x" * 256, "validation_failed")
        body = self.booking(unknown={"b": 2, "a": [1, True]})
        original = self.expect(201, "POST", "/reservations", body, self.a, "x" * 255)
        reordered = json.dumps(dict(reversed(list(body.items()))), indent=4).encode()
        replay = self.expect(200, "POST", "/reservations", token=self.a, key="x" * 255, raw=reordered)
        self.assertEqual(original, replay)
        self.expect(409, "POST", "/reservations", {"party_size": False}, self.a, "x" * 255, "idempotency_key_reuse")
        self.expect(409, "POST", "/reservations", dict(body, unknown={"b": 2, "a": [1, 1]}), self.a, "x" * 255, "idempotency_key_reuse")
        # User scope is independent, and failed claims must not consume the key.
        self.expect(409, "POST", "/reservations", self.booking(), self.b, "x" * 255, "table_unavailable")
        self.expect(201, "POST", "/reservations", self.booking(table="table-a"), self.b, "x" * 255)
        batch = {"moves": [{"reference": original["reference"]}]}
        self.expect(201, "POST", "/reservation-moves", batch, self.a, "x" * 255)

    def test_receipts_survive_amend_cancel_and_owner_isolation(self):
        body = self.booking()
        original = self.create()
        reference = original["reference"]
        self.assertRegex(reference, r"^[A-Z0-9]{6,12}$")
        self.assertLessEqual(len(original["reservation_id"]), 64)
        for suffix, method, payload in (("", "GET", None), ("", "PATCH", {"party_size": 1}), ("/cancel", "POST", {})):
            self.expect(404, method, "/reservations/" + reference + suffix, payload, self.b, code="not_found")
        changed = self.expect(200, "PATCH", "/reservations/" + reference, {"table_id": "table-a", "starts_at_local": "2032-06-17T20:00"}, self.a)
        for field in ("reference", "reservation_id", "created_at"):
            self.assertEqual(original[field], changed[field])
        cancelled = self.expect(200, "POST", "/reservations/" + reference + "/cancel", {}, self.a)
        self.assertEqual(cancelled, self.expect(200, "POST", "/reservations/" + reference + "/cancel", {}, self.a))
        self.expect(409, "PATCH", "/reservations/" + reference, {}, self.a, code="reservation_cancelled")
        self.assertEqual(original, self.expect(200, "POST", "/reservations", body, self.a, "create"))
        self.assertEqual(len(self.expect(200, "GET", "/reservations", token=self.a)["reservations"]), 1)
        self.assertEqual(self.expect(200, "GET", "/reservations", token=self.b)["reservations"], [])

    def test_half_open_intervals_grid_capacity_and_failed_patch(self):
        first = self.create()
        self.create(key="adjacent", local="2032-06-17T19:00")
        self.expect(409, "POST", "/reservations", self.booking(local="2032-06-17T18:30"), self.a, "overlap", "table_unavailable")
        self.expect(422, "POST", "/reservations", self.booking(local="2032-06-17T18:01"), self.a, "grid", "not_on_slot_grid")
        self.expect(422, "POST", "/reservations", self.booking(local="2032-06-17T23:30"), self.a, "end", "outside_opening_hours")
        self.expect(422, "POST", "/reservations", self.booking(party=3), self.a, "capacity", "party_exceeds_capacity")
        self.expect(409, "PATCH", "/reservations/" + first["reference"], {"starts_at_local": "2032-06-17T18:30"}, self.a, code="table_unavailable")
        self.assertEqual(first, self.expect(200, "GET", "/reservations/" + first["reference"], token=self.a))
        slots = {x["starts_at_local"]: x for x in self.availability()["slots"]}
        self.assertNotIn("table-z", slots["2032-06-17T18:30"]["available_table_ids"])
        self.assertIn("table-z", slots["2032-06-17T20:00"]["available_table_ids"])
        self.assertEqual(slots["2032-06-17T20:00"]["available_table_ids"], ["table-z", "table-a", "table-m"])

    def test_past_creation_and_current_cutoff(self):
        original = self.create(local="2001-01-01T18:00")
        ref = original["reference"]
        self.expect(409, "PATCH", "/reservations/" + ref, {"starts_at_local": "2032-06-17T18:00"}, self.a, code="cutoff_passed")
        self.expect(409, "POST", "/reservations/" + ref + "/cancel", {}, self.a, code="cutoff_passed")
        self.expect(409, "POST", "/reservation-moves", {"moves": [{"reference": ref, "party_size": False}]}, self.a, "past-batch", "cutoff_passed")

    def test_slots_from_opening_offset_and_full_empty_rows(self):
        data = fixture(duration=45, slot=20)
        data["restaurants"][0]["opening_hours"] = [{"weekday": day, "opens": "17:10", "closes": "18:30"} for day in WEEKDAYS]
        self.reset(data)
        self.a = self.login()
        slots = self.availability(party=9, ignored="yes")["slots"]
        self.assertEqual([s["starts_at_local"] for s in slots], ["2032-06-17T17:10", "2032-06-17T17:30"])
        self.assertTrue(all(s["available_table_ids"] == [] for s in slots))
        self.create(local="2032-06-17T17:10")
        self.expect(422, "POST", "/reservations", self.booking(local="2032-06-17T17:20"), self.a, "wrong-grid", "not_on_slot_grid")

    def test_dst_gaps_folds_absolute_durations_arbitrary_year(self):
        for zone, month, day, local, offset, ends in (
            ("Europe/Berlin", 10, 27, "02:30", "+02:00", "03:00:00+01:00"),
            ("America/New_York", 11, 3, "01:30", "-04:00", "02:00:00-05:00"),
        ):
            with self.subTest(zone=zone):
                self.reset(fixture(zone, duration=90)); self.a = self.login()
                date = f"2030-{month:02d}-{day:02d}"
                value = self.create(local=date + "T" + local)
                self.assertTrue(value["starts_at"].endswith(offset))
                self.assertEqual(value["ends_at"], date + "T" + ends)
                self.assertEqual(datetime.fromisoformat(value["ends_at"]) - datetime.fromisoformat(value["starts_at"]), timedelta(minutes=90))
                slots = self.availability(date)["slots"]
                self.assertEqual(sum(s["starts_at_local"] == date + "T" + local for s in slots), 1)
        for zone, date in (("Europe/Berlin", "2030-03-31"), ("America/New_York", "2030-03-10")):
            with self.subTest(gap=zone):
                self.reset(fixture(zone)); self.a = self.login()
                self.expect(422, "POST", "/reservations", self.booking(local=date + "T02:30"), self.a, "gap", "invalid_local_time")
                self.assertFalse(any(s["starts_at_local"].startswith(date + "T02:") for s in self.availability(date)["slots"]))

    def test_batch_swap_noop_receipt_and_atomic_failure(self):
        one = self.create(key="one")
        two = self.create(key="two", table="table-a")
        moves = {"moves": [{"reference": one["reference"], "table_id": "table-a"}, {"reference": two["reference"], "table_id": "table-z"}]}
        receipt = self.expect(201, "POST", "/reservation-moves", moves, self.a, "swap")
        self.assertEqual([r["reference"] for r in receipt["reservations"]], [one["reference"], two["reference"]])
        self.assertEqual([r["table_id"] for r in receipt["reservations"]], ["table-a", "table-z"])
        before = self.snapshot()
        bad = {"moves": [{"reference": one["reference"], "table_id": "table-m"}, {"reference": two["reference"], "table_id": "table-m"}]}
        self.expect(409, "POST", "/reservation-moves", bad, self.a, "retryable", "table_unavailable")
        self.assertTrue(before == self.snapshot(), "failed batch changed exported state")
        noop = {"moves": [{"reference": one["reference"]}]}
        self.assertEqual(self.expect(201, "POST", "/reservation-moves", noop, self.a, "retryable")["reservations"], [receipt["reservations"][0]])
        self.expect(200, "POST", "/reservations/" + one["reference"] + "/cancel", {}, self.a)
        self.assertEqual(receipt, self.expect(200, "POST", "/reservation-moves", moves, self.a, "swap"))

    def test_batch_shape_owner_and_input_order(self):
        one = self.create()
        ref = one["reference"]
        for moves in ([], [True], [{"reference": ref}, {"reference": ref}], [{"reference": ref}] * 9, "bad"):
            self.expect(422, "POST", "/reservation-moves", {"moves": moves}, self.a, "shape", "validation_failed")
        self.expect(404, "POST", "/reservation-moves", {"moves": [{"reference": ref}]}, self.b, "owner", "not_found")
        self.expect(422, "POST", "/reservation-moves", {"moves": [{"reference": ref, "party_size": 0}, {"reference": "MISSING"}]}, self.a, "order", "validation_failed")
        self.assertEqual(one, self.expect(200, "GET", "/reservations/" + ref, token=self.a))

    def test_concurrent_identical_50_exactly_one_write(self):
        body = self.booking()
        results = self.concurrent(50, lambda _: self.request("POST", "/reservations", body, self.a, "race-identical"))
        self.assertEqual([status for status, _ in results].count(201), 1)
        self.assertEqual([status for status, _ in results].count(200), 49)
        original = next(body for status, body in results if status == 201)
        self.assertTrue(all(body == original for _, body in results))
        self.assertEqual(len(self.expect(200, "GET", "/reservations", token=self.a)["reservations"]), 1)

    def test_concurrent_competing_50_no_double_booking(self):
        results = self.concurrent(50, lambda i: self.request("POST", "/reservations", self.booking(), self.a, f"race-{i}"))
        self.assertEqual([status for status, _ in results].count(201), 1)
        self.assertEqual([status for status, _ in results].count(409), 49)
        self.assertTrue(all(body["error"]["code"] == "table_unavailable" for status, body in results if status == 409))

    def test_export_import_receipts_sessions_replacement_and_rejection(self):
        original = self.create()
        ref = original["reference"]
        moves = {"moves": [{"reference": ref, "table_id": "table-a"}]}
        batch = self.expect(201, "POST", "/reservation-moves", moves, self.a, "batch")
        exported = self.snapshot()
        self.assertEqual(exported["track"], "tablekeeper")
        self.assertEqual(exported["format_version"], 1)
        self.assertIsInstance(exported["state"], dict)
        self.assertNotIn(PASSWORD, json.dumps(exported), "plaintext synthetic password exported")
        self.expect(200, "POST", "/reservations/" + ref + "/cancel", {}, self.a)
        self.reset()
        destination_token = self.login()
        for _ in range(2):
            self.expect(204, "POST", "/_test/import", exported)
            self.expect(401, "GET", "/reservations", token=destination_token, code="unauthenticated")
            self.assertEqual(original, self.expect(200, "POST", "/reservations", self.booking(), self.a, "create"))
            self.assertEqual(batch, self.expect(200, "POST", "/reservation-moves", moves, self.a, "batch"))
            self.assertEqual(batch["reservations"][0], self.expect(200, "GET", "/reservations/" + ref, token=self.a))
            self.login()
        before = self.snapshot()
        for invalid in ({}, dict(exported, track="different"), dict(exported, format_version=99), dict(exported, state={})):
            self.expect(422, "POST", "/_test/import", invalid, code="validation_failed")
            self.assertTrue(before == self.snapshot(), "invalid import changed destination state")
        self.expect(400, "POST", "/_test/import", raw=b"{", code="malformed_request")
        self.assertTrue(before == self.snapshot(), "malformed import changed destination state")


if __name__ == "__main__":
    unittest.main(verbosity=2)
