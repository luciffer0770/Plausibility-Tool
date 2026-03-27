"""Tests for PUMA columns without limit definitions (WARNING rows)."""

from __future__ import annotations

import unittest

from core.models import LimitDefinition, ParameterType
from core.plausibility_engine import column_covered_by_enabled_limit, status_sort_rank_v3


class TestUnconfiguredColumns(unittest.TestCase):
    def test_column_covered_by_enabled_limit(self) -> None:
        defs = [
            LimitDefinition(
                parameter_name="CO",
                parameter_type=ParameterType.EMISSION,
                description="",
                unit="",
                is_enabled=True,
            )
        ]
        cols = ["CO", "N", "MD"]
        self.assertTrue(column_covered_by_enabled_limit("CO", defs, cols))
        self.assertFalse(column_covered_by_enabled_limit("N", defs, cols))

    def test_warning_sorts_last(self) -> None:
        self.assertLess(status_sort_rank_v3("HIGH"), status_sort_rank_v3("WARNING"))
        self.assertLess(status_sort_rank_v3("OK"), status_sort_rank_v3("WARNING"))


if __name__ == "__main__":
    unittest.main()
