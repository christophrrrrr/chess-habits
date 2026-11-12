# Clock and time use: overview

**Question:** What can the clock tell a strong player about *how* they decide, and which of these analyses fit which time control?

This is the overview for the clock area. Each strong candidate has its own note (template format):

| Note | One-line idea | Verdict |
|---|---|---|
| [clock-time-trouble.md](clock-time-trouble.md) | When you fall into time trouble, where the time went, and what it costs you | **MVP** (clock-only part) |
| [clock-flag-losses.md](clock-flag-losses.md) | Points lost on the clock from positions you were winning, and points won on the clock | **MVP** (material proxy) |
| [clock-opening-speed.md](clock-opening-speed.md) | Time burned in positions you know (your own repertoire) vs. time used once you leave it | **MVP** |
| [clock-time-vs-criticality.md](clock-time-vs-criticality.md) | Do you spend time where it matters? Time vs. how critical the position was | Later (flagship, first after MVP) |
| [clock-long-thinks.md](clock-long-thinks.md) | Overthinking easy/forced moves, and whether your long thinks pay off | Later |
| [clock-surprise-response.md](clock-surprise-response.md) | How you react (time and quality) after your opponent's unexpected move | Later |
| [clock-bullet-premoves.md](clock-bullet-premoves.md) | How often you premove, where, and what premoves cost you | Later (cheap add-on) |
| [clock-daily-latency.md](clock-daily-latency.md) | Daily chess: do quick replies cost you? | Later (data format must be confirmed first) |

Dates: researched 2026-11-12. Sources are linked inline.

---

## 1. What the data actually contains (chess.com, verified)

