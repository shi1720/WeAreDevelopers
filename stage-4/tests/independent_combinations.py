"""Stage-2 HTTP properties derived before implementation review."""
import copy
import unittest
from independent_contract import IndependentContract, fixture


def combination_fixture():
    data = fixture()
    data["restaurants"][0]["combinable"] = [["table-a", "table-z"], ["table-m", "table-a"]]
    return data


class IndependentCombinations(IndependentContract):
    def setUp(self):
        self.reset(combination_fixture())
        self.a = self.login()
        self.b = self.login("bea@example.test")

    def pair_body(self, pair=None, party=5, local="2032-06-17T18:00"):
        body = self.booking(party=party, local=local)
        del body["table_id"]
        body["table_ids"] = pair if pair is not None else ["table-z", "table-a"]
        return body

    def pair(self, key="pair", **kwargs):
        return self.expect(201, "POST", "/reservations", self.pair_body(**kwargs), self.a, key)

    def test_option_order_sums_no_transitivity_and_response_shapes(self):
        slot = next(s for s in self.availability(party=2)["slots"] if s["starts_at_local"].endswith("18:00"))
        self.assertEqual(slot["available_table_ids"], ["table-z", "table-a", "table-m"])
        self.assertEqual(slot["available_options"], [
            {"table_ids": ["table-z"], "capacity": 2},
            {"table_ids": ["table-a"], "capacity": 4},
            {"table_ids": ["table-m"], "capacity": 8},
            {"table_ids": ["table-a", "table-z"], "capacity": 6},
            {"table_ids": ["table-m", "table-a"], "capacity": 12},
        ])
        slot = next(s for s in self.availability(party=6)["slots"] if s["starts_at_local"].endswith("18:00"))
        self.assertEqual(slot["available_table_ids"], ["table-m"])
        self.assertEqual([x["table_ids"] for x in slot["available_options"]], [["table-m"], ["table-a", "table-z"], ["table-m", "table-a"]])
        self.expect(422, "POST", "/reservations", self.pair_body(pair=["table-z", "table-m"]), self.a, "transitive", "combination_not_allowed")
        single = self.create(table="table-m")
        self.assertEqual(single["table_ids"], ["table-m"])
        combined = self.pair()
        self.assertEqual(combined["table_ids"], ["table-a", "table-z"])
        self.assertNotIn("table_id", combined)

    def test_selection_errors_rollback_and_retry_reuse(self):
        cases = [([], "validation_failed"), (["table-z", "table-z"], "validation_failed"),
                 (["table-z", "table-a", "table-m"], "combination_not_allowed")]
        before = self.snapshot()
        for ids, error in cases:
            self.expect(422, "POST", "/reservations", self.pair_body(pair=ids), self.a, "reusable", error)
            self.assertTrue(before == self.snapshot())
        both = self.pair_body(); both["table_id"] = "table-z"
        self.expect(422, "POST", "/reservations", both, self.a, "reusable", "validation_failed")
        self.expect(422, "POST", "/reservations", self.pair_body(party=7), self.a, "reusable", "party_exceeds_capacity")
        self.expect(400, "POST", "/reservations", dict(self.pair_body(), table_ids="table-a"), self.a, "reusable", "malformed_request")
        self.pair(key="reusable", party=6)

    def test_both_members_occupied_then_freed_and_original_receipt(self):
        original = self.pair()
        for table in ("table-a", "table-z"):
            self.expect(409, "POST", "/reservations", self.booking(table=table), self.b, table, "table_unavailable")
        slot = next(s for s in self.availability()["slots"] if s["starts_at_local"].endswith("18:00"))
        self.assertEqual(slot["available_table_ids"], ["table-m"])
        self.assertEqual([x["table_ids"] for x in slot["available_options"]], [["table-m"]])
        self.expect(200, "POST", "/reservations/" + original["reference"] + "/cancel", {}, self.a)
        for table in ("table-a", "table-z"):
            self.expect(201, "POST", "/reservations", self.booking(table=table), self.b, table)
        self.assertEqual(original, self.expect(200, "POST", "/reservations", self.pair_body(), self.a, "pair"))

    def test_pair_amendment_identity_noop_and_failed_transition(self):
        original = self.pair(party=2)
        path = "/reservations/" + original["reference"]
        reversed_noop = self.expect(200, "PATCH", path, {"table_ids": ["table-z", "table-a"]}, self.a)
        self.assertEqual(reversed_noop, original)
        single = self.expect(200, "PATCH", path, {"table_id": "table-z"}, self.a)
        self.assertEqual(single["table_ids"], ["table-z"])
        self.assertEqual(single["table_id"], "table-z")
        self.create(key="fixed", table="table-a")
        self.expect(409, "PATCH", path, {"table_ids": ["table-a", "table-z"]}, self.a, code="table_unavailable")
        self.assertEqual(single, self.expect(200, "GET", path, token=self.a))
        for field in ("reference", "reservation_id", "created_at"):
            self.assertEqual(original[field], single[field])

    def test_atomic_pair_single_swap_and_intra_batch_overlap(self):
        first = self.pair(party=2)
        second = self.create(key="single", table="table-m")
        moves = {"moves": [{"reference": first["reference"], "table_ids": ["table-m"]},
                            {"reference": second["reference"], "table_ids": ["table-z", "table-a"]}]}
        receipt = self.expect(201, "POST", "/reservation-moves", moves, self.a, "swap")
        self.assertEqual([r["table_ids"] for r in receipt["reservations"]], [["table-m"], ["table-a", "table-z"]])
        before = self.snapshot()
        invalid = {"moves": [{"reference": first["reference"], "table_ids": ["table-m", "table-a"]},
                              {"reference": second["reference"], "table_ids": ["table-a", "table-z"]}]}
        self.expect(409, "POST", "/reservation-moves", invalid, self.a, "bad", "table_unavailable")
        self.assertTrue(before == self.snapshot())
        self.expect(204, "POST", "/_test/import", before)
        self.assertEqual(receipt, self.expect(200, "POST", "/reservation-moves", moves, self.a, "swap"))

    def test_fifty_competing_overlapping_pairs_have_one_winner(self):
        def attempt(index):
            ids = ["table-a", "table-z"] if index % 2 else ["table-m", "table-a"]
            return self.request("POST", "/reservations", self.pair_body(pair=ids), self.a, "compete-" + str(index))
        results = self.concurrent(50, attempt)
        self.assertEqual(sum(status == 201 for status, _ in results), 1)
        self.assertEqual(sum(status == 409 for status, _ in results), 49)
        self.assertTrue(all(body["error"]["code"] == "table_unavailable" for status, body in results if status == 409))

    def test_seeded_cancelled_pair_occupancy_and_import(self):
        data = combination_fixture()
        data["reservations"] = [dict(self.pair_body(), id="seed-pair", reference="PAIR001", user_id="user-a", status="cancelled")]
        self.reset(data); self.a = self.login()
        seeded = self.expect(200, "GET", "/reservations/PAIR001", token=self.a)
        self.assertEqual(seeded["status"], "cancelled")
        self.assertEqual(seeded["table_ids"], ["table-a", "table-z"])
        self.pair()
        exported = self.snapshot()
        self.reset()
        self.expect(204, "POST", "/_test/import", exported)
        self.assertEqual(seeded, self.expect(200, "GET", "/reservations/PAIR001", token=self.a))


def load_tests(loader, tests, pattern):
    return unittest.TestSuite(IndependentCombinations(name) for name in IndependentCombinations.__dict__
                              if name.startswith("test_"))
