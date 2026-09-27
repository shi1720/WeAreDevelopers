"""Coverage: §5 types/formats; §8 grid/hours; §9 gaps/folds/absolute time.

Past/leap dates and non-hour DST transitions guard against fixture-specific logic.
HTTP atomicity, authentication and receipt behavior are tested by other seats.
"""

import unittest
from datetime import timezone

from tablekeeper.temporal import booking_interval, iter_slots, resolve_local
from tablekeeper.validation import APIError


def restaurant(zone="Europe/Berlin", opens="00:00", closes="06:00", duration=90, slot=30):
    return {"id": "r", "timezone": zone, "slot_minutes": slot,
            "reservation_duration_minutes": duration,
            "opening_hours": [{"weekday": d, "opens": opens, "closes": closes}
                              for d in ("mon", "tue", "wed", "thu", "fri", "sat", "sun")],
            "tables": [{"id": "small", "capacity": 2}, {"id": "large", "capacity": 6}]}


class TemporalTests(unittest.TestCase):
    def error(self, code, call, *args):
        with self.assertRaises(APIError) as result:
            call(*args)
        self.assertEqual(code, result.exception.code)

    def test_gaps_and_first_folds(self):
        for zone, gap, fold, offset in [
            ("Europe/Berlin", "2026-03-29T02:30", "2026-10-25T02:30", 7200),
            ("America/New_York", "2026-03-08T02:30", "2026-11-01T01:30", -14400),
            ("Australia/Lord_Howe", "2026-10-04T02:15", "2026-04-05T01:45", 39600),
        ]:
            with self.subTest(zone=zone):
                self.error("invalid_local_time", resolve_local, zone, gap)
                self.assertEqual(offset, resolve_local(zone, fold).utcoffset().total_seconds())

    def test_absolute_durations_both_transitions(self):
        for zone, local, expected in [
            ("Europe/Berlin", "2026-10-25T02:30", "2026-10-25T03:00:00+01:00"),
            ("America/New_York", "2026-11-01T01:30", "2026-11-01T02:00:00-05:00"),
            ("Europe/Berlin", "2026-03-29T01:30", "2026-03-29T04:00:00+02:00"),
            ("America/New_York", "2026-03-08T01:30", "2026-03-08T04:00:00-04:00"),
        ]:
            with self.subTest(local=local, zone=zone):
                start, end = booking_interval(restaurant(zone), local)
                self.assertEqual(expected, end.isoformat())
                self.assertEqual(5400, (end.astimezone(timezone.utc) - start.astimezone(timezone.utc)).total_seconds())

    def test_gap_slots_omitted_fold_slots_once(self):
        spring = list(iter_slots(restaurant(), "2026-03-29"))
        self.assertFalse(any(start.hour == 2 for start, _ in spring))
        fall = list(iter_slots(restaurant(), "2026-10-25"))
        self.assertEqual(2, sum(start.hour == 2 for start, _ in fall))
        self.assertEqual(len(fall), len({start.strftime("%H:%M") for start, _ in fall}))

    def test_grid_anchored_at_opening_and_exact_close(self):
        config = restaurant(opens="18:10", closes="23:10")
        self.assertEqual("23:10", booking_interval(config, "2024-02-29T21:40")[1].strftime("%H:%M"))
        self.error("not_on_slot_grid", booking_interval, config, "2024-02-29T19:00")
        self.error("outside_opening_hours", booking_interval, config, "2024-02-29T22:10")
        self.error("outside_opening_hours", booking_interval, config, "2024-02-29T18:00")
        self.assertEqual("18:10", next(iter_slots(config, "2024-02-29"))[0].strftime("%H:%M"))

    def test_transition_closing_uses_real_duration(self):
        spring = restaurant(closes="03:30")
        self.error("outside_opening_hours", booking_interval, spring, "2026-03-29T01:30")
        self.assertEqual("03:30", booking_interval(spring, "2026-03-29T01:00")[1].strftime("%H:%M"))
        fall = restaurant(closes="03:00")
        self.assertEqual("03:00", booking_interval(fall, "2026-10-25T02:30")[1].strftime("%H:%M"))
        self.assertIn("02:30", [start.strftime("%H:%M") for start, _ in iter_slots(fall, "2026-10-25")])

    def test_invalid_formats_and_types(self):
        for value in ("2026-01-01T12:00Z", "2026-01-01T12:00:00", "2026-01-01 12:00",
                      "2026-02-29T12:00", "2026-01-01T24:00", "２０２６-01-01T12:00"):
            self.error("validation_failed", resolve_local, "UTC", value)
        for value in (None, 3, True, [], {}):
            self.error("malformed_request", resolve_local, "UTC", value)
        for value in ("2026-2-01", "2026-02-29", "2026-01-01T00:00"):
            self.error("validation_failed", lambda: list(iter_slots(restaurant(), value)))

    def test_closed_day_and_arbitrary_past_date(self):
        config = restaurant()
        config["opening_hours"] = []
        self.assertEqual([], list(iter_slots(config, "2037-01-03")))
        self.error("outside_opening_hours", booking_interval, config, "2037-01-03T01:00")
        self.assertTrue(list(iter_slots(restaurant("Asia/Kolkata"), "1998-06-09")))


if __name__ == "__main__":
    unittest.main()
