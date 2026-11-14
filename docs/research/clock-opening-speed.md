# Opening speed: known positions vs. own play

**Question:** How much clock do you spend in opening positions you have already played many times, and how do you use time (and play) on the first moves after you leave your own repertoire?

**What to measure:** Per exact time control, per colour, per opening family (chess.com `ECOUrl` gives a readable name). All "familiarity" is computed from the player's **own earlier games only** (no leakage from later games, no external database).

Definitions:

- Position key = first four FEN fields (pieces, side to move, castling, en passant).
- **Familiar position** before own move k: the player had this exact key, same colour, in **≥ 3 earlier games** (all live time controls pooled, since a repertoire is shared across them).
- **Autopilot move**: familiar position **and** the move played equals the player's most frequent earlier move there.
- **Exit move** `k_exit` = first own move whose position is not familiar. If the opponent deviated first, mark the exit as `opponent-exit`, else `own-exit` (the player chose a new move in a familiar position).

Metrics:

1. **Autopilot cost** = Σ `t_k` over autopilot moves, as a share of `T_est`, and its median per move. The floor is premove speed (0.1 s on chess.com). Example output: "In 3+0 you spend 7% of your clock on moves you have played 10+ times." (Number illustrative.)
2. **Exit depth**: median `k_exit` per opening family and colour, with the split own-exit / opponent-exit.
3. **Post-exit spend**: relative time `r_k` (own baseline, see overview) on the first 3 own moves after `k_exit`. Low `r` after an opponent-exit = playing on autopilot in a new position.
4. **Opening budget vs result**: share of `T_est` used by own move 12, and its relationship with time-trouble entry later ([clock-time-trouble.md](clock-time-trouble.md)) and with score (logistic, controlled for rating difference). Owner's 2026 baseline, clock-only: median share used by move 12 is 20% in 1+0, 16% in 3+0, 13% in 5+0, 14% in 10+0 (pulled 2026-11-12). Lichess's unshipped draft flagged a "slow opening" when < 80% of total time is left at move 6 ([TutorTime.scala](https://github.com/lichess-org/lila/blob/master/modules/tutor/src/main/TutorTime.scala)); Chess Habits uses the player's own distribution instead of a fixed cut-off.
5. Later, with engine: **quality just after exit** = error rate (`ΔW ≥ 10`) on the first 3 own moves after exit vs. the player's own early-middlegame baseline at the same criticality. Answers "you leave your prep and immediately misplay, fast".

Per time control: in bullet the autopilot cost is the headline (every second counts); in blitz and rapid the post-exit spend and quality matter more; in classical the budget at move 12/20 matters; not for Daily.

**Data needed:** PGN moves + `[%clk]` from chess.com; colour; `ECOUrl`. A move-replay library (e.g. python-chess in the insights service, or chess.js in the browser) to build position keys. No engine for metrics 1-4.

**Reliability:**
- Needs history: familiarity starts working after roughly 50+ games per colour in a time-control group (the owner has 700+ bullet games in 2026, enough). Early games will show few familiar positions; say so on the page.
- Opening families with < 20 games are pooled into "other".
- Noise: transpositions are handled by keys; chess.com may skip the first-move timer (we drop own move 1); premoves of book moves are real behaviour, not noise.
- The score link (metric 4) is an association, not a cause.

**Effort:** S-M. Position keys and familiarity counting are simple but must be stored incrementally (insights service). No engine for the MVP part.

**Prior work:**
- Chess.com Insights "Openings > Mastery" shows the average number of *book* moves before you leave book, plus results per opening, no time (Diamond; [help](https://support.chess.com/en/articles/8708925-what-is-insights-on-chess-com)).
- Lichess Insights can show move time by game phase or opening, in absolute buckets ([InsightDimension.scala](https://github.com/lichess-org/lila/blob/master/modules/insight/src/main/InsightDimension.scala)), but does not know which positions are *your* repertoire.
- Chessiro shows opening/middlegame/endgame time per game ([Chessiro](https://chessiro.com/blog/inside-chessiro-game-review)).
- Lichess's personal opening explorer exists but now needs an OAuth token for API use ([Lichess blog](https://lichess.org/@/thibault/blog/the-opening-explorer-now-requires-authentication/FSWh9Zg3)); using our own stored games avoids that dependency.
- No tool found that measures clock spent on *your own* repeated positions.

**Why it's not engine review:** No engine is involved in the main metrics. It uses the player's own history to separate "known" from "new" positions, which Game Review cannot know, and turns it into seconds saved.

**Training link:**
- High autopilot cost: repertoire drill of the specific lines (spaced repetition on the player's own most-played positions) so they become instant; in bullet, premove the known replies.
- Low post-exit spend with poor results: a rule "stop and think once the opponent leaves my line" (first move after an opponent-exit gets at least your median think time x 2).
- Measure: autopilot cost and post-exit `r` over the next 50-100 games in that time control; success = autopilot cost down, post-exit spend up, no extra time trouble.

**Verdict:** **Build for MVP.** Clock-only, cheap, high novelty, and directly actionable as repertoire drills.
