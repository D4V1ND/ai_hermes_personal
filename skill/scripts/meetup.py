"""Meetup Intelligence: the part that must be exact.

The database, the Day rule, the edit operations and the command line.
Hermes runs this script and reads its JSON output. It makes no network
calls and uses no model. Words like Note, Term and Day are defined in
CONTEXT.md.
"""

from __future__ import annotations

import re
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterable

SCHEMA = """
CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY,
    saved_at TEXT NOT NULL,
    day TEXT NOT NULL,
    kind TEXT NOT NULL CHECK (kind IN ('text', 'voice', 'link')),
    text TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS terms (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE COLLATE NOCASE,
    description TEXT
);
CREATE TABLE IF NOT EXISTS note_terms (
    note_id INTEGER NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
    term_id INTEGER NOT NULL REFERENCES terms(id) ON DELETE CASCADE,
    PRIMARY KEY (note_id, term_id)
);
"""


def connect(path: str | Path) -> sqlite3.Connection:
    """Open the database and create the tables if they are missing."""
    db = sqlite3.connect(path)
    db.execute("PRAGMA foreign_keys = ON")
    db.executescript(SCHEMA)
    return db


def day_of(saved_at: datetime) -> date:
    """The Day a Note belongs to. Days run from 04:00 to 04:00."""
    return (saved_at - timedelta(hours=4)).date()


def days_of_term(db: sqlite3.Connection, term_id: int) -> list[str]:
    """Every Day a Term came up on, oldest first."""
    rows = db.execute(
        "SELECT DISTINCT n.day FROM notes n "
        "JOIN note_terms nt ON nt.note_id = n.id "
        "WHERE nt.term_id = ? ORDER BY n.day",
        (term_id,),
    )
    return [day for (day,) in rows]


def list_terms(db: sqlite3.Connection) -> list[dict]:
    rows = db.execute("SELECT name, description FROM terms ORDER BY name")
    return [{"name": name, "description": description} for name, description in rows]


def find_term(db: sqlite3.Connection, name: str) -> tuple[int, str]:
    """A Term's id and stored name, looked up without regard to case."""
    row = db.execute("SELECT id, name FROM terms WHERE name = ?", (name.strip(),)).fetchone()
    if row is None:
        raise LookupError(f"No Term named {name!r}.")
    return row


def describe_term(db: sqlite3.Connection, name: str, description: str) -> dict:
    term_id, name = find_term(db, name)
    db.execute("UPDATE terms SET description = ? WHERE id = ?", (description, term_id))
    return {"name": name, "description": description}


def link_terms(db: sqlite3.Connection, note_id: int, names: Iterable[str]) -> list[tuple[int, bool]]:
    """Link a Note to its Terms, creating the ones that do not exist yet.

    Returns (term id, is new) for each name.
    """
    linked = []
    for name in names:
        name = name.strip()
        if not name:
            raise ValueError("A Term needs a name.")
        row = db.execute("SELECT id FROM terms WHERE name = ?", (name,)).fetchone()
        is_new = row is None
        term_id = db.execute("INSERT INTO terms (name) VALUES (?)", (name,)).lastrowid if is_new else row[0]
        db.execute("INSERT OR IGNORE INTO note_terms (note_id, term_id) VALUES (?, ?)", (note_id, term_id))
        linked.append((term_id, is_new))
    return linked


def term_view(db: sqlite3.Connection, term_id: int, day: str) -> dict:
    """A Term as shown next to a Note: name, description, and the other Days it came up on."""
    name, description = db.execute("SELECT name, description FROM terms WHERE id = ?", (term_id,)).fetchone()
    other_days = [other for other in days_of_term(db, term_id) if other != day]
    return {"name": name, "description": description, "other_days": other_days}


def save_note(
    db: sqlite3.Connection,
    kind: str,
    text: str,
    term_names: Iterable[str] = (),
    saved_at: datetime | None = None,
    descriptions: dict[str, str] | None = None,
) -> dict:
    """Save a Note under its Day and link its Terms."""
    saved_at = saved_at or datetime.now()
    day = day_of(saved_at).isoformat()
    note_id = db.execute(
        "INSERT INTO notes (saved_at, day, kind, text) VALUES (?, ?, ?, ?)",
        (saved_at.isoformat(timespec="seconds"), day, kind, text),
    ).lastrowid
    linked = link_terms(db, note_id, term_names)
    for name, description in (descriptions or {}).items():
        describe_term(db, name, description)
    terms = [{**term_view(db, term_id, day), "new": is_new} for term_id, is_new in linked]
    return {"note_id": note_id, "day": day, "terms": terms}


def term_ids_of_note(db: sqlite3.Connection, note_id: int) -> list[int]:
    rows = db.execute("SELECT term_id FROM note_terms WHERE note_id = ? ORDER BY term_id", (note_id,))
    return [term_id for (term_id,) in rows]


def timeline(db: sqlite3.Connection, day: str) -> dict:
    """A Day's Notes in the order they were saved, each Term with its description and other Days."""
    rows = db.execute(
        "SELECT id, saved_at, kind, text FROM notes WHERE day = ? ORDER BY saved_at, id", (day,)
    ).fetchall()
    notes = [
        {
            "id": note_id,
            "time": saved_at[11:16],
            "kind": kind,
            "text": text,
            "terms": [term_view(db, term_id, day) for term_id in term_ids_of_note(db, note_id)],
        }
        for note_id, saved_at, kind, text in rows
    ]
    return {"day": day, "notes": notes}


