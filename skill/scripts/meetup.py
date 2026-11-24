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
