# Time vs. criticality (time-allocation efficiency)

**Question:** Do you invest your thinking time in the positions where it matters (only one move holds, the obvious move is wrong) and save it where many moves are fine, compared with your own history and with players of your level?

**What to measure:** For every own move k with clock fraction `c_k ≥ 10%` (outside time trouble, where time is not a free choice), compute a criticality score of the position **before** the move and the player's relative time `r_k` (own median for that time control, clock band and phase = 1; see [clock-and-time.md](clock-and-time.md)). Win% `W` uses the Lichess formula ([accuracy page](https://lichess.org/page/accuracy)).

Criticality, from simplest to most human-relevant:

| Score | Formula | Engine work | Meaning |
|---|---|---|---|
| `C_gap` | `W(best) - W(2nd best)` from MultiPV 2 | 1 search | Large = only one move keeps the evaluation |
| `G5` | number of moves with `W(best) - W(m) ≤ 5`, MultiPV 5 (capped at 5) | 1 search | 1 = only move, ≥ 4 = many moves are fine |
| `ΔU` (benefit of computation) | `W_deep(m_deep) - W_deep(m_shallow)`, `m_shallow` = Stockfish depth-1 best move | 1 deep + 1 depth-1 search | Large = the "obvious" move is wrong, so thinking pays. Definition from [Russek et al. 2025](https://doi.org/10.1111/cogs.70119) (depth 1 vs depth 15, values mapped to win probability) |
| `ΔU_human` (later) | as `ΔU`, with `m_shallow` = the top move of a human model (Maia) at the player's rating | + Maia inference | Large = a player of your level would usually go wrong here. Russek et al. used Maia as a robustness check |
| `D_maia` (later) | `1 - Σ p_Maia(m)` over moves with `W(best) - W(m) ≤ 5` | + Maia inference | Probability a player of your rating picks a non-good move |

Positions where the game is already decided (`W < 10` or `W > 90`) are excluded: nothing is critical there in practice.

Metrics:

1. **Allocation efficiency** `ρ` = Spearman correlation between `r_k` and `ΔU_k` over the player's non-time-trouble moves, per time control. Compare with the player's own previous window, and later with peers of the same rating (Russek et al. found this relationship in all 11 Lichess time controls, concave, stronger with more clock and with higher Elo, though the Elo effect is modest; in a 60 s game the mean move time rises by about 0.67 s as `ΔU` goes from 0 to 0.4 on their 0-1 win-probability scale, i.e. 40 Win% points; in a 600 s game by about 6.7 s).
2. **The 2x2 matrix** (the main page): critical (`C_gap ≥ 10` or `G5 = 1`) vs. quiet (`G5 ≥ 4`), crossed with fast (`r < 0.5`) vs. slow (`r ≥ 2`). For each cell: share of moves, error rate (`ΔW ≥ 10`), seconds spent. Named findings:
   - **Missed alarms** = critical & fast. Error rate here vs. critical & slow. "In critical positions you moved at half your usual time 31% of the time and erred in 40% of those, vs. 18% when you slowed down." (Numbers illustrative.)
   - **Wasted time** = quiet & slow. Seconds per game spent here, linked to later time trouble ([clock-time-trouble.md](clock-time-trouble.md)).
3. **Critical time share** = (Σ `t` on critical moves / Σ `t` on all non-time-trouble moves) ÷ (share of moves that are critical). Above 1 = you invest where it matters.
4. **Alarm triggers** (descriptive, later): which features predict that the player *slows down* (check, capture, opponent's surprise, material imbalance) vs. which features the critical positions he rushed actually had. This is where causes appear ("you don't slow down for quiet only-moves; you do for tactics").

Per time control: core analysis for **rapid, classical and blitz**. In **bullet** most move times are 0.1-2 s (owner's median 1.1 s in 1+0), so `r` is noisy; show only the missed-alarm rate. **Daily**: latency is not thinking time, so not applicable (see [clock-daily-latency.md](clock-daily-latency.md)).

**Data needed:** chess.com PGN clocks (no evals in the API, verified) + our own Stockfish analysis of every own-move position: one MultiPV 3-5 search at a fixed node budget, one depth-1 search, and a restricted search of the played move if it is not in the MultiPV list. Run in the browser with Stockfish WASM (Stockfish 18 lite single-threaded, about 7 MB, works on a static host: [nmrugg/stockfish.js](https://github.com/nmrugg/stockfish.js)) and post the numbers to the insights service. Maia scores later.

**Reliability:**
- `ρ`: with ~1,000 non-time-trouble moves (about 50 blitz games) the naive SE is about 0.03, roughly 0.04 with game clustering. Detecting a *change* of 0.05 between two windows needs several thousand moves per window (Fisher z), so track `ρ` over quarters, not weeks.
- The 2x2 cells: critical positions are a minority (share unknown, to be measured; speculation 10-20% of non-book moves), and critical & fast is a minority of those. Expect ~200-300 games per time control before the missed-alarm error rate has a useful CI. The owner has that volume only in bullet (where the metric is weakest), so for rapid this needs a long history (import all years, not only 2026).
- Known confound: long thinks happen in positions that *feel* hard, and in professional games faster moves are better even after controlling for engine complexity ([Sunde, Zegners, Strittmatter 2022](https://arxiv.org/abs/2201.10808); [PNAS 2026](https://doi.org/10.1073/pnas.2531472123)). That is why the comparison is always *within* a criticality band, and why `ΔU_human` (subjective difficulty) is the target measure.
- Engine noise: fixed node budgets give slightly different MultiPV gaps between runs; use bins, not exact values. Low-depth evaluations misjudge some endgames.
- Compute cost in the browser is unknown: benchmark before promising "500 games" (open question in the overview).

**Effort:** L. Browser engine pipeline (Web Worker, resumable batches), eval storage in the insights service, the metrics, and a careful UI. Worth it only after the clock-only MVP works.

**Prior work:**
- Research: Russek et al. 2025, 12.5 M Lichess games, players spend more time where computation helps more and stronger players do so more ([Cognitive Science](https://doi.org/10.1111/cogs.70119)). Sunde et al. on professional games relate time to remaining clock, the best-vs-second-best gap and complexity ([arXiv 2201.10808](https://arxiv.org/abs/2201.10808)). Salant & Spenkuch: more decision time offsets complexity, with better players benefiting more ([NBER digest](https://www.nber.org/digest/202208/decision-making-lessons-online-chess)). None of these is a product.
- Chess.com Game Review: per-game "Show Time Spent On Move" toggle ([help](https://support.chess.com/en/articles/8584089)); its "Great move" marks "finding the only good move" in one game ([help](https://support.chess.com/en/articles/8572705-how-are-moves-classified-what-is-a-blunder-or-brilliant-etc)), not your time habits around such moves.
- Lichess Insights: accuracy by absolute move-time bucket, no criticality ([InsightRange.scala](https://github.com/lichess-org/lila/blob/master/modules/insight/src/main/InsightRange.scala)).
- Chessiro (2026): per game, average time on accurate vs. inaccurate moves and "longest think and whether it was worth it" ([Chessiro](https://chessiro.com/blog/inside-chessiro-game-review)).
- Closest: the open-source `chess-game-analyzer` (created Oct 2026, MIT, 0 stars) marks per game the moments where only one move held and lists "long thinks on obvious moves" and "mistakes under 3 seconds", with some cross-game stats ([GitHub](https://github.com/StephanAkkerman/chess-game-analyzer)). It does not report an allocation measure against the player's own baseline as far as its README shows. The idea is in the air; the depth (own baseline, `ΔU`, human model, training loop) is our edge.

**Why it's not engine review:** The engine only labels positions as critical or quiet. The output is about the player's *habit*: whether they notice critical moments and slow down, across hundreds of games, compared with their own baseline. Game Review can say "Nf5 was the only move"; it cannot say "you rush only-moves in quiet positions".

**Training link:**
- Drill set from the player's own **missed alarms** (critical & fast & error): first ask "is this a moment to think?" (yes/no, trains recognition), then solve with a minimum think time.
- From **wasted time** positions: speed drills where any reasonable move is fine (trains letting go).
- In-game rule derived from alarm triggers ("slow down when the opponent's last move changed the pawn structure").
- Measure: missed-alarm error rate and `ρ` per quarter in the same time control, with CIs; success = missed alarms down without more time trouble.

**Verdict:** **Later (first engine analysis after the MVP).** The most novel and valuable clock analysis and the vision's headline, but it needs the browser engine pipeline (L) and a long game history to be reliable.
