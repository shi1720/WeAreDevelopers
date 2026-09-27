"""Additional HTTP boundaries selected during independent source review."""
import unittest
from independent_combinations import IndependentCombinations


class IndependentReview(IndependentCombinations):
    def test_selection_member_types_and_opaque_id_boundary(self):
        before = self.snapshot()
        for value in (None, True, 2, {}, [None], [True], [2], [{}]):
            body = dict(self.pair_body(), table_ids=value)
            self.expect(400, "POST", "/reservations", body, self.a, "review", "malformed_request")
            self.assertTrue(before == self.snapshot())
        self.expect(422, "POST", "/reservations", dict(self.pair_body(), table_ids=["x" * 65]),
                    self.a, "review", "validation_failed")
        self.pair(key="review")

    def test_pair_replay_body_order_is_distinct_from_table_set_order(self):
        original = self.pair()
        changed_json = self.pair_body(pair=["table-a", "table-z"])
        self.expect(409, "POST", "/reservations", changed_json, self.a, "pair", "idempotency_key_reuse")
        self.assertEqual(original, self.expect(200, "POST", "/reservations", self.pair_body(), self.a, "pair"))


def load_tests(loader, tests, pattern):
    return unittest.TestSuite(IndependentReview(name) for name in IndependentReview.__dict__ if name.startswith("test_"))
