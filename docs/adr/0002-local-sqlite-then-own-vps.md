# Test locally on SQLite, then run everything on my own VPS

Meetup Intelligence runs on my own VPS: Hermes, the Telegram bot, the Jev scoring script (parked, see ADR 0001) and a SQL database holding Notes, Terms and which Term appears in which Note. Scores and Event Reports join them when those return. Before that, it is built and tested on my Windows PC with SQLite, so the data is SQL from day one and moves to the VPS without a file-format migration. The Profile is the one exception to SQL: a Markdown file I edit by hand, kept next to the database. Notes, the Profile and reports never live in this repository, because it is public.

The Knowledge Graph lives in that same database as a link table ("this Term appears in this Note"), not in a graph database. The Obsidian-style picture of it, the Graph View, is my own web page that reads the database and draws it.

## Considered Options

- **A graph database (such as Neo4j)**: built for dots and links, but a second server to run and back up. The graph has one kind of link, which a link table covers fully.
- **An Obsidian vault written from the database**: graph view for free, but I don't use Obsidian, and the vault would need syncing from the VPS to every device.

## Consequences

- While it runs on the PC, Notes sent with the PC off are lost unless Telegram's `drop_pending_on_cold_boot` is set to `false`; on the always-on VPS this stops mattering.
- On the VPS, Event Reports can be served as links instead of Telegram file attachments.
