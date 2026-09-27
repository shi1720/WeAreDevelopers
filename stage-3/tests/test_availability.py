"""Coverage: §1 half-open occupancy; §8 capacity/order/empty days; §9 folds.

Confirmed-only filtering and snapshot purity support caller-owned atomic reads.
"""

import copy
import unittest
from datetime import datetime

from tablekeeper.availability import get_availability, overlaps
from tablekeeper.validation import APIError


class AvailabilityTests(unittest.TestCase):
    def setUp(self):
        self.restaurant = {"id": "r", "timezone": "Europe/Berlin", "slot_minutes": 30,
                           "reservation_duration_minutes": 90,
                           "opening_hours": [{"weekday": "thu", "opens": "18:00", "closes": "22:00"}],
                           "tables": [{"id": "z", "capacity": 4}, {"id": "a", "capacity": 2}]}
        self.booking = {"restaurant_id": "r", "table_id": "z", "status": "confirmed",
                        "starts_at": "2026-09-24T19:00:00+02:00", "ends_at": "2026-09-24T20:30:00+02:00"}

    def test_half_open_overlap_and_fixture_order(self):
        response = get_availability(self.restaurant, [self.booking], "2026-09-24", 2)
        slots = {slot["starts_at_local"][-5:]: slot["available_table_ids"] for slot in response["slots"]}
        self.assertEqual(["a"], slots["18:00"])
        self.assertEqual(["a"], slots["20:00"])
        self.assertEqual(["z", "a"], slots["20:30"])
        self.assertEqual(6, len(slots))
        start, end = map(datetime.fromisoformat, ("2026-09-24T17:30:00+02:00", "2026-09-24T19:00:00+02:00"))
        self.assertFalse(overlaps(start, end, self.booking))

    def test_capacity_closed_empty_and_cancelled(self):
        slots = get_availability(self.restaurant, [], "2026-09-24", 9)["slots"]
        self.assertEqual(6, len(slots))
        self.assertTrue(all(slot["available_table_ids"] == [] for slot in slots))
        self.assertEqual([], get_availability(self.restaurant, [], "2026-09-25", 1)["slots"])
        cancelled = dict(self.booking, status="cancelled")
        other_restaurant = dict(self.booking, restaurant_id="other")
        response = get_availability(self.restaurant, [cancelled, other_restaurant], "2026-09-24", 4)
        self.assertTrue(all(slot["available_table_ids"] == ["z"] for slot in response["slots"]))

    def test_fold_overlap_compares_absolute_instants(self):
        booking = {"starts_at": "2026-10-25T02:45:00+02:00", "ends_at": "2026-10-25T02:15:00+01:00"}
        self.assertTrue(overlaps(datetime.fromisoformat("2026-10-25T02:00:00+01:00"),
                                 datetime.fromisoformat("2026-10-25T02:30:00+01:00"), booking))

    def test_inputs_not_mutated_and_result_not_aliased(self):
        bookings = [self.booking]
        before = copy.deepcopy((self.restaurant, bookings))
        result = get_availability(self.restaurant, bookings, "2026-09-24", 2)
        result["slots"][-1]["available_table_ids"].clear()
        self.assertEqual(before, (self.restaurant, bookings))

    def test_party_type_and_range(self):
        for party in (True, False, 0, -1, 2.0, "2", None):
            with self.subTest(party=party), self.assertRaises(APIError) as error:
                get_availability(self.restaurant, [], "2026-09-24", party)
            self.assertEqual("validation_failed", error.exception.code)

    def test_pairs_in_declared_order_and_occupy_both_members(self):
        self.restaurant['tables'].append({'id': 'b', 'capacity': 3})
        self.restaurant['combinable'] = [['a', 'z'], ['z', 'b']]
        result = get_availability(self.restaurant, [], '2026-09-24', 2)['slots'][0]
        self.assertEqual([['z'], ['a'], ['b'], ['a', 'z'], ['z', 'b']],
                         [option['table_ids'] for option in result['available_options']])
        self.assertEqual([4, 2, 3, 6, 7], [option['capacity'] for option in result['available_options']])
        booked = dict(self.booking, table_ids=['a', 'z'])
        booked.pop('table_id')
        result = get_availability(self.restaurant, [booked], '2026-09-24', 2)['slots'][0]
        self.assertEqual(['b'], result['available_table_ids'])
        self.assertEqual([{'table_ids': ['b'], 'capacity': 3}], result['available_options'])

    def test_pairs_capacity_is_sum_no_transitive_options(self):
        self.restaurant['tables'].append({'id': 'b', 'capacity': 3})
        self.restaurant['combinable'] = [['a', 'z'], ['z', 'b']]
        result = get_availability(self.restaurant, [], '2026-09-24', 5)['slots'][0]
        self.assertEqual([], result['available_table_ids'])
        self.assertEqual([['a', 'z'], ['z', 'b']], [o['table_ids'] for o in result['available_options']])
        self.assertEqual([], get_availability(self.restaurant, [], '2026-09-24', 8)['slots'][0]['available_options'])


if __name__ == "__main__":
    unittest.main()
