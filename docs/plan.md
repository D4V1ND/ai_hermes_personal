# Build plan: Meetup Intelligence, first version

## Context

The [spec](spec.md) is finished and committed on branch `first-version` (commit `c6ba299`). No code exists yet. This plan rolls the spec out in **five phases, one per part of the spec, in the spec's build order**. Every phase ends at a **checkpoint**: a fixed list of things that must be true before the next phase starts. Work stops at each checkpoint until you confirm it.

Words in capitals (Note, Term, Day, Timeline, Graph View) are defined in `CONTEXT.md`. "Criterion 1" to "Criterion 13" are the Success Criteria in the spec.

## Overview

| Phase | Part | Who | Checkpoint (short) |
|---|---|---|---|
| 0 | Setup | Claude | Tests run, plan saved in the repository |
| 1 | `store` | Claude | Criteria 1 to 8 pass as automated tests |
| 2 | `capture` | You set up Hermes, Claude writes the skill | Criteria 9 and 10 hold in Telegram |
| 3 | `lookup` | Claude, you try it | Criterion 11 holds in Telegram |
| 4 | `edit` | Claude, you try it | Criterion 12 holds in Telegram |
| 5 | `graph-view` | Claude, you look at it | Criterion 13 holds in the browser |

Phase 5 only needs Phase 1. If your Hermes setup is not ready when Phase 1 ends, Phase 5 moves forward and Phases 2 to 4 follow after it.

## Decisions made in this plan

1. **Graph library: 3d-force-graph, version 1.80.2, loaded from jsDelivr with a checksum.** Changed on 25 Nov 2026: the picture is 3D, so D3 (flat only) was replaced. 3d-force-graph is the usual library for a 3D graph that arranges itself and can be turned, zoomed and dragged. The name tags are ordinary buttons laid over the picture, so every dot stays reachable by keyboard and keeps the square or round key from the approved example.
2. **The real Graph View keeps what the example shows (legend, counts, click panel) around a 3D picture, in its own design.** Changed on 25 Nov 2026, after looking at what recent award-winning sites (Awwwards Sites of the Day) have in common: the page is set like a printed index. It is black and white plus one colour (orange for a Day; a Term is the text colour), with very large type against small monospace labels, a catalogue number for every dot, and the selected name printed large behind the picture. The page opens on the Index, a list of every Day and Term. It drops the two parts that only explain the example: the "Send a new Note" button and the "What is stored behind the picture" table.
3. **"Inside this repository" is checked as "inside any git repository".** The script walks up from the data folder and refuses if it finds a `.git` folder. This still works after `skill/` is copied into Hermes's skills folder.
4. **Term names ignore upper and lower case**, so "langgraph" cannot become a second Term next to "LangGraph". Deciding that "Lang Graph" means LangGraph stays Hermes's job, as the spec says.

## The script's commands

This is the contract between Hermes and `meetup.py`. Every command prints JSON. Every argument is a plain string, so Hermes never has to quote JSON on a Windows command line.

| Command | What it does | Phase |
|---|---|---|
| `terms` | Lists every Term with its description | 1 |
| `save --kind text\|voice\|link --text "…" [--term NAME]… [--describe NAME "…"]… [--at TIME]` | Saves a Note under its Day and links its Terms. Says for each Term whether it is new and which other Days it came up on | 1 |
| `describe NAME "…"` | Sets or replaces a Term's description | 1 |
| `day [YYYY-MM-DD]` | Returns that Day's Timeline. Without a date: the current Day | 1 |
| `recent [--n 10]` | Lists the latest Notes with ids, so Hermes can find "that" Note | 1 |
| `correct NOTE_ID --text "…" [--term NAME]…` | Rewrites a Note and relinks its Terms. Returns old and new text | 1 |
| `rename OLD NEW [--description "…"]` | Renames a Term and replaces the old name in its Notes. Merges if NEW exists | 1 |
| `merge A B [--keep NAME]` | Makes two Terms one. The older keeps its name unless `--keep` says otherwise | 1 |
| `delete NOTE_ID` | Removes a Note | 1 |
| `graph` | Writes `graph.html` into the data folder | 5 |

`--at` sets the save time by hand. It exists so the example data (Notes on 12 Nov and 3 Dec) can be loaded for Criterion 13.

## Files

```
.gitignore                          .venv/ and __pycache__/
docs/plan.md                        this plan
skill/scripts/meetup.py             the script
skill/scripts/graph_template.html   the Graph View page without data
skill/SKILL.md                      instructions for Hermes
tests/test_meetup.py                one test per rule
```

The database (`meetup.db`) and `graph.html` live in the folder named by `$env:MEETUP_DATA`, never in the repository.

---

## Phase 0: Setup

1. Add `.gitignore` for `.venv/` and `__pycache__/`.
2. Create `.venv` and an empty `tests/test_meetup.py` that runs.

**Checkpoint 0**
- [ ] `python -m unittest discover -s tests` runs without error.
- [ ] Plan and `.gitignore` are committed on `first-version`.

## Phase 1: `store`

Each task: write the tests first, then the smallest code that passes, run all tests, commit.

