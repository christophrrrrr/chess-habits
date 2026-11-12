# Game patterns across many games: overview

Research area: analyses of **how** a strong (1800+) player plays, computed across many of their own games. Every candidate below was checked against Lichess Insights, chess.com Insights and Game Review, Aimchess, Audit Chess, FireChess and the ChessBase Style/Error Reports. Status: November 2026.

## Notes

| Note | Verdict | One line |
|---|---|---|
| [game-mistake-taxonomy.md](game-mistake-taxonomy.md) | **MVP** (reduced) | Classify each mistake as missed threat / allowed tactic / missed chance / quiet misjudgement, plus drift and transition tags; show where each class clusters compared with your own norm. |
| [game-conversion-and-defence.md](game-conversion-and-defence.md) | **MVP** | Points dropped from winning positions and saved from lost ones *against expectation*, with the cause of each failure. The plain conversion rate already exists (Aimchess), so it is context only. |
| [game-recurring-positions.md](game-recurring-positions.md) | **MVP candidate** | Exact positions you reach repeatedly and the habitual weak move; quality of your first moves after leaving your own known tree. Cheapest: mostly cached Lichess cloud evals. |
| [game-decision-points.md](game-decision-points.md) | Later (first after MVP) | Find rate at non-trivial "only-move" positions, split by the kind of move needed (quiet, retreat, defensive) and clock. The most distinctive idea. |
| [game-problem-setting.md](game-problem-setting.md) | Later | How often your moves leave the opponent a critical position, especially when you are worse (practical chances). |
| [game-position-types.md](game-position-types.md) | Later | Excess win% loss per move in named pawn structures and imbalances, controlled for difficulty and clock. |
| [game-surprise-reaction.md](game-surprise-reaction.md) | Later (needs Maia) | Do you play worse after an opponent move a player of your level would not expect? Split by good and bad surprises. |

**Overlaps with other areas of this sweep (merge before building):**
- [clock-surprise-response.md](clock-surprise-response.md) covers the same question as game-surprise-reaction from the clock side.
- [practical-pressure.md](practical-pressure.md) is a Maia-based version of game-problem-setting.
- [structure-familiarity.md](structure-familiarity.md) complements game-position-types with familiarity effects.
- [clock-time-vs-criticality.md](clock-time-vs-criticality.md) uses the same criticality definition as game-decision-points.
- [clock-flag-losses.md](clock-flag-losses.md) and [psych-resignation-and-draws.md](psych-resignation-and-draws.md) overlap with `flag_while_winning` and `early_resignation` in the conversion note.
- [maia-human-baseline.md](maia-human-baseline.md) supplies the human-relevance weighting used by several notes here.

Dropped or folded in: plain conversion rate, accuracy by phase, results by opening, eval-curve "game shapes", and "punishing opponent errors" as a stand-alone metric. Each already exists (Aimchess; chess.com Insights; Lichess "Tactical awareness"). Transition errors and drift are folded into the taxonomy.

## Shared foundations (all notes rely on these)

