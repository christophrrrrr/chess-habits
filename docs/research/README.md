# Research notes

One file per candidate analysis or research question, e.g. `time-vs-criticality.md`, `gaze-threat-check.md`, `maia-human-baseline.md`.

Read [../vision.md](../vision.md) first. Every proposal must pass the test: **"Could chess.com's Game Review already tell you this?"**

## Template

```markdown
# <Analysis name>

**Question:** What does this analysis tell the player, in one sentence?

**What to measure:** The exact metric(s), and how they are computed.

**Data needed:** Games / clock / engine evals / gaze / context. Where it comes from.

**Reliability:** How many games or moves are needed before the finding is trustworthy? Known noise sources?

**Effort:** Rough size to build (S / M / L) and which service it belongs to.

**Prior work:** Do Lichess Insights, Aimchess, chess.com or published research already do this? Links.

**Why it's not engine review:** How it passes the vision test.

**Training link:** What the player should practise if this finding shows a weakness, and how we'd measure improvement.

**Verdict:** Build for MVP / later / drop, with one line of reasoning.
```
