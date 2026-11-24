"""Meetup Intelligence: the part that must be exact.

The database, the Day rule, the edit operations and the command line.
Hermes runs this script and reads its JSON output. It makes no network
calls and uses no model. Words like Note, Term and Day are defined in
CONTEXT.md.
"""

from __future__ import annotations

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
