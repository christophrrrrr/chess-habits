# Time-trouble onset, cause and cost

**Question:** How often and how early do you fall into time trouble, where did the time go before that, and how many points does it cost you compared with your own games that stay calm?

**What to measure:** Per exact time control (fall back to time class if fewer than 30 games). Definitions from [clock-and-time.md](clock-and-time.md): `T_est = base + 40 × inc`, clock fraction before own move k `c_k = clk_{k-1} / T_est`.

1. **Entry rate** `E` = share of games where `c_k < 10%` at some own move k while **at least 5 more own moves** are played (so a mate-in-time-trouble at move 60 does not count). The 10% and "5 more moves" rule is the one Lichess drafted for Tutor ([TutorTime.scala](https://github.com/lichess-org/lila/blob/master/modules/tutor/src/main/TutorTime.scala)). Also report the stricter **scramble rate** (`c < 3%`).
2. **Onset move** `k*` = first own move with `c_k < 10%`. Report median and IQR of `k*` over games with an entry. Early onset (move 25 in a 3+0) is a different problem from late onset (move 55).
3. **Self-inflicted share** = share of entries where the opponent had **more** clock at that moment (Lichess's draft condition). If both players are low, the game was simply long and sharp; if only you are low, it is your habit.
4. **Where the time went** (the new part). For each game with an entry, split the clock spent before `k*` into:
   - `opening` = time on own moves 2-12,
   - `spikes` = time on moves with `r_k ≥ 4` (four times your usual time for that band),
   - `drain` = everything else.
   Classify the game by the largest share relative to the player's games *without* an entry ("you entered time trouble mainly because of the opening in 41% of cases, vs. 18% of opening time in calm games"). This is clock-only.
5. **Pace curve**: median clock fraction at own moves 10, 20, 30, 40 in games you scored 1 vs 0, as a target ("in your wins you have 62% left at move 20, in losses 48%").
6. **Cost**
   - Clock-only (MVP): score in games with entry vs. without, with a logistic regression `score ~ entry + rating_diff + colour` to remove the opponent-strength effect. Warning: this is **confounded** (complex games both eat time and get lost), so show it as "association", not "cost".
   - With engine (later): **time-trouble tax** = error rate (`ΔW ≥ 10`) on moves with `c < 10%` minus error rate on your own moves with `c ≥ 25%` in the **same criticality band** (`C_gap` bins, see [clock-time-vs-criticality.md](clock-time-vs-criticality.md)) and same phase. Expressed as "errors per game caused by time trouble" = tax × average number of time-trouble moves per game.

Per time control: bullet uses the scramble rate and onset (entry is nearly universal); blitz and rapid use all six; classical replaces entry with the pace curve at moves 20/30/40 (FIDE-style controls).

**Data needed:** chess.com PGN `[%clk]` (0.1 s resolution, increment included; verified in [clock-and-time.md](clock-and-time.md)), `time_control`, per-player `result`, ratings. Engine evals only for the cost part. Daily games are excluded.

**Reliability:**
- Entry rate and onset are robust counts; about 30 games give a 95% CI of roughly 17-49% around an observed 30% rate (Wilson), so show "early estimate" until 100 games. The owner's 2026 data has 703 games in 1+0, 162 in 10+0, 94 in 3+0, so bullet and rapid are ready now.
- "Where the time went" needs ≥ 30 games with an entry and ≥ 30 without.
- The engine-based tax compares error rates; telling 8% from 12% needs about 1,300 moves per group with clustering (see statistics rule in the overview). In 10+0 with ~49 entry games x ~8 time-trouble moves that is ~400 moves: not enough for one season of rapid. Show it only when the CI allows.
- Noise: lag in bullet, games abandoned, opponent flagging early (fewer moves), and the confound in the clock-only score comparison.

**Effort:** S for the clock-only metrics (parsing in the games service at import; metrics in the insights service). M for the engine-based tax (needs browser Stockfish evals).

**Prior work:**
- Lichess Insights can chart accuracy against time-pressure buckets `≤3%, 3-10%, 10-25%, 25-50%, ≥50%` ([InsightRange.scala](https://github.com/lichess-org/lila/blob/master/modules/insight/src/main/InsightRange.scala)), only for Lichess games and without criticality matching.
- Lichess Tutor (status unclear, not generally released) compares your average clock % and the clock used in lost games with rating peers ([TutorPerfReport.scala](https://github.com/lichess-org/lila/blob/master/modules/tutor/src/main/TutorPerfReport.scala), [model.scala](https://github.com/lichess-org/lila/blob/master/modules/tutor/src/main/model.scala)). Its richer time-pressure report is commented out ([TutorTime.scala](https://github.com/lichess-org/lila/blob/master/modules/tutor/src/main/TutorTime.scala)).
- Aimchess: "behind on the clock for X% of your moves" ([aimchess.com](https://aimchess.com)).
- Chess.com Insights: no clock statistics, only results by timeout ([help](https://support.chess.com/en/articles/8708925-what-is-insights-on-chess-com)).
- Research: time pressure raises blunder probability, most sharply in extreme pressure, in elite Lichess blitz (39,922 positions, 7 players; preprint, [Research Square](https://sciety.org/articles/activity/10.21203/rs.3.rs-9159157/v1), later [Sci. Rep. 2026](https://www.nature.com/articles/s41598-026-59689-z), full text not read). In top classical games, blunders rise as the clock runs down and time trouble after move 40 is worse than before it ([Chess Engine Lab, 2025](https://chessenginelab.substack.com/p/mistakes-clock)).

**Why it's not engine review:** Game Review looks at one game and grades moves. This looks at the clock across all games and answers *when* and *why* you run short (opening, single long thinks, or steady drain), and whether it is your habit or the game's nature (self-inflicted share). The engine is only used to price the cost against your own calm play.

**Training link:**
- Opening-driven: drill the lines where time leaks (see [clock-opening-speed.md](clock-opening-speed.md)).
- Spike-driven: a "decision deadline" (e.g. 3x your median move time in that band) and a blunder-check routine to finish long thinks.
- Drain-driven: play with **clock checkpoints** taken from your own wins (pace curve: "≥ 60% at move 20").
- Measure: entry rate and median onset move over the next 50-100 games in the same time control, CI compared with the previous window. Success = entry rate down and onset later, without the score dropping.

**Verdict:** **Build for MVP** (clock-only metrics 1-5); add the engine-priced tax later. Cheap, reliable, high value for a player losing 27% of bullet games on time.
