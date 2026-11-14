# Problem-setting (practical pressure)

**Question:** How often do your moves leave the opponent a position where only one move holds, especially when you are worse? In other words, do you create practical chances or let the opponent play easy moves?

**What to measure:**

1. For each scored own move (not opening book, best-line W not decided), take the **opponent's next position** `R`. Its criticality comes from the same MultiPV-2 pass the other analyses already run: `gap_R = W_best(R) - W_second(R)` from the opponent's point of view (win% points, [Lichess win% formula](https://lichess.org/page/accuracy)).
2. **Problem-setting rate**: `PSR = share of own moves after which gap_R >= 10`. Split by the player's win% after the move into three bands: `worse` (W < 40), `equal` (40–60), `better` (> 60). The `worse` band is the practical-chances / resourcefulness signal.
3. **Induced error rate**: `IER = share of own moves after which the opponent's reply has WPL >= 10` (a Lichess "mistake", [Advice.scala](https://github.com/lichess-org/lila/blob/master/modules/tree/src/main/Advice.scala)). This is the outcome counterpart of PSR. It depends on the opponent, so it is only meaningful averaged over many games and compared with expectation.
4. **Choice-level version (later, costlier):** at own positions where several moves are "fine" (≥ 2 moves within 3 win% of the best), evaluate `gap_R` for each fine move and check whether the player chose the one that sets the most problems:
   - `pressure_choice = (gap_R(chosen) - mean gap_R(fine moves)) / sd`.
   - Cost: one extra MultiPV-2 search per fine candidate, so analyse only sampled positions.
5. **Baselines:** the player's own PSR and IER by band over time, and population values by rating band from [Lichess database](https://database.lichess.org/) games with evals (about 6% of games). Use Maia-predicted opponent errors as a later refinement: expected IER = Σ_m p_Maia(m | R, opp rating) · 1[WPL(m) ≥ 10].

**Data needed:** PGN (chess.com), the standard browser engine pass with MultiPV 2 on **every** ply (opponent plies too, which the pass already covers), clocks for the time-control split.

**Reliability:**
- **Pilot (owner, 40 random games per time control, Stockfish 19 lite WASM, 100k nodes, MultiPV 2; scratchpad scripts):** PSR / IER by band.

  | Own W after move | rapid | blitz | bullet |
  |---|---|---|---|
  | worse (< 40) | 21% / 8% (n=262) | 19% / 13% (n=216) | 25% / 19% (n=239) |
  | equal (40–60) | 10% / 7% (n=475) | 13% / 9% (n=512) | 11% / 13% (n=453) |
  | better (> 60) | 12% / 9% (n=267) | 9% / 11% (n=350) | 8% / 8% (n=331) |

  The roughly 2x higher PSR when worse is partly mechanical: worse positions are sharper because the opponent has more to lose. So PSR must be read against a **baseline for the same band**, never as an absolute. In bullet, IER when worse (19%) is about twice rapid's (8%). Swindles pay off in fast games, which this metric captures.
- About 25 scored own moves per rapid game, so a few hundred band-moves accumulate quickly. A ±3-point CI on a 15% rate needs about 550 moves, roughly 50–70 games in one band. *Rule of thumb; per-game clustering widens it.*
- Noise: low-node MultiPV gaps are unstable near the threshold (see the noise check in [game-patterns.md](game-patterns.md)). Trivial "critical" positions such as recaptures and check evasions must be excluded, just as in [game-decision-points.md](game-decision-points.md). Opponent strength matters, so control for the rating difference.

**Effort:** M for PSR/IER, which is a by-product of the standard pass and a few lines in **insights**. L for the choice-level version.

**Prior work:**
- **Aimchess "Resourcefulness"**: "Can you find counter-play even when you're in worse positions?" ([aimchess.com](https://aimchess.com)). Its formula is not published. A review describes it as how well you defend worse positions, an outcome-level score ([MyChessPlan review](https://mychessplan.com/aimchess-review-2026-signal-vs-noise/)).
- **Lichess Insights "Luck"** ("How often your opponent fails to punish your mistakes") is the reverse of this question. It is outcome-only, after *your* mistakes ([InsightMetric.scala](https://github.com/lichess-org/lila/blob/master/modules/insight/src/main/InsightMetric.scala)).
- **ChessBase Style Report "Risk"** measures sharpness and complexity of the player's games against GM averages ([criteria](https://help.chessbase.com/CBase/18/Eng/criteria_of_the_style_report.htm)). It describes style, not whether the pressure is created by the player's own moves.
- **Audit Chess** lists "Position Complexity" and "Risk Profile" without definitions ([auditchess.com](https://www.auditchess.com/)).
- Research: sharpness from Leela's WDL, `(2 / (log(1/W - 1) + log(1/L - 1)))^2`, is a position-level complexity proxy ([Chess Engine Lab](https://chessenginelab.substack.com/p/evaluating-sharpness-using-lc0s-wdl)). Anderson et al. show that position difficulty predicts human errors far better than skill or time ([KDD 2016](https://arxiv.org/abs/1606.04956)). Problem-setting is the deliberate creation of such difficulty for the opponent.

**Why it's not engine review:** The engine grades your move by its objective value and treats a move that sets problems the same as an equally evaluated move that sets none. Measuring how often your moves hand the opponent hard decisions, across hundreds of games and against your level, is a practical-play trait that no reviewed tool quantifies.

**Training link:** For a low PSR when worse, practise "make it hard" exercises: from your own worse positions, choose among equal-value moves the one that leaves the most traps, then check with the engine's opponent-side gap. For a low PSR when better, the player may be simplifying too early. Combine with the transition tag in the taxonomy note. Improvement: PSR by band on new games against the own baseline, with a bootstrap CI.

**Verdict:** **Later** (the first version is cheap once the MultiPV-2 pass exists). It is promising for blitz and bullet, where practical pressure decides games, but it needs population baselines before its absolute values mean anything.
