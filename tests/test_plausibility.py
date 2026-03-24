"""Tests for plausibility_engine."""

from __future__ import annotations

import math
import unittest

from core.plausibility_engine import check_plausibility, deviation_percent, status_sort_rank


class TestPlausibility(unittest.TestCase):
    def test_no_data(self) -> None:
        self.assertEqual(check_plausibility(None, 0, 100, 10), "NO_DATA")
        self.assertEqual(check_plausibility(float("nan"), 0, 100, 10), "NO_DATA")

    def test_fail_outside(self) -> None:
        self.assertEqual(check_plausibility(-1, 0, 100, 10), "FAIL")
        self.assertEqual(check_plausibility(101, 0, 100, 10), "FAIL")

    def test_ok_center(self) -> None:
        self.assertEqual(check_plausibility(50, 0, 100, 10), "OK")

    def test_warning_near_limit(self) -> None:
        # range 100, warn_band 10 -> warn if value < 10 or value > 90
        self.assertEqual(check_plausibility(5, 0, 100, 10), "WARNING")
        self.assertEqual(check_plausibility(95, 0, 100, 10), "WARNING")

    def test_deviation(self) -> None:
        d = deviation_percent(50, 0, 100)
        self.assertIsNotNone(d)

    def test_sort_rank(self) -> None:
        self.assertLess(status_sort_rank("FAIL"), status_sort_rank("WARNING"))


if __name__ == "__main__":
    unittest.main()
