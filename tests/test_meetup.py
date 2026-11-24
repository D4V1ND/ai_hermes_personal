"""Checks for meetup.py. One test per rule in docs/spec.md."""

import sys
import unittest
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skill" / "scripts"))

import meetup  # noqa: E402


class StoreTest(unittest.TestCase):
    def setUp(self) -> None:
        self.db = meetup.connect(":memory:")
        self.addCleanup(self.db.close)


class DayRuleTest(StoreTest):
    def test_note_after_midnight_belongs_to_the_evening_before(self) -> None:
        self.assertEqual(meetup.day_of(datetime(2026, 11, 13, 0, 30)), date(2026, 11, 12))
        self.assertEqual(meetup.day_of(datetime(2026, 11, 13, 3, 59)), date(2026, 11, 12))

    def test_day_starts_at_four(self) -> None:
        self.assertEqual(meetup.day_of(datetime(2026, 11, 13, 4, 0)), date(2026, 11, 13))

    def test_database_has_the_three_tables(self) -> None:
        rows = self.db.execute("SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name")
        self.assertEqual([name for (name,) in rows], ["note_terms", "notes", "terms"])


if __name__ == "__main__":
    unittest.main()
