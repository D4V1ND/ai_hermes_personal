# Spec: Meetup Intelligence, first version

Words in capitals (Note, Term, Day, Timeline, Knowledge Graph, Graph View) are defined in [CONTEXT.md](../CONTEXT.md). Storage and hosting decisions are in [ADR 0002](adr/0002-local-sqlite-then-own-vps.md). All example Notes here are made up.

## Objective

At a meetup I send short Notes to a Telegram bot. Each Note is saved under its Day, its Terms are found and explained, and Terms heard on several Days are connected. Afterwards I can ask for any Day in Telegram, or open the Graph View and click around.

The user is me, alone. The first version is done when the Success Criteria below all hold on my Windows PC.

**Parked, not in this version:** scoring (Jev, Profile), Event Report, Example Project, Main Page, named meetups, the VPS move.

## Parts and build order

| Part id | Responsibility | Depends on |
|---|---|---|
| `store` | The database and every operation on it: save, look up, edit | none |
| `capture` | Hermes turns a Telegram message into a saved Note with Terms, and answers with one line | `store` |
| `lookup` | Hermes answers "notes from 12 Nov" in Telegram | `store` |
| `edit` | Hermes applies corrections I send by chat | `store`, `capture` |
| `graph-view` | The page that draws the Knowledge Graph | `store` |

Build order: `store` → `capture` → `lookup` → `edit` → `graph-view`. Each part can be tried on its own once the parts before it exist. They share one small database, so they stay in this one spec.

## How the work is split

- **Hermes (the agent)** does everything that needs a language model or the internet: reading the Telegram message, transcribing voice, finding Terms, deciding whether a Term already exists, looking a new Term up on the web, understanding dates and corrections, and writing the reply.
- **One Python script (`meetup.py`)** does everything that must be exact: the database, the Day rule, the edit operations, and writing the Graph View. Hermes runs it and reads its JSON output. It makes no network calls and uses no model.

## Behaviour

### Capture

1. I send a text, a voice message or a link to the bot.
2. Hermes asks the script for the list of existing Terms.
3. Hermes finds the Terms in the Note. It reuses an existing Term when the meaning is the same ("Lang Graph", "MCP" vs "Model Context Protocol") and creates a new one only when nothing fits.
4. For each new Term, Hermes looks up a one-sentence description on the web.
5. Hermes saves the Note through the script and answers with one line:

   > Saved. LangGraph, also on 12 Nov.
   > Saved. MCP, new Term.
   > Saved. No Term found.

Rules:

- A Note belongs to the Day it was saved. A Day runs from 04:00 to 04:00 in the time zone of the machine the script runs on.
- A voice Note is stored as its transcript. A link Note is stored as its URL; Hermes opens the page and takes at most three Terms from its main subject.
- A Note with no Term is still saved and appears in its Day's Timeline.
- A Note is never lost because a lookup failed. If the web lookup fails, the Term is saved without a description, and the reply says so. Saying "look up LangGraph again" fills it in later.

### Lookup in Telegram

I ask for a Day in my own words ("notes from 12 Nov", "what did I note yesterday"). Hermes answers with that Day's Timeline as text:

> **12 Nov**
> 18:42 LangGraph
> → LangGraph: a library for building AI agents as step-by-step graphs. Also on 3 Dec.
> 19:05 MCP for tool calling
> → MCP: a standard way for AI models to call outside tools. Only on this Day so far.

A Day with no Notes gets the answer "No Notes on 12 Nov."

### Edit by chat

"That" means the Note I replied to in Telegram, or else my most recent Note. Edits apply straight away with no confirmation, and the reply shows the old and new wording:

> Changed. "Land Graph" → "LangGraph". Now linked to LangGraph (also on 12 Nov).

| I say | Operation | Effect |
|---|---|---|
| "that's LangGraph" | Correct a Note | The Note's text is rewritten and it is linked to the right Terms. The original wording is not kept. |
| "rename Land Graph to LangGraph" | Rename a Term | The Term gets the new name and a fresh description, and the old name is replaced in the text of its Notes. If the new name already exists, the two Terms become one. |
| "MCP and Model Context Protocol are the same" | Merge two Terms | The two Terms become one, and the dropped name is replaced by the kept name in the text of its Notes. The Term that existed first keeps its name, unless I say which name to keep. |
| "delete that Note" | Delete a Note | The Note is removed. |

After any edit, a Term that no Note points to is removed.

### Graph View

- A single HTML file, written into the data folder and rewritten after every change. I open it in a browser on the PC.
- The picture is 3D. Every Day is one dot (orange, larger) and every Term is one dot (smaller, in the text colour: white on the dark theme, black on the light one). A line joins a Term to each Day it came up on. The dots arrange themselves. I can turn the picture, zoom, and drag a dot.
- Each dot has a name tag with the legend's key (a square for a Day, a circle for a Term) and a catalogue number: D01, D02 and so on for Days in date order, T01, T02 and so on for Terms in the order they first came up.
- The page opens on the Index, a list of every Day and Term. Clicking a dot, its name tag or its line in the Index shows that entry. A Day shows its Timeline, as in the Telegram answer. A Term shows its description and the Notes it came up in. Clicking empty space, pressing Escape or clicking "Index" goes back.
- What the page shows follows the approved example page ("Graph View Example"): the picture, a legend, the counts, and a panel for the clicked dot. How it looks does not. The page has its own design, set like a printed index: black and white with orange as the only colour, the picture on the left and the panel on the right (below the picture on a phone). The dark and the light theme follow the PC's setting, and a button switches between them.
- The page only shows. Nothing I do on it is saved. Changes are made by chat (see Edit).