**Units.**
- Win% for the side to move: `W = 50 + 50 * (2 / (1 + exp(-0.00368208 * cp)) - 1)`. This is the Lichess formula; its coefficient was fitted on positions from 2300+ rapid games ([accuracy page](https://lichess.org/page/accuracy), [lila PR 11148](https://github.com/lichess-org/lila/pull/11148)).
- Move loss: `WPL = max(0, W_best - W_after)`.
- Thresholds: inaccuracy 5, mistake 10, blunder 15 win% points (Lichess's .1/.2/.3 on a −1..1 scale, [Advice.scala](https://github.com/lichess-org/lila/blob/master/modules/tree/src/main/Advice.scala)).
- Moves are not scored in decided positions (W_best > 97 or < 3) or in the first 6 own moves.

**Engine pipeline.** chess.com games carry no evals, only `[%clk]` per move. Of the owner's 2,642 games, 1,440 carry a game-level `accuracies` field and nothing per move ([Published-Data API](https://www.chess.com/news/view/published-data-api)). Chess Habits therefore has to evaluate every game itself:
- **Engine:** Stockfish 19 via [stockfish.js](https://github.com/nmrugg/stockfish.js) (v19.0.1, 2026-10-10; GPL-3.0 engine). The "lite single-threaded" build (≈1.7 MB) runs on any static host without cross-origin isolation headers. The multi-threaded builds need COOP/COEP headers.
- **Measured cost on this PC** (Node 24, one thread per worker): MultiPV 2 at 100k nodes on every ply, plus one null-move probe per mistake, took **about 0.37 s per ply per worker**. 120 games (8,614 plies, about 72 per game) finished in 453 s on 7 workers. In a browser with 4 workers that is about 7 s per game, so 300 games take about 35 minutes. The owner's full history would take about 5 hours. Browser speed is assumed similar to Node and is untested.
- **Consequences:**
  - (a) Analyse incrementally (newest games first), resumable, in Web Workers.
  - (b) Store per-ply results in the insights DB keyed by EPD, so a game is never analysed twice and shared opening positions are free.
  - (c) Take opening positions from the Lichess cloud-eval API first ([docs](https://lichess.org/api#tag/analysis/GET/api/cloud-eval); a test call returned depth 60, 3 PVs).
  - (d) **Re-verify candidate mistakes** (WPL ≥ 7) at a higher budget.
- **Noise check (pilot):** 150 positions re-evaluated with full Stockfish 19 at 1M nodes.
  - Only 37 of 50 lite@100k "mistakes" stayed mistakes (mean |ΔWPL| 5.3).
  - 47 of 50 "critical" labels held.
  - 49 of 50 non-mistake moves stayed non-mistakes.

  So criticality is robust at low budget, mistake labels are not.

**Statistics rules** (apply to every finding):
1. Unit of resampling is the **game**, not the move. Use game-cluster bootstrap CIs for means. Use Wilson CIs for rates.
2. Shrink small cells toward the player's overall value (beta-binomial / empirical Bayes, prior worth about 20 observations).
3. Compare with an **expectation** (own context model: eval bucket × clock bucket × phase × criticality), not raw values. Population baselines per rating band come later from [Lichess DB](https://database.lichess.org/) games with evals (about 6% of games; all have `[%clk]`; CC0).
4. Control multiple testing with Benjamini–Hochberg (FDR 10%). Show at most the top 3 findings per analysis. Hide effects below a minimum size (for example rate ratio < 1.3).
5. Always split by time-control group. Bullet results must be conditioned on clock.

## Pilot on the owner's games (chrisaxm, chess.com)

Corpus: 2,642 standard games, 2023-07 to 2026-11: 1,305 rapid, 845 bullet, 439 blitz, 53 daily. Recent volume is mostly 1+0 bullet (406 of 500 games in Oct 2026), so rapid evidence grows slowly (about 10 games a month now) while bullet grows fast.

Engine pilot: 40 random rated games per time control, Stockfish 19 lite WASM, 100k nodes, MultiPV 2.

| | rapid | blitz | bullet |
|---|---|---|---|
| mistakes (≥ 10 win%) / game | 2.35 | 2.73 | 3.52 |
| largest mistake class | quiet misjudgement 35% | allowed tactic 35% | allowed tactic 37% |
| non-trivial decision points / game | 2.5 | 2.4 | 1.9 |
| find rate at non-trivial decision points | 72% | 73% | 62% |
| find rate when best move is quiet / capture | 67% / 78% | 67% / 79% | 61% / 68% |
| conversion of winning entries (W ≥ 75) | 69% (n=13) | 68% (n=25) | 57% (n=21) |

Engine-free facts that shaped the designs:
- **Exact positions stop recurring early.** The median last ply at a position seen ≥ 5 times is 9 (rapid), 7 (blitz), 6 (bullet). Only 20 positions at ply ≥ 16 recur ≥ 5 times in 1,305 rapid games. "Recurring middlegame positions" therefore need fuzzy keys (structure classes), not exact matching.
- **Structure tags have coverage.** An IQP appears in 19% of rapid games and opposite-side castling in 14%.

These are pilot numbers for sizing and method checks, not findings about the player: n is small and the engine budget is low.

## What is new compared with existing tools

- Existing tools report **what happened** (accuracy by phase, results by opening, conversion rate, motif counts: forks, pins, hanging pieces) or **style frequency** (ChessBase).
- The gap Chess Habits can fill is **why and when**:
  - causes of errors (threat vs chance vs quiet vs drift);
  - only-move find rates by kind of move;
  - points dropped against an expectation that includes the clock and the selection bias;
  - all of it conditioned on context and compared with the player's own norm (and later with peers via Maia or the Lichess DB).
- Audit Chess (free, browser-side Stockfish) is the closest new competitor. It lists "Mistake Themes", "Blown Wins", "Position Complexity" and "Confidence Under Pressure", but publishes no definitions ([auditchess.com](https://www.auditchess.com/)). Chess Habits' defensible difference is **published, validated definitions with sample sizes and confidence**, as vision principle 4 requires.

## Recommendation for the MVP (deadline 2026-11-24)

1. One browser analysis job: Stockfish lite single-threaded, MultiPV 2, 100k nodes, re-verify WPL ≥ 7. Results posted to **insights**.
2. Ship **conversion & defence (v1 expectation)** and the **mistake taxonomy (4 classes + drift)**, split by time control, each with n and CI. Recurring-position flags are the fallback if the engine job slips, since they mostly use cached Lichess cloud evals.
3. Decision points next, reusing the same pass.
