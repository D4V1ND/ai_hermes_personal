# Meetup Intelligence

A personal knowledge agent that turns the notes I take at AI meetups, hackathons and conversations into knowledge connected to my interests and projects.

## Language

### Capture

**Event**:
A meetup, hackathon or conversation I attend, scheduled in advance with a name and a time window; every Note captured inside that window belongs to it.
_Avoid_: session, meeting, occasion

**Note**:
One thing I capture during an Event: a text, a link or a voice note.
_Avoid_: message, entry, memo, capture

**Timeline**:
An Event's Notes in the order I captured them.
_Avoid_: log, history, feed

### Judging a Note

**Profile**:
My hand-written description of my current interests, projects and goals; what every Note is judged against. When it disagrees with what Hermes remembers about me, the Profile wins.
_Avoid_: persona, preferences, interests file

Each Note gets three separate Scores, given by Jev. When Jev fails, the main Hermes model gives them instead and they are marked as **Fallback Scores**.

**Relevance**:
How strongly a Note connects to something in my Profile.
_Avoid_: match, fit

**Novelty**:
How new or surprising a Note is to me, whether or not it touches my Profile.
_Avoid_: interestingness, interest (that word belongs to the Profile)

**Usefulness**:
How directly I can act on a Note: a tool to try, a person to contact, a link to read.
_Avoid_: value, actionability

### Output

**Event Report**:
The designed HTML page made for one Event after it ends.
_Avoid_: summary, digest, recap

**Main Page**:
The one page that gathers what is relevant to me across all Events.
_Avoid_: dashboard, index, home, hub
