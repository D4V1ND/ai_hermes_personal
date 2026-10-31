# Score Notes with Jev through LangChain, not the Hermes Jev plugin

Every Note is scored by TypeSafe's Jev from day one, called through LangChain's official `langchain-typesafe` integration (`TypeSafeClassifier`, TypeSafe API key) from a small script that Hermes runs. Hermes keeps everything else: Telegram capture, scheduling, research and delivering the Event Report. LangChain is limited to this one scoring step.

## Considered Options

- **Hermes community `jev` plugin**: native `jev_evaluate` tool, but v0.1.2 prerelease whose direct TypeSafe route and accuracy are marked unverified by its author.
- **TypeSafe's own Python SDK**: one layer thinner than LangChain; not chosen because I prefer the LangChain integration.
- **Main Hermes model scores the Notes**: no extra account, but less consistent Scores across Events, which the Main Page will depend on.

## Consequences

When Jev fails, the main Hermes model scores the Notes so the Event Report still arrives on time. Those Scores are marked as Fallback Scores, and the Telegram message that delivers the report says that Jev scoring had a problem.
