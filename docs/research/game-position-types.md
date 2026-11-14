# Position-type weaknesses

**Question:** In which kinds of positions (pawn structures, open or closed centre, castling setups, material imbalances) do you play clearly worse than your own norm, once the clock and the difficulty of the position are accounted for?

**What to measure:**

1. **Tag every position** where the player is to move with rule-based features from bitboards (python-chess in the service, or chess.js in the browser):
   - *Named pawn structures* (each also tagged with its colour-reversed form). The label set is based on Flores Rios' 28 structures and Soltis' 17 ([Wikipedia: Pawn structure](https://en.wikipedia.org/wiki/Pawn_structure)). Start with rules that are easy to verify:
     - IQP (own or opponent's): a d-pawn with no c- or e-pawn of that side.
     - Hanging pawns: c- and d-pawns side by side, with no b- or e-pawn.
     - Carlsbad: White d4+e3, no c-pawn; Black c6+d5, no e-pawn.
     - Maroczy: c4+e4, no d-pawn, against a d6 pawn.
     - French chain (d4+e5 against d5+e6) and KID chain (d5+e4 against d6+e5).
     - Hedgehog: a6, b6, d6, e6 against c4+e4.
     - Benoni: d5 against c5+d6, with no e-pawn exchange.
   - *Centre type*: `closed` if 2 or more central pawns (c to f files) are blocked head-on; `open` if the d- and e-files have no pawns; otherwise `semi-open`.
   - *King setup*: opposite-side castling, same-side castling, or one king uncastled after ply 24.
   - *Imbalances*: bishop pair against no pair; opposite-coloured bishops; R against minor (+pawns); B against N; queens off before ply 40.
2. **Context model (expected WPL).** For every scored own move (not in the opening book, and not in a decided position with best-line W > 97 or < 3), compute `WPL = max(0, W_best - W_after_played)` in win% points. Fit `E[WPL | eval bucket, clock-left bucket, phase, criticality bucket]` on the player's **own** moves:
   - Eval buckets are the 11 buckets Lichess Insights uses: -600 / -350 / -175 / -80 / -25 / +25 / +80 / +175 / +350 / +600 ([InsightRange.scala](https://github.com/lichess-org/lila/blob/master/modules/insight/src/main/InsightRange.scala)).
   - Clock buckets: ≤3%, 3–10%, 10–25%, 25–50%, ≥50% of the base time (also Lichess's buckets).
   - Phase: opening, middlegame or endgame.
   - Criticality bucket: the gap between the best and second-best move; see [game-decision-points.md](game-decision-points.md).

   A simple cell-mean table with shrinkage works at first. Gradient-boosted trees can come later.
3. **Excess loss for a tag `c`:** `excess_c = mean over moves in c of (WPL - E[WPL | context])`, in win% points per move. Report it next to `n_moves`, `n_games`, and a **game-cluster bootstrap** 95% CI: resample games, not moves, because moves within a game are correlated.
4. **Outcome check:** for games that spend ≥ 6 own moves in `c`, compute `score - W_entry/100`, where `W_entry` is the win% when `c` first appears. This is the actual score against the score the position promised. A tag counts as a weakness only if the move-level excess and the outcome residual point the same way.
5. **Multiple testing:** about 20 tags × 4 time-control groups is about 80 tests. Control them with Benjamini–Hochberg at a 10% FDR, and show at most the top 3 tags.

**Data needed:** chess.com PGN (moves, `[%clk]`); engine evals per own move (best and second-best line, for criticality) from the browser Stockfish job; time control from `time_class` in the archive JSON.

**Reliability:**
- **Coverage on the owner's games** (engine-free count, 2,642 games):
  - An IQP appears between plies 12 and 40 in 242 of 1,305 rapid games (19%), 88 of 439 blitz games, and 176 of 845 bullet games.
  - Opposite-side castling occurs in 180 rapid games (14%).
  - Exact central pawn configurations (c to e files) at ply 24 form 533 distinct patterns in rapid. Only 22 of them reach ≥ 10 games, and together they cover 410 of 1,249 games. **Named classes, not exact patterns, are therefore required.**
- **Minimum sample (rule of thumb, to verify on real data):** at least 30 games and 300 own moves in a tag before showing anything. Per-move WPL is heavy-tailed: most moves lose 0–2 points, and a few lose more than 30. Use a trimmed mean (cap WPL at 50) or the share of moves with WPL ≥ 10 as a robust alternative. See the pilot numbers in [game-patterns.md](game-patterns.md) for the per-move SD.
- **Confounders:**
  - Some structures are simply harder for everyone. Sharp opposite-castling positions produce bigger WPL at every level. That is why the comparison is against the context model, which includes criticality, and why a population baseline from the [Lichess database](https://database.lichess.org/) (about 6% of games carry `[%eval]`, all carry `[%clk]`) is the stronger second reference.
  - Selection: you get IQP positions from your own repertoire, so tag and opening are entangled. Report the openings that feed each tag.
  - Low-node engine noise inflates WPL slightly and evenly. It cancels in relative comparisons but not in absolute ones.
- Rapid has the most signal. Bullet WPL is dominated by the clock, so a bullet tag is shown only if it survives the clock-bucket control.

**Effort:** M. The tagger is S (pure bitboard rules, unit-testable). The context model and bootstrap are M. Lives in **insights**.

**Prior work:**
- **Lichess Insights** has dimensions `myCastling`, `opCastling`, `queenTrade` and `material` (imbalance in pawn units), with ACPL or accuracy as the metric ([InsightDimension.scala](https://github.com/lichess-org/lila/blob/master/modules/insight/src/main/InsightDimension.scala)). This covers raw ACPL by castling side or by queen trade. It has no pawn-structure classes, no control for difficulty or clock, and no CI.
- **ChessBase 18/26 Style Report** "Positional Play" scores avoidance of own pawn weaknesses, the bishop pair, space, and closed positions against average GM games ([criteria](https://help.chessbase.com/CBase/18/Eng/criteria_of_the_style_report.htm); unchanged in CB26 per [ChessBase](https://en.chessbase.com/post/chessbase-2026-a-players-guide-3)). It measures style frequency, not error rate per structure, and it is a paid desktop product.
- **Audit Chess** "Mistake Themes" include "pawn structure" (examples: isolated pawn, pawn chain) and an "Endgame Profile" by ending type ([auditchess.com](https://www.auditchess.com/)). This is the closest overlap. It reports *what your mistakes were about*, not *your error rate in a structure against your own norm*. Its method is not published.
- chess.com Insights: castling phase with results only ([help](https://support.chess.com/en/articles/8708925-what-is-insights)).
- Research: Guid & Bratko measured error as a function of position complexity across champions ([LNCS 4630](https://doi.org/10.1007/978-3-540-75538-8_1); [ChessBase summary](https://en.chessbase.com/post/computers-choose-who-was-the-strongest-player-)). Error rates rise with complexity, which is why the comparison controls for difficulty.

**Why it's not engine review:** A single game cannot tell you that you lose 4 win% more per move than usual in Carlsbad structures. Lichess shows raw ACPL by castling side, but it does not control for the position being sharp or for the clock. That is the difference between "these positions are hard" and "these positions are hard **for you**".

**Training link:** For a weak tag, suggest model games and plans for that structure, plus a drill set of the player's own positions in that tag where WPL ≥ 10 (handled by the training feature). Re-measure `excess_c` on games played after the training started, with the same CI method. A weakness counts as improved when the new CI lies above the old point estimate.

**Verdict:** **Later.** It is a strong long-term differentiator for 1800+ players, but it needs hundreds of analysed games per time control and a validated context model. Build the tagger early: it is cheap and is reused by the taxonomy and decision-point notes.
