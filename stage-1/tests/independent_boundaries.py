"""Additional state-transition and concurrency cases derived from stage 1."""
import copy
from independent_contract import IndependentContract, fixture


# Reuse helpers without inheriting the contract test methods into discovery twice.
class IndependentBoundaries(IndependentContract):
    def test_seeded_identity_past_dates_reset_and_descending_listing(self):
        data = fixture()
        data["reservations"] = [dict(self.booking(local=local), id="opaque-" + str(i),
                                     reference="SEED0" + str(i), user_id="user-a")
                                for i, local in enumerate(("2001-01-01T18:00", "2032-06-17T18:00", "2020-05-05T18:00"))]
        for _ in range(2):
            self.reset(data); self.a = self.login()
            reservations = self.expect(200, "GET", "/reservations", token=self.a)["reservations"]
            self.assertEqual([r["reference"] for r in reservations], ["SEED01", "SEED02", "SEED00"])
            self.assertEqual([r["reservation_id"] for r in reservations], ["opaque-1", "opaque-2", "opaque-0"])
            self.assertTrue(all(r["status"] == "confirmed" for r in reservations))
        self.reset(); self.a = self.login()
        self.assertEqual(self.expect(200, "GET", "/reservations", token=self.a)["reservations"], [])

    def test_cross_restaurant_tables_and_collective_moves(self):
        data = fixture()
        second = copy.deepcopy(data["restaurants"][0]); second["id"] = "restaurant-two"
        for table in second["tables"]:
            table["id"] += "-other"
        data["restaurants"].append(second)
        self.reset(data); self.a = self.login()
        first = self.create()
        second_body = self.booking(table="table-z-other"); second_body["restaurant_id"] = "restaurant-two"
        other = self.expect(201, "POST", "/reservations", second_body, self.a, "second")
        for body in (self.booking(table="table-z-other"), dict(self.booking(), restaurant_id="missing"), self.booking(table="missing")):
            self.expect(404, "POST", "/reservations", body, self.a, "missing", "not_found")
        before = self.snapshot()
        self.expect(422, "POST", "/reservation-moves", {"moves": [{"reference": first["reference"]}, {"reference": other["reference"]}]}, self.a, "cross", "validation_failed")
        self.assertTrue(before == self.snapshot(), "cross-restaurant batch changed state")

    def test_eight_item_batch_and_unlisted_occupancy_rollback(self):
        bookings = [self.create(key=f"b-{i}", local=f"2032-06-{i+1:02d}T18:00") for i in range(8)]
        moves = {"moves": [{"reference": b["reference"], "table_id": "table-a"} for b in bookings]}
        changed = self.expect(201, "POST", "/reservation-moves", moves, self.a, "eight")["reservations"]
        self.assertEqual(len(changed), 8)
        self.assertTrue(all(b["table_id"] == "table-a" for b in changed))
        self.create(key="fixed", table="table-m", local="2032-06-08T18:00")
        before = self.snapshot()
        conflict = {"moves": [{"reference": b["reference"], "table_id": "table-m"} for b in bookings]}
        self.expect(409, "POST", "/reservation-moves", conflict, self.a, "rollback-eight", "table_unavailable")
        self.assertTrue(before == self.snapshot(), "late conflict partially moved eight-item batch")

    def test_concurrent_amendments_cannot_share_target(self):
        one = self.create(key="one")
        two = self.create(key="two", table="table-a")
        refs = [one["reference"], two["reference"]]
        results = self.concurrent(2, lambda i: self.request("PATCH", "/reservations/" + refs[i], {"table_id": "table-m"}, self.a))
        self.assertEqual(sorted(status for status, _ in results), [200, 409])
        self.assertEqual(next(body for status, body in results if status == 409)["error"]["code"], "table_unavailable")
        values = self.expect(200, "GET", "/reservations", token=self.a)["reservations"]
        self.assertEqual(sum(b["table_id"] == "table-m" for b in values), 1)

    def test_concurrent_signup_one_identity(self):
        body = {"email": "race@example.test", "password": "synthetic-signup-password", "display_name": "Race"}
        results = self.concurrent(10, lambda _: self.request("POST", "/auth/signup", body))
        statuses = [status for status, _ in results]
        self.assertEqual(statuses.count(201), 1)
        self.assertEqual(statuses.count(409), 9)
        self.assertTrue(all(body["error"]["code"] == "email_taken" for status, body in results if status == 409))

    def test_batch_input_error_precedes_occupancy_and_noop_occupies(self):
        one = self.create(key="one")
        two = self.create(key="two", table="table-a")
        collision = {"moves": [{"reference": one["reference"], "table_id": "table-a"}, {"reference": two["reference"]}]}
        before = self.snapshot()
        self.expect(409, "POST", "/reservation-moves", collision, self.a, "noop-collision", "table_unavailable")
        self.assertTrue(before == self.snapshot())
        collision["moves"][1]["party_size"] = 0
        self.expect(422, "POST", "/reservation-moves", collision, self.a, "noop-collision", "validation_failed")
        self.assertTrue(before == self.snapshot())


def load_tests(loader, tests, pattern):
    """Exclude inherited test methods; the sibling module runs those once."""
    import unittest
    return unittest.TestSuite(IndependentBoundaries(name) for name in IndependentBoundaries.__dict__
                              if name.startswith("test_"))