| Task | Work | Proves |
|---|---|---|
| 1.1 | Three tables (`notes`, `terms`, `note_terms`) and `day_of()`, the 04:00 rule | Criterion 1 |
| 1.2 | `save_note()` and `list_terms()` | Criterion 2 |
| 1.3 | `timeline()`: a Day's Notes in saved order, each Term with description and other Days | Criterion 3 |
| 1.4 | `correct_note()`, `rename_term()`, `merge_terms()`, `delete_note()`, removal of unused Terms | Criteria 4, 5, 6, 7 |
| 1.5 | Data folder check and the command line for all commands except `graph` | Criterion 8 |

Tests use an in-memory SQLite database. Functions take the database connection as an argument and SQL uses `?` parameters, following the spec's Code Style.

**Checkpoint 1**
- [ ] All tests pass, with at least one test for each of Criteria 1 to 8.
- [ ] This works by hand against a throwaway folder outside the repository:
  ```powershell
  $env:MEETUP_DATA = "$env:TEMP\meetup-try"
  python skill\scripts\meetup.py save --kind text --text "LangGraph" --term LangGraph --at 2026-11-12T18:42
  python skill\scripts\meetup.py day 2026-11-12
  ```
- [ ] The same command with `MEETUP_DATA` pointing into the repository stops with an error.
- [ ] You confirm before Phase 2 starts.

## Phase 2: `capture`

**Your setup (can start today, alongside Phase 1):**

1. Install Hermes on Windows and connect the Telegram bot.
2. Select the `local` voice transcription provider. This answers the spec's second open setup question.
3. Set `drop_pending_on_cold_boot` to `false` (ADR 0002), so Notes sent while the PC is off are not lost.
4. Set the data folder once:
   ```powershell
   [Environment]::SetEnvironmentVariable("MEETUP_DATA", "$env:USERPROFILE\meetup-data", "User")
   ```
5. Find where your own skills go (expected `%LOCALAPPDATA%\hermes\skills\`). This answers the spec's first open setup question.

**Claude's tasks:**

| Task | Work |
|---|---|
| 2.1 | Read the Hermes skill documentation again, then write `skill/SKILL.md` with the capture section only |
| 2.2 | Link `skill/` into Hermes's skills folder |

**Checkpoint 2a: the connection** (the smallest possible check, done first on purpose)
- [ ] In Telegram, Hermes runs `meetup.py terms` and reports the result. If this fails, we fix it before writing more instructions.

**Checkpoint 2b: capture**
- [ ] A text, a voice message and a link each get a one-line answer and appear in the Day's Timeline (Criterion 9).
- [ ] "Model Context Protocol" sent after "MCP" answers "also on …" and creates no new Term (Criterion 10).
- [ ] A failed web lookup still saves the Note, and the reply says the description is missing.
- [ ] You confirm before Phase 3 starts.

## Phase 3: `lookup`

| Task | Work |
|---|---|
| 3.1 | Add the lookup section to `SKILL.md`: turn "notes from 12 Nov" or "yesterday" into a date, run `day`, answer in the spec's format |

**Checkpoint 3**
- [ ] "notes from 12 Nov" returns the Timeline in the spec's format (Criterion 11).
- [ ] A Day without Notes answers "No Notes on …".
- [ ] You confirm before Phase 4 starts.

## Phase 4: `edit`

| Task | Work |
|---|---|
| 4.1 | Add the edit section to `SKILL.md`: find "that" Note with `recent`, then run `correct`, `rename`, `merge` or `delete`, and answer with old → new |

**Checkpoint 4**
- [ ] "that's LangGraph" after a wrong transcript answers with old → new, and the junk Term is gone (Criterion 12).
- [ ] Rename, merge and delete each work once by chat.
- [ ] You confirm before Phase 5 starts.

## Phase 5: `graph-view`

| Task | Work |
|---|---|
| 5.1 | `graph_template.html`: the Index, legend, counts and click panel around a 3D picture. 3d-force-graph places the dots. The data comes from one embedded JSON block |
| 5.2 | `write_graph()` and the `graph` command. Every changing command rewrites the page. Note text is embedded safely, so a Note containing HTML cannot break the page. One test for that |
| 5.3 | Load the example data with `save --at …` into a throwaway folder and generate the page |

**Checkpoint 5**
- [ ] All tests still pass.
- [ ] The page for the example data shows four dots and three lines, and clicking each dot shows the right panel (Criterion 13).
- [ ] The page looks right on the PC and on a phone, in the dark and the light theme. You judge this.
- [ ] After a new Note in Telegram, the page shows it when reloaded.

## Final checkpoint: first version done

- [ ] All 13 Success Criteria hold on your Windows PC.
- [ ] The two open setup questions in the spec are answered and written into the spec.
- [ ] No Notes, database, keys or tokens are in the repository.
- [ ] You decide whether to merge `first-version` into `main` and push.

## Not in this plan

- Scoring, reports, named meetups and the server move. The spec parks them.
- The wording difference on time zone ("home time zone" in `CONTEXT.md`, "the machine's time zone" in the spec). The script follows the spec. It only matters at the server move.

## Verification

Automated, before every commit:

```powershell
python -m unittest discover -s tests
```

By hand: the boxes under each checkpoint above.
