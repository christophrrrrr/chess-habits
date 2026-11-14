# Mistake taxonomy (why points are lost)

**Question:** When you lose win% across many games, *what kind* of error is it (missing the opponent's threat, walking into a tactic, missing your own chance, misjudging a quiet position, slowly drifting, or a bad transition), and in which situations does each kind cluster compared with your own norm?

**What to measure:**

Units: win% `W` for the side to move ([Lichess formula](https://lichess.org/page/accuracy)). For an own move, `WPL = max(0, W_best - W_after)`, where `W_after = 100 - W_best(next position)`. A **mistake** is `WPL >= 10`, Lichess's "mistake" threshold (.2 on its −1..1 scale), and a **blunder** is `WPL >= 15` ([Advice.scala](https://github.com/lichess-org/lila/blob/master/modules/tree/src/main/Advice.scala)). Moves in decided positions (`W_best > 97` or `< 3`) and the first 6 own moves are not scored.

**Move-level classes**, assigned in this order to every mistake:

| Class | Rule (all from engine output plus python-chess) |
|---|---|
| `missed_chance` | The opponent's previous move gave something away: `W_best - B >= 10`, where `B` is the player's `W_after` on the previous own move. The played move kept the player roughly where they were (`W_after >= B - 5`). Typical example: the opponent blundered a piece and you didn't take it. |
| `missed_threat` | **Null-move probe:** flip the side to move (only if not in check; clear en passant) and evaluate. Threat size `T = W_best - W_null`, where `W_null` is the player's win% if they "pass". Rule: `T >= 10`, and the opponent's best reply after the played move is the threat move, or lands on the same square. The threat existed before your move, and your move did not deal with it. |
| `allowed_tactic` | No relevant prior threat, but the opponent's best reply is forcing (capture or check). Your own move created the tactic. |
| `quiet_misjudgement` | Everything else. The loss is not a short forcing sequence. This covers plan errors, wrong pawn moves, wrong piece placement. |

**Orthogonal tags** (a mistake can carry several):
- `low_clock`: own clock below 10% of the base time.
- `transition`: the move trades queens, enters a pure pawn or rook ending, or reduces material by ≥ 6 points in 2 plies. These are the "wrong simplification" errors that strong players make.
- `in_conversion` / `in_defence`: made after a winning or lost entry (see [game-conversion-and-defence.md](game-conversion-and-defence.md)).

**Sequence-level classes:**
- `drift`: a window of 8 consecutive scored own moves with `sum(WPL) >= 15` and no single move `>= 10`. Windows do not overlap.
- `conversion_failure` and `defence_collapse` are defined in the conversion note and attributed to the classes above.

**Outputs per time-control group:**
1. Share of total WPL (not just counts) by class. Points lost are what matter.
2. Rate per 100 scored moves by class.
3. **Over-representation** of each class in a context compared with the player's own baseline:
   - contexts: phase, clock bucket, eval bucket, structure tag from [game-position-types.md](game-position-types.md), after a surprising move from [game-surprise-reaction.md](game-surprise-reaction.md);
   - ratio `rate(class | context) / rate(class | all)`, with a game-cluster bootstrap CI;
   - Benjamini–Hochberg FDR 10% across the context grid.
4. Later: the same rates for players of the same rating band, computed offline from [Lichess database](https://database.lichess.org/) games that carry `[%eval]` (about 6% of games; all have `[%clk]`). Stored as a small lookup table in the insights DB.

**Human relevance (later, with Maia):** weight each mistake by how findable the best move was for a human of the player's rating: `p_maia(best | position, rating)` from [Maia-2](https://arxiv.org/abs/2409.20553) (MIT) or [Maia-3](https://arxiv.org/abs/2605.19091) (AGPL code). A mistake where `p_maia(best) >= 0.5` is a **blind spot** (peers usually find it). One where `p_maia(best) < 0.1` is **hard** for everyone and gets down-weighted.

**Data needed:** chess.com PGN with `[%clk]`. Engine evals come from the browser Stockfish job:
- pass 1: every ply, MultiPV 2;
- probe: one extra null-move search per mistake, about 2 to 3 per game;
- python-chess or chess.js for capture/check/material/phase features.

**Reliability:**
- **Pilot on the owner's games**: 40 random games per time control, Stockfish 19 lite WASM, 100k nodes, MultiPV 2. The scratchpad scripts are not committed.

  | | rapid | blitz | bullet |
  |---|---|---|---|
  | scored own moves / game | 26.7 | 29.2 | 28.8 |
  | mean / median / SD WPL | 3.3 / 0.8 / 6.9 | 3.4 / 0.7 / 8.0 | 4.4 / 0.9 / 8.9 |
  | mistakes (WPL ≥ 10) / game | 2.35 | 2.73 | 3.52 |
  | … of which own clock < 10% of base | 20% | 12% | 14% |
  | `quiet_misjudgement` | 35% | 25% | 24% |
  | `allowed_tactic` | 28% | 35% | 37% |
  | `missed_threat` | 27% | 26% | 17% |
  | `missed_chance` | 11% | 15% | 22% |
  | `drift` windows / game | 0.97 | 0.75 | 0.70 |

  The class mix shifts plausibly with speed: more self-made tactics and missed gifts in bullet, more quiet misjudgements in rapid. These are n = 94 / 109 / 141 mistakes, so the shifts are suggestive only. 300 rapid games give roughly 700 mistakes, about 190 per main class. That is enough to compare class rates across 3 to 4 contexts. Finer grids need more data.
- **Minimum sample:** a context comparison needs at least 30 mistakes of the class inside the context. Otherwise show nothing. Rate ratios below 1.3 are not reported even when significant.
- **Classification noise:**
  - The rules are heuristics. The `missed_threat` vs `allowed_tactic` boundary depends on the null-move probe. It fails in zugzwang-like positions, where passing is not neutral, and gives "tempo" threat values of 3 to 8 points in normal positions. That is why `T >= 10`.
  - Low-node evals mislabel mistakes. In the pilot noise check, only **37 of 50** lite@100k-node "mistakes" stayed mistakes when re-checked with full Stockfish 19 at 1M nodes (mean |ΔWPL| 5.3). Non-mistakes were stable (49/50). **Rule:** re-verify every candidate with `WPL >= 7` at a higher budget before classifying. That is only about 3 to 5 positions per game. See [game-patterns.md](game-patterns.md).
  - **Validation plan before shipping:** the owner (≈2380) hand-labels 150 to 200 own mistakes into the 4 classes. Target ≥ 80% agreement per class. Merge classes that cannot reach it. Store labels as a regression test set.
- Bullet: most mistakes are clock-driven. Report the taxonomy *within* clock buckets, otherwise `low_clock` explains everything.

**Effort:** M for the 4 move classes, drift and tags. M for validation and the labelling UI, which can be a simple page in the static UI. L for the Maia weighting. Lives in **insights**. Engine work is in the browser job shared with all analyses.

**Prior work:**
- **chess.com Game Review** labels single moves: Blunder (≥ 0.20 expected points lost), Mistake (0.10–0.20), Inaccuracy (0.05–0.10), and "Miss" ("fail to capitalize on your opponent's mistake") ([classification help](https://support.chess.com/article/2965-how-are-moves-classified-what-is-a-blunder-or-brilliant-and-etc)). It works per game and gives no cause.
- **chess.com Insights** (Diamond): found vs missed forks, pins and mates; pieces left hanging by you and by the opponent ([help](https://support.chess.com/en/articles/8708925-what-is-insights)). These are tactic *motifs*, not causes, and they come without context or baseline.
- **Lichess Insights**:
  - "Tactical awareness": after an opponent mistake, your move is not a mistake;
  - "Luck": after your mistake, the opponent also errs;
  - ACPL / accuracy by phase, clock %, eval bucket, piece moved.

  ([InsightMetric.scala](https://github.com/lichess-org/lila/blob/master/modules/insight/src/main/InsightMetric.scala), [PovToEntry.scala](https://github.com/lichess-org/lila/blob/master/modules/insight/src/main/PovToEntry.scala)). It has no threat-vs-chance split and no drift.
- **Audit Chess** "Mistake Themes" ranks errors by tactic motif (fork, pin, back-rank), "positional weakness", "endgame rule" and "pawn structure". It also offers "Tactic Profile" (as attacker and defender) and "Time Pressure Analysis" ([auditchess.com](https://www.auditchess.com/)). This is the closest overlap, motif-oriented, and its method is not published.
- **FireChess** clusters mistakes "by type" using "Stockfish evaluation deltas" plus heuristics ([FireChess blog](https://www.firechess.com/blog/free-chess-analysis-tools-2026)). It is vendor-described only.
- **ChessBase Error Report** compares error rate with an average GM and gives a "Blunder Elo" ([ChessBase 26 guide](https://en.chessbase.com/post/chessbase-2026-a-players-guide-3)).
- Research:
  - Anderson, Kleinberg & Mullainathan: position difficulty ("blunder potential" = share of legal moves that are blunders) predicts errors much better than skill or time (accuracy 0.75 vs 0.55 vs 0.53), shown on tablebase endgames ([arXiv 1606.04956](https://arxiv.org/abs/1606.04956)). This supports controlling for difficulty when comparing classes.
  - Maia blunder prediction ([arXiv 2006.01855](https://arxiv.org/abs/2006.01855)).

**Why it's not engine review:** Engine review says *that* a move lost 12%. This analysis says *what kind* of error it was, using a null-move threat probe and a sequence view that no reviewed tool exposes. It then says in which contexts that kind is over-represented **for this player compared with their own norm**, for example "your missed threats double in sharp middlegames after you spent more than 20% of your clock". Motif lists (fork, pin) describe the board. Classes describe the player's failure mode.

**Training link:**

| Dominant class | Practice | Improvement measure |
|---|---|---|
| `missed_threat` | Blunder-check routine ("what does the opponent's last move attack?"); defence puzzles from own positions | rate per 100 moves falls on new games |
| `allowed_tactic` | Checks/captures/threats scan before committing; own-position puzzles from the opponent's side | rate falls |
| `missed_chance` | "Punish the mistake" puzzles from own games | share of `missed_chance` among opportunities falls |
| `quiet_misjudgement` | Structure-specific model games (link to position types) | excess WPL in the tagged structure |
| `drift` | Slow, annotated rapid games; plan-writing exercise | drift windows per game |
| `transition` | Endgame-transition exercises (should I trade into this ending?) | WPL on transition moves |

**Verdict:** **MVP**, in a reduced form: the 4 move-level classes plus drift, and shares by time control and clock bucket. It is the core "explain the player" feature. The extra engine cost is only one null-move search per mistake. Context over-representation, the Maia weighting and population baselines come later. Validate against the owner's hand labels before showing classes as facts.
