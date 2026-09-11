import unittest

from hold_time import (
    HoldTimeError, duration_hours, evaluate, format_datetime, format_hours,
    parse_ts, step_status,
)


def granulation_steps(ends=True):
    steps = [
        {"name": "Wet granulation", "start": "2026-09-01 08:00",
         "end": "2026-09-01 11:00", "limit_h": 4.0},
        {"name": "Drying", "start": "2026-09-01 11:00",
         "end": "2026-09-01 15:00", "limit_h": 6.0},
        {"name": "Milling", "start": "2026-09-01 15:00",
         "end": "2026-09-01 16:00", "limit_h": 3.0},
    ]
    if not ends:
        steps[-1]["end"] = None
    return steps


class TimeTests(unittest.TestCase):
    def test_parse_iso_and_z(self):
        self.assertEqual(parse_ts("2026-09-01 08:00").hour, 8)
        self.assertEqual(parse_ts("2026-09-01T08:00:00Z").hour, 8)

    def test_duration_hours(self):
        self.assertEqual(duration_hours(parse_ts("2026-09-01 08:00"),
                                        parse_ts("2026-09-01 11:30")), 3.5)

    def test_end_before_start_raises(self):
        with self.assertRaises(HoldTimeError):
            duration_hours(parse_ts("2026-09-01 12:00"),
                           parse_ts("2026-09-01 09:00"))


class StatusTests(unittest.TestCase):
    def test_step_status_thresholds(self):
        self.assertEqual(step_status(1.0, 4.0), "On time")
        self.assertEqual(step_status(3.2, 4.0), "Near")
        self.assertEqual(step_status(4.0, 4.0), "Over")
        self.assertEqual(step_status(5.0, 4.0), "Over")

    def test_step_status_no_limit_tracks(self):
        self.assertEqual(step_status(5.0, None), "Track")


class EvaluateTests(unittest.TestCase):
    def test_cumulative_rolls_up(self):
        res = evaluate(granulation_steps(), global_limit_h=24.0,
                       now="2026-09-01 16:00")
        self.assertAlmostEqual(res["cumulative_total_h"], 8.0, places=2)
        self.assertEqual(res["steps"][-1]["cumulative_h"], res["cumulative_total_h"])

    def test_cumulative_status_bands(self):
        steps = granulation_steps(ends=False)  # last step runs until "now"
        self.assertEqual(evaluate(steps, 24.0,
                                  now="2026-09-01 16:00")["cumulative_status"],
                         "On time")
        self.assertEqual(evaluate(steps, 24.0,
                                  now="2026-09-02 04:00")["cumulative_status"],
                         "Near")
        self.assertEqual(evaluate(steps, 24.0,
                                  now="2026-09-02 12:00")["cumulative_status"],
                         "Over")

    def test_remaining_and_over(self):
        res = evaluate(granulation_steps(), 8.0, now="2026-09-01 16:00")
        self.assertEqual(res["remaining_h"], 0.0)
        self.assertAlmostEqual(res["over_by_h"], 0.0, places=2)
        res2 = evaluate(granulation_steps(), 6.0, now="2026-09-01 16:00")
        self.assertAlmostEqual(res2["over_by_h"], 2.0, places=2)

    def test_ongoing_step_uses_now(self):
        steps = granulation_steps(ends=False)
        res = evaluate(steps, 24.0, now="2026-09-01 18:00")
        self.assertAlmostEqual(res["cumulative_total_h"], 10.0, places=2)

    def test_projected_total_on_ongoing_step(self):
        steps = granulation_steps(ends=False)
        res = evaluate(steps, 24.0, now="2026-09-01 16:30")
        self.assertAlmostEqual(res["projected_total_h"], 10.0, places=2)

    def test_excursion_flag_any_over_step(self):
        steps = granulation_steps()
        steps[0]["end"] = "2026-09-01 14:00"  # 6 h vs 4 h limit
        res = evaluate(steps, 24.0, now="2026-09-01 16:00")
        self.assertTrue(res["excursion"])
        self.assertEqual(res["steps"][0]["status"], "Over")

    def test_no_steps_raises(self):
        with self.assertRaises(HoldTimeError):
            evaluate([], 24.0)

    def test_bad_global_limit(self):
        with self.assertRaises(HoldTimeError):
            evaluate(granulation_steps(), 0.0)


class FormatTests(unittest.TestCase):
    def test_format_hours_rounding(self):
        self.assertEqual(format_hours(0), "00:00")
        self.assertEqual(format_hours(8.0), "08:00")
        self.assertEqual(format_hours(8.5), "08:30")
        self.assertEqual(format_hours(1.75), "01:45")

    def test_format_hours_rounds_minutes_to_60(self):
        self.assertEqual(format_hours(1.999), "02:00")

    def test_format_hours_passes_24(self):
        self.assertEqual(format_hours(26.75), "26:45")

    def test_format_hours_none(self):
        self.assertIsNone(format_hours(None))

    def test_format_datetime_24h_clock(self):
        self.assertEqual(format_datetime(parse_ts("2026-09-01 06:05")),
                         "2026-09-01 06:05")
        self.assertEqual(format_datetime(parse_ts("2026-09-01 18:40")),
                         "2026-09-01 18:40")

    def test_evaluate_reports_hhmm_fields(self):
        res = evaluate(granulation_steps(), 24.0, now="2026-09-01 16:00")
        self.assertEqual(res["cumulative_total_hhmm"], "08:00")
        self.assertEqual(res["global_limit_hhmm"], "24:00")
        self.assertEqual(res["remaining_hhmm"], "16:00")
        self.assertEqual(res["steps"][0]["duration_hhmm"], "03:00")
        self.assertEqual(res["steps"][0]["cumulative_hhmm"], "03:00")
        self.assertEqual(res["steps"][-1]["start_time"], "2026-09-01 15:00")

    def test_evaluate_projected_hhmm(self):
        steps = granulation_steps(ends=False)
        res = evaluate(steps, 24.0, now="2026-09-01 16:30")
        self.assertEqual(res["projected_total_hhmm"], "10:00")


if __name__ == "__main__":
    unittest.main()