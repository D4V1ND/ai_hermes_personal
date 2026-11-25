# Meetup Intelligence

A personal knowledge agent that turns the notes I take at AI meetups, hackathons and conversations into knowledge connected to my interests and projects.

## Language

### Capture

**Day**:
The calendar date I captured a Note on. It stands in for the meetup, hackathon or conversation I was at, which has no name or schedule of its own. A Day runs from 04:00 to 04:00 in my home time zone, so a Note sent after midnight still belongs to the evening before.
_Avoid_: Event, session, meeting, occasion

**Note**:
One thing I capture: a text, a link or a voice note. It belongs to the Day I sent it. When I correct a Note, or merge one of its Terms into another, its text is rewritten and the original wording is not kept.
_Avoid_: message, entry, memo, capture

**Term**:
A technical name mentioned in a Note: a tool, technique, model, paper or company. A Note is often nothing but Terms, or one sentence around one. Every Term gets a short description looked up on the web. Another spelling or an abbreviation of the same thing ("MCP", "Model Context Protocol") is the same Term, not a new one.
_Avoid_: concept, keyword, buzzword

**Timeline**:
A Day's Notes in the order I captured them. When I ask for a Day, I get its Timeline with each Term's description and the other Days that Term came up on.
_Avoid_: log, history, feed

### Connecting

**Knowledge Graph**:
All my Terms across every Day, each linked to the Notes that mention it. There is one graph, not one per meetup, so a Term heard on two Days is a single thing.
_Avoid_: memory, timed memory, network

**Graph View**:
The page that draws the Knowledge Graph in the style of Obsidian's graph. Every Day is one dot and every Term is one dot, with a line wherever a Term came up on a Day. Clicking a Day shows its Timeline; clicking a Term shows its description and its Days.
_Avoid_: dashboard, map, visualisation

### Judging a Note

_Parked: nothing is scored for now. Notes and Term descriptions are kept, so any Day can be scored later._

**Profile**:
My hand-written description of my current interests, projects and goals, plus an "Already know" list of Terms I know well; what every Term is judged against. When it disagrees with what Hermes remembers about me, the Profile wins.
_Avoid_: persona, preferences, interests file

Each Term is first looked up on the web for a short description, then gets three separate Scores from Jev, judged on that description; a Note with no Term is scored as a whole. When Jev fails, the main Hermes model gives them instead and they are marked as **Fallback Scores**.

**Relevance**:
How strongly a Term connects to something in my Profile.
_Avoid_: match, fit

**Novelty**:
How new or surprising a Term is to me, judged against the Profile's "Already know" list; a Term can be novel whether or not it touches my interests.
_Avoid_: interestingness, interest (that word belongs to the Profile)

**Usefulness**:
How directly I can act on a Term: a tool to try, a person to contact, a link to read.
_Avoid_: value, actionability

### Output

_Parked: these terms still speak of Events, which Days replaced. They get redefined when the output is redesigned._

**Event Report**:
The designed HTML page made for one Event after it ends.
_Avoid_: summary, digest, recap

**Example Project**:
An open-source project someone built with a Term, a hackathon winner when one exists. Only Terms with high Usefulness and Relevance get them in the Event Report.
_Avoid_: showcase, use case, demo

**Main Page**:
The one page that gathers what is relevant to me across all Events.
_Avoid_: dashboard, index, home, hub
