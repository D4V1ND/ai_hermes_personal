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


class SaveTest(StoreTest):
    def test_same_term_on_two_days_is_one_term(self) -> None:
        first = meetup.save_note(self.db, "text", "LangGraph", ["LangGraph"], datetime(2026, 11, 12, 18, 42))
        second = meetup.save_note(self.db, "voice", "Lang Graph", ["LangGraph"], datetime(2026, 12, 3, 19, 20))

        self.assertEqual([term["name"] for term in meetup.list_terms(self.db)], ["LangGraph"])
        term_id = self.db.execute("SELECT id FROM terms").fetchone()[0]
        self.assertEqual(meetup.days_of_term(self.db, term_id), ["2026-11-12", "2026-12-03"])
        self.assertTrue(first["terms"][0]["new"])
        self.assertFalse(second["terms"][0]["new"])
        self.assertEqual(second["terms"][0]["other_days"], ["2026-11-12"])

    def test_term_names_ignore_upper_and_lower_case(self) -> None:
        meetup.save_note(self.db, "text", "LangGraph", ["LangGraph"])
        meetup.save_note(self.db, "text", "langgraph again", ["langgraph"])
        self.assertEqual([term["name"] for term in meetup.list_terms(self.db)], ["LangGraph"])

    def test_note_without_term_is_still_saved(self) -> None:
        saved = meetup.save_note(self.db, "text", "nice venue", [], datetime(2026, 11, 12, 20, 0))
        self.assertEqual(saved["terms"], [])
        self.assertEqual(self.db.execute("SELECT text, day FROM notes").fetchall(), [("nice venue", "2026-11-12")])

    def test_description_can_come_with_the_note_or_later(self) -> None:
        saved = meetup.save_note(self.db, "text", "MCP", ["MCP", "LangGraph"], descriptions={"MCP": "A standard."})
        self.assertEqual(saved["terms"][0]["description"], "A standard.")
        self.assertIsNone(saved["terms"][1]["description"])

        meetup.describe_term(self.db, "langgraph", "A library.")
        self.assertEqual(
            meetup.list_terms(self.db),
            [{"name": "LangGraph", "description": "A library."}, {"name": "MCP", "description": "A standard."}],
        )

    def test_describing_an_unknown_term_fails(self) -> None:
        with self.assertRaises(LookupError):
            meetup.describe_term(self.db, "Nope", "x")


if __name__ == "__main__":
    unittest.main()
