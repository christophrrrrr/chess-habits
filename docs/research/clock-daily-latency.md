# Daily chess: cost of quick replies

**Question:** In Daily (correspondence) games, are your quick replies worse than the moves you take time over, and does that depend on the position's criticality or the time of day?

**What to measure:** Daily games only (`time_class = daily`, `time_control` like `1/86400` = 1 day per move).

**First, the data format.** In Daily games chess.com's `[%clk]` is **not** remaining time. In the owner's 29 Daily games (2026, pulled 2026-11-12):
- values never exceed ~2.35 h although the control allows 24 h per move;
- for the 17 games with ≥ 20 plies, `(end_time - start_time) / Σ clk` has a median of **10.04** (10th percentile 10.00, 90th 15.3);
- early moves of fast-played games show values like `0:00:01.4`.

Cross-check on other accounts (top players of the chess.com Daily leaderboard, `https://api.chess.com/pub/leaderboards`, Sep-Oct 2026 archives, 10 finished games with ≥ 20 plies, controls 3 and 7 days per move): the same ratio has a median of **10.27** (25th-75th percentile 10.02-10.67; one outlier at ~1,400, probably a tournament game whose `start_time` is far before the first move). The largest value under the 3-day control is 25,588 s = 7.1 h, i.e. 71 h after × 10, just under the 72 h limit.

Best explanation (**strong evidence, but undocumented; 27 games from the owner plus Daily leaderboard players**): each Daily `[%clk]` is the time between the opponent's move and this move, divided by 10. The chess.com API docs say nothing about clocks ([API docs](https://www.chess.com/news/view/published-data-api)). Chess.com could change or fix this at any time, so the parser must check the ratio per game and refuse to use clocks that do not fit. Then:

- **Reply latency** `L_k = 10 × clk_k` (seconds since the opponent moved). It includes sleep, work and other games, so it is *not* thinking time.

Metrics (if the format is confirmed):

1. **Quick-reply share**: own moves with `L_k < 5 min` (the player was online and answered at once). Threshold to tune.
2. **Quick-reply cost**: error rate (`ΔW ≥ 10`, browser Stockfish) of quick replies vs. replies after ≥ 1 h, **within the same criticality band** (see [clock-time-vs-criticality.md](clock-time-vs-criticality.md)). A finding looks like "in critical positions your instant replies err 3x as often as replies you sleep on".
3. **Time of day of the reply** (from `start_time` + cumulative latency): error rate by local hour, e.g. late-night replies. Overlaps with the psychology/context area.
4. **Timeouts**: Daily losses on time are usually abandonment or vacation issues, not clock management; report counts only.

**Data needed:** Daily PGNs with `[%clk]`, `start_time`, `end_time`; browser Stockfish evals; the player's time zone (profile or browser).

**Reliability:**
- The core risk is the data format itself (undocumented, inferred from 27 games of the owner plus a few leaderboard players; vacation or pauses could break the "÷10" reading; ratio outliers of 15x and more exist).
- Sample sizes are small: the owner played 29 Daily games in 2026 (~1,500 own moves at most). Critical quick replies with errors will be a few dozen per year: report counts and examples, not rates, until ~100 Daily games.
- Latency mixes absence with thought; only the *quick* end (player clearly online) is interpretable.

**Effort:** S on top of the engine pipeline (parsing + one comparison). Before building: repeat the ratio test on a larger sample (100+ games, including games with vacation) and on older years.

**Prior work:**
- No tool found that analyses reply latency in Daily games. Chess.com Insights has a time-of-day calendar for results and accuracy, not reply latency ([help](https://support.chess.com/en/articles/8708925-what-is-insights-on-chess-com)). Lichess Tutor explicitly excludes correspondence from its clock reports ([TutorClockUsage.scala](https://github.com/lichess-org/lila/blob/master/modules/tutor/src/main/TutorClockUsage.scala), [TutorFlagging.scala](https://github.com/lichess-org/lila/blob/master/modules/tutor/src/main/TutorFlagging.scala)).

**Why it's not engine review:** It is about a habit outside the board (answering instantly while on the phone) and its cost, compared with your own considered moves.

**Training link:**
- A "sleep on it" rule: in positions Chess Habits flags as critical-looking (captures, checks, opponent's surprise), do not reply within N minutes.
- Measure: quick-reply share in critical positions and the quick-reply error rate over the next 50 Daily games.

**Verdict:** **Later.** Novel, but low value for the owner (little Daily play) and blocked on confirming the clock format; run the verification spike when Daily support is built.
