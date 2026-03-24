"""Tests for data_loader mapping."""

from __future__ import annotations

import unittest

import pandas as pd

from core.data_loader import apply_mapping, detect_column_mapping


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


if __name__ == "__main__":
    unittest.main()