The chess.com Published-Data API returns monthly archives at `https://api.chess.com/pub/player/{username}/games/{YYYY}/{MM}` with, per game, `pgn`, `time_control` ("PGN-compliant"), `time_class`, `end_time`, `start_time` (Daily only), `accuracies` ("if they were previously calculated"), `fen`, `eco` and per-player `result` ([chess.com API docs](https://www.chess.com/news/view/published-data-api)). The docs **do not mention `[%clk]` at all**, say serial access is unlimited but parallel requests may get `429`, and say data refreshes at most every 12 or 24 hours (the page contradicts itself) ([same page](https://www.chess.com/news/view/published-data-api)).

Because the docs are silent on clocks, I checked real data: 1,036 games of the product owner (`chrisaxm`) from 2026-01 to 2026-11-12, pulled from the public API on 2026-11-12. Findings:

| Fact | Evidence |
|---|---|
| Every move carries `{[%clk H:MM:SS.s]}` = the mover's **remaining** time after the move. | All live games inspected. |
| Resolution is **0.1 s**. Trailing `.0` is dropped (`0:09:57`), about 10% of values. | 25,937 of 28,606 bullet clock values have a decimal; final digits 1-9 evenly spread. |
| The value already **includes the increment**. | 120+1 game: Black's first clock is `0:02:00.5` (> 2:00 start). |
| Move time formula works without negatives: `t_k = clk_{k-1} - clk_k + inc`, with `clk_0 = base`. | 0 negative move times across 30k+ own moves. |
| `time_control` is `"60"`, `"180"`, `"120+1"`, `"600"` (seconds), Daily is `"1/86400"` (1 day per move). | Owner's data. |
| `time_class` follows *base + 40 × increment*: `120+1` (160 s) is `bullet`. Chess.com has **no live "classical" class**; 30+0 and slower are `rapid`. | Owner's data; [chess.com time controls](https://www.chess.com/terms/chess-time-controls). |
| Premoves cost exactly 0.1 s on chess.com, and a move needs > 0.1 s on the clock to go through. | [chess.com help: pre-moves](https://support.chess.com/en/articles/8562432-what-are-pre-moves-and-how-do-they-work). In data: 10.1% of bullet move times are exactly 0.1 s vs 3.1% at 0.2 s. |
| **Daily `[%clk]` is not remaining time.** Values never exceed ~2.35 h under a 24 h/move control, and `(end_time - start_time) / Σ clk` has a median of **10.04** (owner, 17 games, ≥ 20 plies) and **10.27** (10 games of Daily leaderboard players, 3- and 7-day controls; max value 7.1 h under 3 days/move = 71 h × 1/10). Best explanation: the value is the elapsed time since the opponent moved, **divided by 10**. | Owner's and leaderboard players' data. Undocumented, so the parser must sanity-check it per game (see [clock-daily-latency.md](clock-daily-latency.md)). |
| **No per-move engine evaluations.** `accuracies` is a single game-level number and is present only for games someone reviewed (31 of 500 games in Oct 2026). | Owner's data. |
| Termination is machine-readable: `result` = `timeout`, `timevsinsufficient`, `resigned`, ... and the PGN `Termination` says "won on time". | Owner's data. |

Consequence: **every quality measure (error, criticality) needs our own engine run**, in the browser (Stockfish WASM; the lite single-threaded build of Stockfish 18 is about 7 MB and runs from a static host without special headers, [nmrugg/stockfish.js](https://github.com/nmrugg/stockfish.js)). Clock-only analyses need no engine and are the realistic MVP.

Lichess (later): stores clocks to 0.1 s, and to 0.01 s when under 10 s left ([Lichess blog](https://lichess.org/blog/WOEVrjAAALNI-fWS/a-better-game-clock-history)); the export API streams 20 games/s anonymously and 60/s for your own games with a token ([lichess API spec](https://github.com/lichess-org/api/blob/master/doc/specs/tags/games/api-games-user-username.yaml)); analysed games carry evals. Premoves are free on Lichess, so the premove detector below is chess.com-specific.

## 2. Shared building blocks (used by every note)

All notes use these definitions so results are comparable.

- **Estimated game time** `T_est = base + 40 × inc` (seconds), the rule both sites use for classification ([Lichess FAQ/source via forum](https://lichess.org/faq); chess.com behaviour verified above).
- **Chess Habits time class**: keep the site's `bullet / blitz / rapid / daily`, and relabel live games with `T_est ≥ 1500 s` as **classical** (Lichess's boundary), because chess.com lumps them into rapid. Always analyse **per exact time control** (`180` and `300` separately) when there are enough games, else per class.
- **Move time** `t_k` for the player's k-th move: formula above; **drop k = 1** (first-move timers distort it) and drop moves after the game's result is decided by flag.
- **Clock fraction before the move** `c_k = clk_{k-1} / T_est`. Bands copied from Lichess Insights so we can compare: `≥ 50%`, `25-50%`, `10-25%`, `3-10%`, `≤ 3%` ([lila InsightRange.scala](https://github.com/lichess-org/lila/blob/master/modules/insight/src/main/InsightRange.scala)). **Time trouble** = `c < 10%`; **scramble** = `c < 3%`.
- **Relative move time** `r_k = t_k / median(t)` over the player's own moves in the same time control, clock band and phase. Reported on a log2 scale (`+1` = twice your usual time). This makes "slow" mean "slow *for you, here*".
- **Win%** from a centipawn eval: `W = 50 + 50 × (2 / (1 + exp(-0.00368208 × cp)) - 1)` ([Lichess accuracy page](https://lichess.org/page/accuracy)).
- **Move loss** `ΔW = W(best) - W(played)` in Win% points. **Error** = `ΔW ≥ 10`, **blunder** = `ΔW ≥ 20`. These match chess.com's expected-points cut-offs for Mistake (0.10) and Blunder (0.20) ([chess.com help](https://support.chess.com/en/articles/8572705-how-are-moves-classified-what-is-a-blunder-or-brilliant-etc)).
- **Criticality** (details in [clock-time-vs-criticality.md](clock-time-vs-criticality.md)): `C_gap = W(best) - W(2nd best)` from MultiPV 2; `G5` = number of moves within 5 Win% of the best; `ΔU` = benefit of computation as in [Russek et al. 2025](https://doi.org/10.1111/cogs.70119).
- **Statistics rule** (vision principle 4): moves inside one game are correlated, so confidence intervals come from a **bootstrap over games**, not over moves. A finding is shown only if each compared group has **≥ 30 games and ≥ 200 moves** and the 95% CI excludes "no difference". Rough power guide: telling an 8% error rate from 12% at 80% power needs about 880 moves per group before clustering, about 1,300 after a design effect of ~1.5 (my calculation, standard two-proportion formula).

## 3. Time control -> which clock analyses fit

Owner's 2026 volume for scale: bullet 719 games, rapid 162, blitz 126, daily 29 (pulled 2026-11-12).

| Time control | What decides games on the clock | Analyses that fit | Thresholds / notes | Analyses that do **not** fit |
|---|---|---|---|---|
| **Bullet** (1+0, 2+1; `T_est` < 180 s) | Flagging, premoves, moves per second in the scramble | Flag losses / clock points; premove patterns; time-trouble onset (when, not whether); opening speed in known lines (every second counts) | Time trouble < 10% = 6 s in 1+0; scramble < 3%. Owner: 46% of 1+0 games went below 6 s, 191/703 lost on time, 41 of those with ≥ 3 points of material up | Time vs criticality (move times are mostly 0.1-2 s, so the signal is tiny); long-think payoff; surprise response (weak) |
| **Blitz** (3+0, 3+2, 5+0; < 600 s) | Mix of chess and clock | All clock-only analyses; time vs criticality; long thinks; surprise response; premoves (less) | Owner 3+0: 34% of games below 18 s, 11/94 lost on time | Daily latency |
| **Rapid** (10+0, 15+10; < 1500 s) | Mostly chess; time trouble is self-inflicted | Time vs criticality (best signal); long thinks; surprise response; time-trouble onset and "where the time went"; opening speed | Owner 10+0: 30% of games below 60 s, 17/162 lost on time, only 1 of them while ≥ 3 up | Premoves (only 3.6% of owner's 10+0 move times are exactly 0.1 s) |
| **Classical** (`T_est` ≥ 1500 s; Lichess later, rare on chess.com live) | Pacing over a long game | Time vs criticality; long thinks; budget pacing (clock at move 20/30/40 vs own good games); surprise response | Sample sizes are small (few games per month), so findings need months of data | Premoves, flag losses (rare) |
| **Daily** (1-14 days/move) | Not the clock: attention and rushing | Quick-reply cost ([clock-daily-latency.md](clock-daily-latency.md)); time-of-day of replies | Only if the `[%clk]` = elapsed / 10 reading is confirmed | Every remaining-time analysis (time trouble, flag, premove, opening speed) |

Matrix view (yes = fits well, weak = runs but low signal, no = does not apply):

| Analysis | Bullet | Blitz | Rapid | Classical | Daily |
|---|---|---|---|---|---|
| Time-trouble onset & cost | yes | yes | yes | yes (pacing) | no |
| Flag losses / clock points | yes | yes | weak | no | no (timeouts there are abandonment) |
| Opening speed (own repertoire) | yes | yes | yes | weak | no |
| Time vs criticality | weak | yes | yes | yes | weak (latency, not thinking) |
| Long thinks / overthinking easy moves | no | yes | yes | yes | no |
| Surprise response | weak | yes | yes | yes | no |
| Premove patterns | yes | weak | no | no | no |
| Increment use ("living on increment") | only 2+1 | 3+2 | 15+10 | yes | no |
| Daily quick-reply cost | no | no | no | no | yes |

## 4. Every candidate evaluated (scores 1-5)

Novelty = nothing comparable exists in chess.com Game Review / Insights, Lichess Insights / Tutor, Aimchess, Chessiro. Value = for a 1800+ player. Reliability = how trustworthy the finding is with realistic data.

| Candidate | Novelty | Value 1800+ | Reliability | Effort | Verdict | Reason |
|---|---|---|---|---|---|---|
| Time-trouble onset, cause and cost | 3 | 5 | 4 | S | **MVP** | Clock-only, big volume, strong players lose many points here; the "where the time went" decomposition is new |
| Flag losses from winning positions / net clock points | 3 | 4 | 4 | S | **MVP** | Clock + final position only; material proxy works without engine |
| Opening speed vs own repertoire | 4 | 4 | 4 | S-M | **MVP** | Clock-only; no tool ties time to *your* known lines |
| Time vs criticality (allocation efficiency) | 5 | 5 | 3 | L | Later (first after MVP) | The flagship, but needs engine MultiPV on every position |
| Long thinks: payoff and overthinking easy moves | 4 | 4 | 3 | M | Later | Needs engine; easy-move proxies (forced, recapture) work without |
| Surprise response | 5 | 4 | 2 | L | Later | Needs a human-move model (Maia) for "surprise" |
| Premove patterns (bullet) | 3 | 3 | 3 | S | Later | Cheap; chess.com-only detector; value depends on bullet focus |
| Daily quick-reply cost | 4 | 2 | 2 | S | Later | Undocumented clock format; small samples |
| Fast vs slow move quality vs own baseline (unconditioned) | 2 | 3 | 2 | M | Drop as standalone | Confounded (see 5.2); kept inside time-vs-criticality |
| Accuracy by time-pressure band | 1 | 3 | 4 | M | Drop as standalone | Lichess Insights already has it (Accuracy x Time pressure); use as input |
| Increment use ("living on increment") | 2 | 2 | 4 | S | Later (small) | Owner plays almost no increment games on chess.com |
| "Behind on the clock" share vs opponent | 1 | 2 | 4 | S | Drop | Aimchess shows it ([aimchess.com](https://aimchess.com)); use as a control variable |
| Move-time variance / rhythm | 1 | 1 | 3 | S | Drop | Lichess Insights "Time variance" dimension ([InsightDimension.scala](https://github.com/lichess-org/lila/blob/master/modules/insight/src/main/InsightDimension.scala)) |
| Time share per phase (budget) | 2 | 3 | 4 | S | Drop as standalone | Chessiro shows it per game; folded into time-trouble "where the time went" |
| Think time vs a human model's predicted time (Allie) | 5 | 4 | 2 | L | Later (research) | Allie 2.1 predicts human think time but is 9.2B params / 18 GB, not runnable in our constraints ([chess-v2](https://github.com/y0mingzhang/chess-v2)) |

## 5. Key findings

1. **The data is good enough for clock analytics, but undocumented.** 0.1 s resolution, increment already included, premoves visible as exact 0.1 s, termination reason machine-readable. None of this is in the chess.com API docs; we verified it on real data. Daily clocks behave differently (see table).
2. **Long thinks look bad for a reason that is not "thinking is bad".** In professional classical games, faster moves are *better* even after controlling for engine-measured complexity ([Sunde, Zegners, Strittmatter, arXiv 2022](https://arxiv.org/abs/2201.10808); [PNAS 2026](https://doi.org/10.1073/pnas.2531472123), [LMU summary](https://www.lmu.de/en/newsroom/news-overview/news/complex-decisions-the-faster-the-better-0a3aafcb.html)). Players think long when a position *feels* hard. So "your slow moves are worse" is a confound, not a finding. Every Chess Habits time analysis must condition on criticality or compare against the player's own baseline in the same kind of position.
3. **Time allocation is measurable and skill-related.** In 12.5 million Lichess games, players spend more time where extra computation helps more (benefit of computation `ΔU`), the effect is concave, grows with more time on the clock, and is stronger in stronger players, though modestly ([Russek et al., Cognitive Science 2025](https://doi.org/10.1111/cogs.70119)). This is the scientific base for "time vs criticality" and gives a formula we can compute in the browser.
4. **Existing tools stop at per-game charts or simple buckets.** Chess.com Game Review only has a "Show Time Spent On Move" toggle ([help](https://support.chess.com/en/articles/8584089)); chess.com Insights has no clock statistics at all, only results by timeout and a time-of-day calendar (Diamond only) ([help](https://support.chess.com/en/articles/8708925-what-is-insights-on-chess-com)). Lichess Insights has move-time buckets (0-1, 1-3, 3-5, 5-10, 10-30, > 30 s) and time-pressure buckets crossed with accuracy ([InsightRange.scala](https://github.com/lichess-org/lila/blob/master/modules/insight/src/main/InsightRange.scala)). Aimchess reports "behind on the clock for X% of moves" ([aimchess.com](https://aimchess.com)). Chessiro (2026) shows per-game average time on accurate vs inaccurate moves, longest think, premove counts and phase times, **per game only** ([Chessiro](https://chessiro.com/blog/inside-chessiro-game-review)). Nobody aggregates time vs criticality across hundreds of games against the player's own baseline.
5. **Lichess designed some of these and never shipped them.** Lichess Tutor's code contains a commented-out `TutorTimeReport` with exactly: time pressure (below 10% of total with the opponent ahead and ≥ 5 moves still played), defeat with high time left, defeat by flag with a good position (eval > +3 or material > 3), slow opening (< 80% of total time left at move 6) and immediate non-forced moves ([TutorTime.scala](https://github.com/lichess-org/lila/blob/master/modules/tutor/src/main/TutorTime.scala), checked 2026-11-12). The live Tutor compares only average clock %, clock used in losses and flag rates with peers ([TutorPerfReport.scala](https://github.com/lichess-org/lila/blob/master/modules/tutor/src/main/TutorPerfReport.scala), [TutorFlagging.scala](https://github.com/lichess-org/lila/blob/master/modules/tutor/src/main/TutorFlagging.scala)), and Tutor's public release status is unclear. This validates the ideas and gives us tested thresholds, but also shows the simple versions are not unique for long.
6. **The owner's own data shows the clock matters most in bullet.** 2026 1+0: 191 of 703 games lost on time, 41 of those with ≥ 3 points of material up; score 0.62 in games that never went below 10% of the clock vs 0.32 in games that did. In 10+0 the clock costs less (17/162 lost on time, only 1 while clearly up). (Single player, material proxy, and the score gap is confounded: hard games both eat time and get lost.)
7. **Human-move models with clock awareness now exist** but are heavy: Allie 2.1 (MIT) predicts the move, the think time and the result, using the clocks ([chess-v2](https://github.com/y0mingzhang/chess-v2), [Allie paper](https://arxiv.org/abs/2410.03893)); Otter conditions move prediction on the clock and recent history ([arXiv 2608.05206](https://arxiv.org/abs/2608.05206)). Maia-2 is MIT ([CSSLab/maia2](https://github.com/CSSLab/maia2)); Maia-3 has small 5M models but its code is **AGPL-3.0** ([CSSLab/maia3](https://github.com/CSSLab/maia3)).

## 6. Recommended MVP slice

One "Clock profile" page per time control, computed from PGN clocks only (no engine):

1. Time-trouble entry rate, onset move, and where the time went before it (opening / one long think / steady drain).
2. Flag losses and wins split by material on the board at the end ("clock points").
3. Time spent in your own known opening positions vs. after leaving them.

The games service stores per-move clocks at import; the insights service computes the three metrics with game-level bootstrap CIs. Engine-based analyses (criticality, long thinks, surprise) follow after the course, with Stockfish WASM in the browser posting evals to the insights service.

## 7. Open questions

- Confirm the Daily `[%clk]` = elapsed / 10 reading on a larger sample (100+ games, older years, games with vacation); so far 27 games from the owner and Daily leaderboard players fit it.
- Benchmark Stockfish 18 lite WASM in a normal laptop browser: positions per minute at MultiPV 3 and a fixed node budget. This decides whether time-vs-criticality is usable on 500+ games.
- Is chess.com's first-move clock (some games show 3+ s used on move 1 in 1+0) a pre-start timer or real thinking? We drop move 1 for now.
- Lag compensation: on chess.com, recorded move times include network effects in bullet; size unknown.
- Which human-move model can run in the browser under a licence compatible with the project: Maia-2 (MIT, ONNX export not found) vs. Maia-3 (AGPL code, browser ONNX exports exist from third parties; weight licence unchecked).
- Do time findings transfer between time controls (a blitz habit showing up in rapid)? Needs data from players with volume in both.
