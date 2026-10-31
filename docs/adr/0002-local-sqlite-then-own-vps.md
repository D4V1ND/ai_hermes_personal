# Test locally on SQLite, then run everything on my own VPS

Meetup Intelligence runs on my own VPS: Hermes, the Telegram bot, the Jev scoring script and a SQL database holding Notes, Scores and Event Reports. Before that, it is built and tested on my Windows PC with SQLite, so the data is SQL from day one and moves to the VPS without a file-format migration. Notes, the Profile and reports never live in this repository, because it is public.

## Consequences

- While it runs on the PC, Notes sent with the PC off are lost unless Telegram's `drop_pending_on_cold_boot` is set to `false`; on the always-on VPS this stops mattering.
- On the VPS, Event Reports can be served as links instead of Telegram file attachments.
