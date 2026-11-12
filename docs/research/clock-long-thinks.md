# Long thinks: overthinking easy moves and whether long thinks pay off

**Question:** When you think much longer than usual, was the position worth it, did the long think produce a better move than you normally play there, and how often do you burn time on moves that were forced or obvious?

**What to measure:** Per exact time control, own moves with clock fraction `c ≥ 10%` (see [clock-and-time.md](clock-and-time.md)).

- **Long think** = `r_k ≥ 4` (four times the player's own median for that time control, clock band and phase) **and** `t_k ≥ 0.05 × T_est` (at least 9 s in 3+0, 30 s in 10+0), so that a 0.8 s "long" bullet move does not count. Thresholds to tune on data.

Part A, overthinking easy moves (works **without engine**):

1. **Easy-move classes** detectable from the position alone:
   - `forced`: 1 legal move;
   - `recapture`: opponent just captured on square X, the player recaptures on X restoring material, and there are ≤ 2 legal recaptures;
   - `check-reply`: in check with ≤ 2 legal moves;
   - `autopilot`: familiar own-repertoire position playing the usual move (see [clock-opening-speed.md](clock-opening-speed.md)).
   With engine (later) add `quiet`: `G5 ≥ 4` (four or more moves within 5 Win% of the best).
2. **Overthink rate** = share of easy moves with `r_k ≥ 2`, and **seconds lost per game** = Σ (`t_k` - own median for that easy class) over easy moves. Compare with the time the same player had left when time trouble began ([clock-time-trouble.md](clock-time-trouble.md)) to say "your overthought forced moves cost you X s per game, Y% of the time you were short of later".

Part B, long-think payoff (needs engine):

3. **Payoff** = error rate (`ΔW ≥ 10`) on long-think moves vs. the player's error rate on normal-time moves **in the same criticality band** (`C_gap` / `G5` bins, see [clock-time-vs-criticality.md](clock-time-vs-criticality.md)). A long think should beat the normal-time baseline in critical positions; if it does not, the player is deliberating without converging.
4. **What came after**: error rate on the *next 3 own moves* after a long think vs. baseline (hypothesis from the vision: "you miss opponent threats after long thinks"). Speculative mechanism: the player plays the following moves fast to recover time.
5. **Long-think triggers**: share of long thinks in critical vs. quiet positions; quiet + long = deliberation without need.

Per time control: Part A in **blitz, rapid, classical** (bullet move times are too short); Part B in **rapid and classical**, blitz if sample allows. Not for Daily.

**Data needed:** PGN moves and `[%clk]`; a move-replay library for legal-move counts and recaptures (Part A). Browser Stockfish evals for Part B (same pipeline as time-vs-criticality).

**Reliability:**
- Part A counts are exact but easy moves with long thinks may be legitimate: a forced move often comes after a sequence the player is still calculating *beyond* the move (pre-thinking the next decision). So seconds "lost" on forced moves are partly time invested in the next move. Report it, but do not call it waste unless the next move is also slow (double spend).
- Long thinks are rare: maybe 1-3 per rapid game (speculation, to measure). Payoff needs ~100+ long-think moves in a comparable band, i.e. ~100+ rapid games.
- Same confound as in the overview: long thinks select hard positions, so compare only within criticality bands.

**Effort:** M. Part A is S (rules on the position, no engine); Part B reuses the engine pipeline of time-vs-criticality.

**Prior work:**
- Chessiro (2026) reports, per game, "your longest think and whether it was worth it" ([Chessiro](https://chessiro.com/blog/inside-chessiro-game-review)).
- `chess-game-analyzer` (Oct 2026) flags "long thinks on forced moves or plain recaptures" per game ([GitHub](https://github.com/StephanAkkerman/chess-game-analyzer)).
- Lichess drafted the opposite for Tutor, "immediate non-forced moves" (move faster than a floor of 2-6 s outside time pressure in a position with > 1 legal move, 5+0 and slower only), never shipped ([TutorTime.scala](https://github.com/lichess-org/lila/blob/master/modules/tutor/src/main/TutorTime.scala)).
- Research: faster moves are better in professional games even controlling for complexity ([Sunde et al. 2022](https://arxiv.org/abs/2201.10808)); in top classical games longer thinks go with weaker moves, which the author attributes to complexity ([Chess Engine Lab 2025](https://chessenginelab.substack.com/p/mistakes-clock)).
- No tool found that measures long-think payoff against the player's own baseline across games.

**Why it's not engine review:** It is about a thinking habit (when you deliberate and whether deliberation converges), across games, against your own normal play. Game Review grades the move; it does not know you spent 90 seconds on it or whether that is unusual for you.

**Training link:**
- Overthinking forced/obvious moves: "play the forced move, think on the opponent's time" habit; Chess Habits shows the player's own examples.
- Long thinks that do not pay: a think-structure drill (candidate moves first, a fixed blunder check, a deadline at 3x median); solve own long-think positions with half the time they used.
- Errors after long thinks: a "reset" check on the next move (opponent threats first).
- Measure: overthink seconds per game, long-think payoff and post-long-think error rate, per quarter.

**Verdict:** **Later.** Part A could ship soon after the MVP (no engine); Part B rides on the engine pipeline. Valuable for rapid/classical, little for bullet.
