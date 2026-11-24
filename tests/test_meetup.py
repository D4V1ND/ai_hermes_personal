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


class TimelineTest(StoreTest):
    def setUp(self) -> None:
        super().setUp()
        # Saved out of order on purpose: the Timeline sorts by time.
        meetup.save_note(self.db, "text", "MCP for tool calling", ["MCP"], datetime(2026, 11, 12, 19, 5))
        meetup.save_note(
            self.db, "text", "LangGraph", ["LangGraph"], datetime(2026, 11, 12, 18, 42),
            descriptions={"LangGraph": "A library."},
        )
        meetup.save_note(self.db, "voice", "Lang Graph", ["LangGraph"], datetime(2026, 12, 3, 19, 20))

    def test_day_returns_notes_in_saved_order_with_terms(self) -> None:
        timeline = meetup.timeline(self.db, "2026-11-12")

        self.assertEqual(timeline["day"], "2026-11-12")
        self.assertEqual([(note["time"], note["text"]) for note in timeline["notes"]],
                         [("18:42", "LangGraph"), ("19:05", "MCP for tool calling")])
        self.assertEqual(timeline["notes"][0]["terms"],
                         [{"name": "LangGraph", "description": "A library.", "other_days": ["2026-12-03"]}])
        self.assertEqual(timeline["notes"][1]["terms"],
                         [{"name": "MCP", "description": None, "other_days": []}])

    def test_day_without_notes_is_empty(self) -> None:
        self.assertEqual(meetup.timeline(self.db, "2026-01-01"), {"day": "2026-01-01", "notes": []})

    def test_recent_lists_newest_first(self) -> None:
        recent = meetup.recent_notes(self.db, 2)
        self.assertEqual([note["text"] for note in recent], ["Lang Graph", "MCP for tool calling"])
        self.assertEqual(recent[0]["terms"], ["LangGraph"])
        self.assertEqual(recent[0]["day"], "2026-12-03")


class EditTest(StoreTest):
    def term_names(self) -> list[str]:
        return [term["name"] for term in meetup.list_terms(self.db)]

    def note_texts(self) -> list[str]:
        return [text for (text,) in self.db.execute("SELECT text FROM notes ORDER BY id")]

    def test_correcting_a_note_replaces_text_and_terms(self) -> None:
        meetup.save_note(self.db, "text", "LangGraph", ["LangGraph"], datetime(2026, 11, 12, 18, 42))
        wrong = meetup.save_note(self.db, "voice", "Land Graph", ["Land Graph"], datetime(2026, 12, 3, 19, 20))

        result = meetup.correct_note(self.db, wrong["note_id"], "LangGraph", ["LangGraph"])

        self.assertEqual((result["old_text"], result["new_text"]), ("Land Graph", "LangGraph"))
        self.assertEqual(result["terms"][0]["other_days"], ["2026-11-12"])
        self.assertEqual(result["removed_terms"], ["Land Graph"])
        self.assertEqual(self.note_texts(), ["LangGraph", "LangGraph"])  # the old text is gone
        self.assertEqual(self.term_names(), ["LangGraph"])

    def test_renaming_a_term_rewrites_its_notes_and_clears_the_description(self) -> None:
        meetup.save_note(self.db, "text", "tried Land Graph today", ["Land Graph"],
                         descriptions={"Land Graph": "Wrong."})

        result = meetup.rename_term(self.db, "Land Graph", "LangGraph")

        self.assertFalse(result["merged"])
        self.assertEqual(self.note_texts(), ["tried LangGraph today"])
        self.assertEqual(meetup.list_terms(self.db), [{"name": "LangGraph", "description": None}])

    def test_renaming_to_an_existing_name_leaves_one_term_with_both_notes(self) -> None:
        meetup.save_note(self.db, "text", "LangGraph", ["LangGraph"], datetime(2026, 11, 12, 18, 42))
        meetup.save_note(self.db, "voice", "Land Graph", ["Land Graph"], datetime(2026, 12, 3, 19, 20))

        result = meetup.rename_term(self.db, "Land Graph", "LangGraph")

        self.assertTrue(result["merged"])
        self.assertEqual(self.term_names(), ["LangGraph"])
        term_id = meetup.find_term(self.db, "LangGraph")[0]
        self.assertEqual(meetup.days_of_term(self.db, term_id), ["2026-11-12", "2026-12-03"])
        self.assertEqual(self.note_texts(), ["LangGraph", "LangGraph"])

    def test_merging_keeps_the_older_term_and_rewrites_notes(self) -> None:
        meetup.save_note(self.db, "text", "MCP", ["MCP"], datetime(2026, 11, 12, 19, 5))
        meetup.save_note(self.db, "text", "Model Context Protocol demo", ["Model Context Protocol"],
                         datetime(2026, 12, 3, 19, 20), descriptions={"Model Context Protocol": "A standard."})

        result = meetup.merge_terms(self.db, "Model Context Protocol", "MCP")

        self.assertEqual((result["kept"], result["dropped"]), ("MCP", "Model Context Protocol"))
        self.assertEqual(self.note_texts(), ["MCP", "MCP demo"])
        # The kept Term had no description, so it takes the dropped one's.
        self.assertEqual(meetup.list_terms(self.db), [{"name": "MCP", "description": "A standard."}])

    def test_merging_can_keep_the_name_i_ask_for(self) -> None:
        meetup.save_note(self.db, "text", "MCP", ["MCP"])
        meetup.save_note(self.db, "text", "Model Context Protocol", ["Model Context Protocol"])

        meetup.merge_terms(self.db, "MCP", "Model Context Protocol", keep="Model Context Protocol")

        self.assertEqual(self.term_names(), ["Model Context Protocol"])
        self.assertEqual(self.note_texts(), ["Model Context Protocol", "Model Context Protocol"])

    def test_replacing_a_name_leaves_longer_words_alone(self) -> None:
        meetup.save_note(self.db, "text", "Go is used at Google", ["Go"])
        meetup.rename_term(self.db, "Go", "Golang")
        self.assertEqual(self.note_texts(), ["Golang is used at Google"])

    def test_merging_a_term_with_itself_fails(self) -> None:
        meetup.save_note(self.db, "text", "MCP", ["MCP"])
        with self.assertRaises(ValueError):
            meetup.merge_terms(self.db, "MCP", "mcp")

    def test_deleting_the_only_note_of_a_term_removes_the_term(self) -> None:
        keep = meetup.save_note(self.db, "text", "LangGraph", ["LangGraph"])
        gone = meetup.save_note(self.db, "text", "MCP", ["MCP"])

        result = meetup.delete_note(self.db, gone["note_id"])

        self.assertEqual(result["removed_terms"], ["MCP"])
        self.assertEqual(self.term_names(), ["LangGraph"])
        self.assertEqual(self.note_texts(), ["LangGraph"])
        self.assertEqual(keep["note_id"], self.db.execute("SELECT id FROM notes").fetchone()[0])

    def test_editing_an_unknown_note_fails(self) -> None:
        with self.assertRaises(LookupError):
            meetup.delete_note(self.db, 99)
        with self.assertRaises(LookupError):
            meetup.correct_note(self.db, 99, "x")


if __name__ == "__main__":
    unittest.main()
