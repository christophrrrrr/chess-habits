# Kiebitz: Vision and Research Brief

## One-line pitch

Kiebitz collects data about how you play chess (your games, your clock, and optionally where you look) and turns it into personal, evidence-based feedback on what to train next. **Which analyses it runs is deliberately open**: new ones are researched and added over time.

## Goal

Help chess players, including strong ones, improve by finding patterns in **how** they play that they cannot see themselves, and turning those patterns into concrete things to train.

## How Kiebitz differs from engine game review

Chess.com Game Review, Lichess analysis and similar tools grade **moves**. Kiebitz explains **the player**.

| Engine game review | Kiebitz |
|---|---|
| Looks at **one game** | Looks at **patterns across hundreds of games** |
| Judges **moves** (best, blunder, "brilliant", accuracy %) | Explains **the player**: why and in which situations points are lost |
| Compares against **Stockfish perfection** | Compares against **your own baseline** and **players of your level** |
| Says "the best move was Nf5" | Says "you miss opponent threats after long thinks in sharp positions" |
| Uses only the moves | Also uses **behaviour**: clock, gaze, context (tilt, time of day, session length) |
| The review is the end | Each finding becomes **something to train**, and Kiebitz checks whether it improved |

## Design principles

Every feature must follow these. Any proposed analysis must pass one test:

> **"Could chess.com's Game Review already tell you this?"** If yes, drop it or use it only as an input.

1. **The engine is a tool, not the output.** Stockfish provides raw evaluations; Kiebitz never just shows them back. If a feature amounts to "here's the engine line", it doesn't belong in Kiebitz.
2. **Human-relevant, not engine-relevant.** A move that only a 3000-rated engine finds is not a weakness. Research candidate: **Maia**, an open-source engine trained on Lichess games that predicts what a human of a given rating would play. It could separate "mistakes everyone at your level makes" from "mistakes players of your level usually don't make", the real blind spots. (Check its licence before use.)
3. **Explain causes, not symptoms.** "You blundered on move 23" is a symptom. "Your mistakes cluster after your opponent's unexpected moves" is a cause.
4. **Only show what you can back up.** Each finding comes with its sample size and how confident it is. Small samples get no strong claims.
5. **Make it actionable and close the loop.** Each finding leads to a concrete training suggestion, and Kiebitz tracks whether that weakness shrinks over time.

## Data sources

- **Game history** from Lichess (API export, includes engine evaluations for games that were analysed) and chess.com (public game archive API): moves, results, openings, ratings, clock times.
- **Engine evaluations**: Stockfish (browser WASM build, or low depth inside a service container) or existing Lichess evaluations.
- **Gaze data (optional)**: webcam eye tracking in the browser (WebGazer.js, or the newer MIT-licensed WebEyeTrack) while playing. Accuracy is roughly one square (~100 px), so use **regions and habits**, not exact squares. Candidate setting: real Lichess games played inside our own board via the Lichess Board API. Check which time controls it allows. No engine help during play, analysis only afterwards.

## Candidate analyses (from the first brainstorm)

These are starting points, not commitments. Each needs a research note in [research/](research/).

- **Time vs. how critical the position was**: for each move, how much the position demanded (only one move holds vs. many moves are fine), plotted against the clock time spent.
- **Mistake types**: missed opponent threat, missed own chance, failing to convert a winning position, slow drift (many small inaccuracies), time-trouble errors.
- **Recurring positions**: positions the player reaches repeatedly and keeps getting wrong.
- **Training from own mistakes**: the player's critical mistake positions turned into drills with spaced repetition.
- **Gaze habits**: threat-check ratio (attention on the opponent's pieces vs. your own), last look before moving, tunnel vision, reaction to the opponent's last move. Each linked to mistake types.

## Open research questions

- **Game analyses:** Which patterns in a player's own games best predict lost points? (Mistake types, game phases, position types, recurring positions, converting winning positions, defending worse ones.)
- **Time and clock:** How does time use relate to decision quality? (Time spent vs. how critical the position was, time trouble, overthinking easy moves.)
- **Attention (gaze):** Which gaze metrics are reliable at webcam accuracy, and which link to mistakes?
- **Psychology and context:** Does performance change after a loss (tilt), by time of day, by session length, against higher-rated opponents?
- **Training:** How should findings become practice, and how do we measure that a weakness improved?
- **Prior work:** What do Lichess Insights, Aimchess, chess.com Insights and the research literature already do, and where is the gap?

## Known prior work

- [Lichess Insights](https://lichess.org/blog/VmZbaigAABACtXQC/chess-insights): free; breaks games down by phase, move times, material imbalances.
- [Aimchess](https://aimchess.com): imports chess.com/Lichess games; scores tactics, endgame, opening, time management and other areas.
- Chess.com Insights: mostly behind the paid subscription.
- [ChessEyeTrackerProjectCapstone](https://github.com/ryan1woodard/ChessEyeTrackerProjectCapstone): a student project with a chessboard gaze heatmap. No move analysis. No product was found that combines gaze tracking with game analysis.
- Research: [Reingold et al. 2001](https://www.cs.umb.edu/~marc/pubs/reingold_et_al_psysci2001.pdf). Experts fixate on the pieces that matter and look between pieces, while novices scan piece by piece. See also [Science of Chess: eyetracking and expertise](https://benbalas.substack.com/p/science-of-chess-eyetracking-board-c49).

## Constraints

Kiebitz is built for a university group assignment; see [assignment.md](assignment.md). In short: exactly two backend services (Python or Node), each with its own Azure SQL database; a static web UI; no extra Azure services; no paid APIs without caching and rate limits. **A working MVP comes first; analyses are added on top of it.**
