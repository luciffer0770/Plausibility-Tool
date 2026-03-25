"""Tests for profile JSON round-trip."""

from __future__ import annotations

import unittest

from core.models import LimitDefinition, ParameterType
from core.profile_manager import export_profile_json, import_profile_json


class TestProfileManager(unittest.TestCase):
    def test_roundtrip(self) -> None:
        defs = [
            LimitDefinition(
                parameter_name="T0",
                parameter_type=ParameterType.TEMPERATURE,
                description="Test",
                unit="C",
                lower_limit=0,
                upper_limit=100,
                is_required=True,
            )
        ]
        s = export_profile_json(defs)
        out = import_profile_json(s)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].parameter_name, "T0")
        self.assertEqual(out[0].lower_limit, 0.0)
        self.assertTrue(out[0].is_required)
        self.assertTrue(out[0].is_enabled)


if __name__ == "__main__":
    unittest.main()
