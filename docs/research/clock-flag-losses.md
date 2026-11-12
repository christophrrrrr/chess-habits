# Flag losses from good positions and net clock points

**Question:** How many points do you lose on time in positions you were winning or holding, how many do you win on time from bad positions, and what is your net "clock score"?

**What to measure:** Per exact time control; Daily excluded (timeouts there are abandonment, not flagging).

For every game decided by the clock (`result` = `timeout` for the loser, or `timevsinsufficient` = draw), classify the **final position** from the player's point of view:

- MVP, no engine: material balance `M` from the final FEN (`fen` field), with P=1, N=B=3, R=5, Q=9. Buckets: `winning` M ≥ +3, `level` -2..+2, `losing` M ≤ -3. Lichess drafted the same fallback (material imbalance > 3) for Tutor ([TutorTime.scala](https://github.com/lichess-org/lila/blob/master/modules/tutor/src/main/TutorTime.scala)).
- Later, with one engine call per game: `W_final` = Win% of the final position for the player ([Lichess Win% formula](https://lichess.org/page/accuracy)). Buckets: `winning` W ≥ 75, `level` 25-75, `losing` W ≤ 25. Lichess's draft used eval > +3.00.

Metrics:

1. **Lost on time while winning** `L_win` and **while level** `L_level` (counts and share of all games).
2. **Won on time while losing** `W_lose` and **while level** `W_level`.
3. **Net clock points** `N = (W_lose + 0.5·W_level) - (L_win + 0.5·L_level)` per 100 games, a rough "points the clock gave or took" figure. (Speculative weighting: a winning position is not a sure point, and a level one is not half a point. With the engine version use expected score `W/100` instead: points lost = Σ over flag losses of `W_final/100`, points gained = Σ over flag wins of `1 - W_final/100`.)
4. **Clock lead at the end of flag losses**: how far behind on the clock you were 10 own moves before flagging. If you were far behind long before, the problem is time-trouble onset ([clock-time-trouble.md](clock-time-trouble.md)); if you were close, the problem is scramble technique.
5. **Scramble technique** (bullet): in games where both clocks were under 10 s, your moves per second in the last 10 s and your share of moves that were premoves (see [clock-bullet-premoves.md](clock-bullet-premoves.md)), compared between flag wins and flag losses.

**Data needed:** chess.com per-player `result`, final `fen`, `[%clk]`. Optional: one Stockfish evaluation of the final position (browser WASM). Verified on real data: owner's 2026 1+0 games have 191 losses on time, **41 of them with ≥ 3 points of material up**, and 141 wins on time, 26 of them with ≥ 3 points down; 10+0 has 17 losses on time, only 1 with ≥ 3 up (pulled from the public API, 2026-11-12).

**Reliability:**
- Counts are exact; the bucket of each game is approximate. Material misjudges positions with a mating attack, a passed pawn about to queen, or a fortress, so the engine version should replace it when available.
- Flag events are frequent in bullet (hundreds per year for an active player), so rates are stable after ~100 bullet games. In rapid they are rare (owner: 17 in 162 games); show raw counts and individual games there, no rates.
- Final position, not the position at the moment the flag became inevitable: a player can be winning for 20 moves and flag at the end. Later version: also report the maximum `W` in the last 10 own moves.

**Effort:** S (clock-only, material from FEN). +S for the engine version (one eval per flagged game, browser).

**Prior work:**
- Chess.com Insights lists wins and losses by timeout and draws by "timeout vs insufficient material", but not the position at the time (Diamond only; [help](https://support.chess.com/en/articles/8708925-what-is-insights-on-chess-com)).
- Lichess Tutor (status unclear) compares the share of your wins and losses decided by flag with rating peers ([TutorFlagging.scala](https://github.com/lichess-org/lila/blob/master/modules/tutor/src/main/TutorFlagging.scala)); the "defeat by flag with good position" metric exists only as commented-out code ([TutorTime.scala](https://github.com/lichess-org/lila/blob/master/modules/tutor/src/main/TutorTime.scala)).
- Lichess Insights can filter by termination, again without position context ([InsightDimension.scala](https://github.com/lichess-org/lila/blob/master/modules/insight/src/main/InsightDimension.scala)).
- No tool found that computes net clock points or splits flag losses by the position on the board.

**Why it's not engine review:** Game Review never grades a game lost on time as a problem of time; it grades the moves. This counts points that the board said were yours and the clock took away, across all games, and says whether the fix is pacing (onset) or scramble technique.

**Training link:**
- High `L_win`: practise converting won positions fast. Chess Habits can export the player's own flag-loss positions (the position 10 moves before the flag) as "win this with 15 seconds" drills. Rule of thumb to test: when ahead on the board and behind on the clock, simplify and premove safe moves.
- High `W_lose`: nothing to fix, but tell the player this is part of their rating (useful self-knowledge for bullet players).
- Measure: `L_win` per 100 games and net clock points in the next 100-200 bullet games vs. the previous window.

**Verdict:** **Build for MVP** (material version). Clock-only, exact counts, and for the owner it already shows a concrete number (41 bullet games lost on time with ≥ 3 points up in 2026).