def recent_notes(db: sqlite3.Connection, limit: int = 10) -> list[dict]:
    """The latest Notes, newest first, so Hermes can find the Note I mean by "that"."""
    rows = db.execute(
        "SELECT id, saved_at, day, text FROM notes ORDER BY saved_at DESC, id DESC LIMIT ?", (limit,)
    ).fetchall()
    notes = []
    for note_id, saved_at, day, text in rows:
        names = db.execute(
            "SELECT t.name FROM terms t JOIN note_terms nt ON nt.term_id = t.id "
            "WHERE nt.note_id = ? ORDER BY t.id",
            (note_id,),
        )
        notes.append({"id": note_id, "day": day, "time": saved_at[11:16], "text": text,
                      "terms": [name for (name,) in names]})
    return notes


def find_note(db: sqlite3.Connection, note_id: int) -> tuple[str, str]:
    """A Note's text and Day."""
    row = db.execute("SELECT text, day FROM notes WHERE id = ?", (note_id,)).fetchone()
    if row is None:
        raise LookupError(f"No Note with id {note_id}.")
    return row


def prune_terms(db: sqlite3.Connection) -> list[str]:
    """Remove every Term that no Note points to. Returns their names."""
    unused = "id NOT IN (SELECT term_id FROM note_terms)"
    names = [name for (name,) in db.execute(f"SELECT name FROM terms WHERE {unused} ORDER BY name")]
    db.execute(f"DELETE FROM terms WHERE {unused}")
    return names


def correct_note(
    db: sqlite3.Connection,
    note_id: int,
    text: str,
    term_names: Iterable[str] = (),
    descriptions: dict[str, str] | None = None,
) -> dict:
    """Rewrite a Note and link it to the right Terms. The original wording is not kept."""
    old_text, day = find_note(db, note_id)
    db.execute("UPDATE notes SET text = ? WHERE id = ?", (text, note_id))
    db.execute("DELETE FROM note_terms WHERE note_id = ?", (note_id,))
    linked = link_terms(db, note_id, term_names)
    for name, description in (descriptions or {}).items():
        describe_term(db, name, description)
    terms = [{**term_view(db, term_id, day), "new": is_new} for term_id, is_new in linked]
    return {"note_id": note_id, "old_text": old_text, "new_text": text, "terms": terms,
            "removed_terms": prune_terms(db)}


def delete_note(db: sqlite3.Connection, note_id: int) -> dict:
    text, _ = find_note(db, note_id)
    db.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    return {"deleted": {"id": note_id, "text": text}, "removed_terms": prune_terms(db)}


def replace_name(db: sqlite3.Connection, term_id: int, old: str, new: str) -> list[dict]:
    """Replace a Term's old name with the new one in the text of its Notes.

    Only whole words are replaced, so renaming "Go" leaves "Google" alone.
    """
    pattern = re.compile(rf"(?<!\w){re.escape(old)}(?!\w)", re.IGNORECASE)
    rows = db.execute(
        "SELECT n.id, n.text FROM notes n JOIN note_terms nt ON nt.note_id = n.id WHERE nt.term_id = ?",
        (term_id,),
    ).fetchall()
    changed = []
    for note_id, text in rows:
        new_text = pattern.sub(lambda match: new, text)
        if new_text != text:
            db.execute("UPDATE notes SET text = ? WHERE id = ?", (new_text, note_id))
            changed.append({"id": note_id, "old_text": text, "new_text": new_text})
    return changed


def merge_terms(db: sqlite3.Connection, a: str, b: str, keep: str | None = None) -> dict:
    """Make two Terms one. The Term that existed first keeps its name, unless `keep` names the other."""
    kept, dropped = sorted([find_term(db, a), find_term(db, b)])  # lower id existed first
    if kept[0] == dropped[0]:
        raise ValueError(f"{a!r} and {b!r} are already the same Term.")
    if keep is not None:
        keep_id = find_term(db, keep)[0]
        if keep_id not in (kept[0], dropped[0]):
            raise ValueError(f"{keep!r} is neither of the two Terms.")
        if keep_id == dropped[0]:
            kept, dropped = dropped, kept
    (kept_id, kept_name), (dropped_id, dropped_name) = kept, dropped
    changed = replace_name(db, dropped_id, dropped_name, kept_name)
    db.execute(
        "INSERT OR IGNORE INTO note_terms (note_id, term_id) SELECT note_id, ? FROM note_terms WHERE term_id = ?",
        (kept_id, dropped_id),
    )
    db.execute(
        "UPDATE terms SET description = COALESCE(description, (SELECT description FROM terms WHERE id = ?)) "
        "WHERE id = ?",
        (dropped_id, kept_id),
    )
    db.execute("DELETE FROM terms WHERE id = ?", (dropped_id,))
    return {"kept": kept_name, "dropped": dropped_name, "merged": True, "notes_changed": changed}


def rename_term(db: sqlite3.Connection, old: str, new: str, description: str | None = None) -> dict:
    """Give a Term a new name and description. If the new name already exists, the two Terms become one."""
    term_id, old_name = find_term(db, old)
    new = new.strip()
    if not new:
        raise ValueError("A Term needs a name.")
    existing = db.execute("SELECT id FROM terms WHERE name = ?", (new,)).fetchone()
    if existing and existing[0] != term_id:
        return merge_terms(db, old_name, new, keep=new)
    changed = replace_name(db, term_id, old_name, new)
    db.execute("UPDATE terms SET name = ?, description = ? WHERE id = ?", (new, description, term_id))
    return {"kept": new, "dropped": old_name, "merged": False, "notes_changed": changed}