## Tech Stack

- Python 3, standard library only (`sqlite3`, `argparse`, `json`, `datetime`, `unittest`). No packages to install.
- SQLite, one file. Three tables: `notes` (id, saved_at, day, kind, text), `terms` (id, name, description), `note_terms` (note_id, term_id).
- Graph View: one HTML file with the data embedded, plus one graph-drawing JavaScript library loaded from a CDN. The library is chosen in the plan.
- Hermes, running natively on Windows, with its Telegram connection and its `local` voice transcription. It is set up outside this repository.

## Commands

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m unittest discover -s tests
python skill\scripts\meetup.py --help
python skill\scripts\meetup.py graph
```

`$env:MEETUP_DATA` names the data folder. The script stops with an error when it is unset or points inside this repository.

## Project Structure

```
skill/SKILL.md                     tells Hermes how to capture, look up and edit
skill/scripts/meetup.py            the script: database, Day rule, operations, command line
skill/scripts/graph_template.html  the Graph View page without data
tests/test_meetup.py               checks for the script
docs/                              spec, decision records
```

The `skill/` folder is copied or linked into Hermes's skills folder to install it.

The database and the generated Graph View live in the data folder, never here.

## Code Style

Names in code use the glossary words. Functions are small, typed, and take the database connection as an argument. SQL always uses `?` parameters.

```python
def day_of(saved_at: datetime) -> date:
    """The Day a Note belongs to. Days run from 04:00 to 04:00."""
    return (saved_at - timedelta(hours=4)).date()


def days_of_term(db: sqlite3.Connection, term_id: int) -> list[str]:
    rows = db.execute(
        "SELECT DISTINCT n.day FROM notes n "
        "JOIN note_terms nt ON nt.note_id = n.id "
        "WHERE nt.term_id = ? ORDER BY n.day",
        (term_id,),
    )
    return [day for (day,) in rows]
```

## Testing Strategy

- **The script** is checked with `unittest` against an in-memory SQLite database. There is one test per rule in this spec: the Day boundary, saving, lookup, each edit operation, and removal of unused Terms.
- **Hermes behaviour** (finding Terms, reusing Terms, replies) depends on a language model, so it is checked by hand in Telegram with the scenarios under Success Criteria.
- **The Graph View** is checked by generating it from the example data and opening it.

## Boundaries

- **Always:** keep Notes, the database and the generated Graph View outside this repository; run the tests before a commit; use glossary words for names.
- **Ask first:** adding any package or service; changing the tables once real Notes exist; anything that touches a parked feature.
- **Never:** commit Notes, the database, keys or tokens; build scoring or reports in this version; send Note content anywhere other than Hermes's own model and web search.

## Success Criteria

Script, by automated test:

1. A Note saved at 00:30 on 13 Nov belongs to the Day 12 Nov. One saved at 04:00 belongs to 13 Nov.
2. Saving "LangGraph" on 12 Nov and "Lang Graph" on 3 Dec, both linked to the Term LangGraph, gives one Term with two Days.
3. Looking up 12 Nov returns its Notes in the order they were saved, each Term with its description and its other Days.
4. Correcting a Note replaces its text and its Terms, and the old text is gone from the database.
5. Renaming a Term to a name that already exists leaves one Term holding the Notes of both.
6. Merging "Model Context Protocol" into "MCP" leaves one Term, and the Note "Model Context Protocol demo" now reads "MCP demo".
7. Deleting the only Note of a Term removes that Term too.
8. The script refuses to run when the data folder is inside the repository.

By hand, in Telegram and the browser:

9. A text, a voice message and a link each get a one-line answer and appear in that Day's Timeline.
10. Sending "Model Context Protocol" after "MCP" answers "also on …" and creates no new Term.
11. "notes from 12 Nov" returns the Timeline in the format above.
12. "that's LangGraph" after a wrong transcript answers with old → new, and the junk Term is gone.
13. The Graph View for the example data shows four dots and three lines, and clicking each dot shows the right panel.

## Checked against the Hermes documentation (19 Nov 2026)

1. **Connecting the script: confirmed.** A Hermes skill is a folder with a `SKILL.md` instruction file and an optional `scripts/` folder. Hermes runs a bundled script through its `terminal` tool, and `${HERMES_SKILL_DIR}` in `SKILL.md` points at the skill's own folder. So `skill/` in this repository is a Hermes skill.
2. **Voice: confirmed.** Hermes transcribes Telegram voice messages itself and hands the text to the agent. It offers three transcription providers: `local` (faster-whisper on this machine, no key), `groq` and `openai`. This spec uses `local`, so audio never leaves the PC.
3. **Windows: confirmed.** Hermes runs natively on Windows 10 and 11, without WSL.

Still to settle during setup, because the documentation does not state them:

- the exact folder where my own skills go on Windows (expected: `%LOCALAPPDATA%\hermes\skills\`);
- the setting that selects the transcription provider.

One assumption remains mine: the time a Note is saved is close enough to the time I sent it. If the PC is off and the message arrives later, the Note lands on the later Day.

## Open Questions

None. Link Notes and merges are decided and written under Behaviour.
