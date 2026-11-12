# Decision points (critical moments and find rate)

**Question:** In the positions where only one move keeps your evaluation, how often do you find it, and which *kinds* of only-moves do you miss (quiet moves, retreats, defensive moves, under time pressure), compared with your own norm and with players of your level?

**What to measure:**

1. **Criticality of each own position**, from a MultiPV-2 search: `gap = W_best - W_second` in win% points for the side to move ([Lichess win% formula](https://lichess.org/page/accuracy)). Only score positions with `10 <= W_best <= 95`, so they are not decided yet.
   - `critical`: gap ≥ 10, so the second-best move is already a Lichess "mistake" ([Advice.scala](https://github.com/lichess-org/lila/blob/master/modules/tree/src/main/Advice.scala)).
   - `only-move`: gap ≥ 20.
   - For comparison, the Lichess puzzle generator requires the best move to beat the second by 0.7 on the −1..1 scale (35 win% points) for a puzzle move to be unique ([generator.py](https://github.com/ornicar/lichess-puzzler/blob/master/generator/generator.py)). Kiebitz's threshold is lower on purpose, because many real decision points are defensive and not puzzle-like.
2. **Remove trivial critical positions.** This step is essential: the pilot shows that without it, recaptures dominate. A position does not count when:
   - the best move recaptures on the square of the opponent's last move;
   - the player is in check;
   - there are 3 legal moves or fewer.

   Later, with Maia: drop positions where `p_maia(best | rating) >= 0.8` (the move is obvious for this level).
3. **Find rate:** `FR = found / non-trivial critical`, where `found` = the played move is the best move or has `WPL < 3`.
4. **Breakdowns of FR**, each against the player's overall FR:
   - best-move type: capture / check / quiet / **retreat** (piece moves toward its own back rank) / pawn move / king move;
   - purpose: `defensive` (W_second < 35 ≤ W_best: only move to hold) or `offensive` (W_best ≥ 65 > W_second: only move to win);
   - phase; clock bucket; structure tag.
5. **Difficulty-adjusted FR:** `FR - mean(p_human(best))`, where `p_human` is the share of players at the player's rating who find it. Two ways to get it:
   - offline from [Lichess database](https://database.lichess.org/) games with evals, by gap bucket and move type;
   - from Maia ([Maia-2](https://arxiv.org/abs/2409.20553), MIT; [Maia-3](https://arxiv.org/abs/2605.19091), AGPL code).

   This separates "you miss quiet only-moves" from "everyone misses quiet only-moves".
6. **Recognition (link to time):** the time ratio at critical positions against non-critical ones. This is the vision's "time vs. criticality" analysis, covered by the time/clock research. Here it is only used as a breakdown of FR ("when you spend less than your median time at a critical point, FR drops from X to Y").

**Data needed:** chess.com PGN and `[%clk]`. Browser Stockfish pass with **MultiPV 2 on every own position** (the same pass serves the taxonomy and problem-setting). Move-type features from python-chess or chess.js. Optional Maia.

**Reliability:**
- **Pilot (owner, 40 random games per time control, Stockfish 19 lite WASM, 100k nodes):**

  | Time control | Raw critical / game | Raw FR | **Non-trivial critical / game** | **Non-trivial FR** | FR, best move quiet | FR, best move capture |
  |---|---|---|---|---|---|---|
  | rapid | 4.0 | 81% | 2.5 | 72% | 67% (n=55) | 78% (n=36) |
  | blitz | 4.2 | 83% | 2.4 | 73% | 67% (n=55) | 79% (n=29) |
  | bullet | 3.5 | 77% | 1.9 | 62% | 61% (n=41) | 68% (n=31) |

  Raw "only-moves" (gap ≥ 20) were found 85–94% of the time, because they are mostly recaptures. **Without the triviality filter this metric is meaningless.** Two to two and a half real decision points per game means about 300 games give roughly 700 decision points, about 140 to 400 per breakdown cell.
- **Minimum sample:** FR around 70% with a ±7-point 95% CI needs about 160 decision points, roughly 65 games for one headline FR. A breakdown cell needs at least 60 points before it is shown, which gives about ±12 points. Use a game-cluster bootstrap. Shrink cells toward the overall FR (beta prior worth about 20 points).
- **Noise:**
  - The gap from a low-node MultiPV search could be unstable near the threshold. In the pilot noise check, 47 of 50 lite@100k "critical" labels held under full Stockfish 19 at 1M nodes ([game-patterns.md](game-patterns.md)), so criticality is much more robust than mistake labels.
  - Positions with several near-equal "second" moves need MultiPV 3 or more to be sure.
  - "Found" with `WPL < 3` tolerates engine noise.
  - Mixing defensive and offensive points hides the real pattern, so always split them.

**Effort:** M. MultiPV 2 roughly doubles the per-position cost compared with single-PV. The pilot pass, MultiPV 2 at 100k nodes plus null-move probes, averaged about 0.37 s per ply per single-threaded worker on this PC. Classification and breakdowns are S in **insights**. Maia adjustment: L.

**Prior work:**
- **chess.com Game Review "Great"**: "moves that were critical to the outcome… finding the only good move" ([classification help](https://support.chess.com/article/2965-how-are-moves-classified-what-is-a-blunder-or-brilliant-and-etc)). It marks single moves per game, with no find *rate* and no misses-at-critical-points view.
- **chess.com Insights**: found vs missed forks, pins and mates ([help](https://support.chess.com/en/articles/8708925-what-is-insights)). These are motif-based. Only-moves that are not one of those motifs (quiet, defensive, retreats) are invisible.
- **Lichess Insights** has no criticality dimension ([InsightDimension.scala](https://github.com/lichess-org/lila/blob/master/modules/insight/src/main/InsightDimension.scala)).
- **Audit Chess** "Position Complexity" ("how accuracy holds as positions get sharper") and "Confidence Under Pressure", without published definitions ([auditchess.com](https://www.auditchess.com/)). This is the closest overlap, a sharpness-vs-accuracy view rather than an only-move find rate by move type.
- **Research:**
  - Anderson et al.: difficulty ("blunder potential") dominates skill and time in predicting errors ([arXiv 1606.04956](https://arxiv.org/abs/1606.04956)).
  - Guid & Bratko: a complexity measure that weights errors by position difficulty ([LNCS 4630](https://doi.org/10.1007/978-3-540-75538-8_1)).
  - Regan & Biswas: model sensitivity to move-value differences, i.e. how often a player chooses the best move given the spread of alternatives ([paper](https://cse.buffalo.edu/faculty/regan/papers/pdf/ReBiNF13.pdf)).
  - Leela WDL sharpness as an alternative criticality proxy ([Chess Engine Lab](https://chessenginelab.substack.com/p/evaluating-sharpness-using-lc0s-wdl)).

**Why it's not engine review:** One game shows one critical moment. Only a cross-game rate, **split by the kind of move that was needed**, can say "you find 78% of forcing only-moves but 61% of quiet ones, and 52% of defensive only-moves in the last 10% of your clock". That is a property of the player, not of a move.

**Training link:** Build drills from the player's *own* missed non-trivial decision points, filtered to the weakest cell (for example quiet defensive moves). They become puzzles where the solution is not forcing, which is a gap in standard puzzle sets that favour checks and captures (speculation, based on puzzle uniqueness rules favouring forcing lines). Improvement: FR in that cell on new games against the pre-training FR, with CIs. Expect to need about 60 new decision points in the cell, so weeks for a rapid player.

**Verdict:** **Later** (first item after the MVP). It is the most distinctive game-pattern analysis found and is cheap once the MultiPV-2 pass exists. It is not MVP because the triviality filter and the noise thresholds need validation on more data first.
