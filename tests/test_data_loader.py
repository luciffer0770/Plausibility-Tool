"""Tests for data_loader mapping and ZEIT preview."""

from __future__ import annotations

import unittest

import pandas as pd

from core.data_loader import (
    detect_column_mapping,
    preview_parameters_by_zeit,
    preview_parameters_detailed_table,
)


class TestDataLoader(unittest.TestCase):
    def test_detect_mapping(self) -> None:
        df = pd.DataFrame({"T0": [1], "P0": [2], "Timestamp": ["2024-01-01"]})
        m = detect_column_mapping(df)
        self.assertEqual(m["timestamp_col"], "Timestamp")
        names = {x["parameter"] for x in m["mappings"]}
        self.assertIn("T0", names)
        self.assertIn("P0", names)

    def test_min_suffix(self) -> None:
        df = pd.DataFrame({"T0_min": [10], "T0_max": [20]})
        m = detect_column_mapping(df)
        roles = sorted(x["value_role"] for x in m["mappings"] if x["parameter"] == "T0")
        self.assertEqual(roles, ["max", "min"])

    def test_preview_parameters_by_zeit_headers(self) -> None:
        df = pd.DataFrame(
            {
                "PRNAME": ["A", "A"],
                "ZEIT": ["12:17:28", "12:18:21"],
                "T0": [25.1, 25.3],
                "N": [2000, 2100],
            }
        )
        prev = preview_parameters_by_zeit(df, max_runs=2, max_parameters=10)
        self.assertIn("12:17:28", prev.columns)
        self.assertIn("12:18:21", prev.columns)
        self.assertIn("T0", prev.index)
        self.assertIn("N", prev.index)

    def test_preview_detailed_zeit_columns(self) -> None:
        df = pd.DataFrame(
            {
                "PRNAME": ["A", "A"],
                "ZEIT": ["12:17:28", "12:18:21"],
                "T0": [25.1, 25.3],
                "N": [2000, 2100],
            }
        )
        cols, rows = preview_parameters_detailed_table(df, max_runs=2, max_parameters=10)
        self.assertIn("Parameter", cols)
        self.assertIn("Unit", cols)
        self.assertTrue(any(c.startswith("ZEIT ") for c in cols))
        names = {r[0] for r in rows}
        self.assertIn("T0", names)
        self.assertIn("N", names)


if __name__ == "__main__":
    unittest.main()
