# Recurring positions and opening exits

**Question:** Which exact positions do you reach again and again, and which of them do you keep handling badly, either with the same weak move or by playing poorly in the first moves after you leave familiar ground?

**What to measure:**

Data on the owner's own games shaped this design (see "Pilot data" below). Exact positions recur almost only in the opening, so the analysis is built around the player's **own opening tree** and the moment the player **leaves it**.

1. **Own tree.** Key every position by EPD (FEN without move counters). For each time-control group (bullet / blitz / rapid+classical / daily), count visits per position with the player to move. A position is *recurring* when it has `visits >= 5`.
2. **Repeated choice quality**, for each recurring position `P`:
   - `choice_share(m)`: share of visits where the player chose move `m`.
   - `WPL(m)`: win-percent loss of `m` against the best move. Win% uses the Lichess formula `W = 50 + 50 * (2 / (1 + exp(-0.00368208 * cp)) - 1)` ([Lichess accuracy page](https://lichess.org/page/accuracy), coefficient fitted on 2300+ rapid games in [lila PR 11148](https://github.com/lichess-org/lila/pull/11148)).
   - `score(m)`: the player's actual score after `m`, plus `n`.
   - **Flag** a position when the player's main choice has `WPL >= 5` (a Lichess inaccuracy is a 5-point drop; see [Advice.scala](https://github.com/lichess-org/lila/blob/master/modules/tree/src/main/Advice.scala)) **and** a better move exists with `WPL < 2`. Rank flags by `visits * WPL` (total win% given away).
3. **Exit point.** For each game, the *exit ply* is the last ply whose position has `visits >= 5` in that time-control group. The **post-exit quality** is the mean WPL of the player's first 5 own moves after the exit ply, compared with the player's mean WPL on own moves 15 to 30 of the same games. This tells "you play the first moves on your own noticeably worse than your normal middlegame", by opening family.
4. **Opening-family roll-up.** Aggregate flags 2 and 3 by ECO family and by the player's repertoire branch, but always show the concrete position, not just the opening name.

**Data needed:** chess.com PGNs (moves only). Evals for opening positions mostly come from the **Lichess cloud-eval API** (`GET /api/cloud-eval?fen=...&multiPv=3`), which returns cached deep evals: a test call for the position after 1.e4 returned depth 60 with 3 PVs ([API docs](https://lichess.org/api#tag/analysis/GET/api/cloud-eval)). It only answers for positions already in its cache. When it has no answer, the browser Stockfish job computes the eval. Cache every eval by EPD in the insights DB, because tree positions are shared by many users. Optional: the Lichess opening explorer for "what players of your rating play here" (an external API: rate-limit and cache it).

**Reliability:**
- Exact-position statistics are deterministic. The engine eval of a position does not depend on the sample, so a flag needs only enough visits to show the *habit*. With `visits >= 5` and one move chosen in 4 or more of them, the habit is clear. The *score* per move is noisy and must not be the main signal: n = 10 games has a 95% CI of about ±30 points on a score.
- **Pilot data (owner, 2,642 chess.com games 2023-07 to 2026-11, engine-free count, scratchpad script):** the median exit ply (last position seen ≥5 times) is **9** in rapid (p90 14), **7** in blitz, **6** in bullet. Only **20** positions at ply ≥ 16 recur ≥5 times in 1,305 rapid games, none in 845 bullet games. The exact pawn structure at ply 30 never recurs 5 times. So "recurring middlegame positions" are **not** a usable exact-match concept for this player. The exact tree is useful for roughly the first 5 to 7 moves per side; deeper "recurrence" needs fuzzy keys (see [game-position-types.md](game-position-types.md)).
- Noise sources: transpositions (handled by EPD keys); move-order tricks; eval of book lines differs little between moves (most WPL < 3), so the flag threshold matters. Mixing time controls hides habits that differ by speed.

**Effort:** S to M. Tree building and visit counts in the **games** service at import. Flagging and post-exit quality in **insights**. Evals: cloud-eval first, browser engine as fallback.

**Prior work:**
- chess.com **Opening Insights** (Diamond) shows your 10 most-played openings, results, and "moves before leaving theory", per opening and not per position ([announcement](https://www.chess.com/news/view/announcing-opening-insights), [Insights help](https://support.chess.com/en/articles/8708925-what-is-insights)).
- **Lichess Insights** can split accuracy/ACPL by opening family or variation, as dimensions `openingFamily` and `openingVariation` ([InsightDimension.scala](https://github.com/lichess-org/lila/blob/master/modules/insight/src/main/InsightDimension.scala)). It works by opening name, not by position, and only for Lichess games with analysis.
- **Audit Chess** has "Opening Trouble" ("costliest openings by win rate and eval loss"), "Opening Tree" and "Opening Drift" ([auditchess.com](https://www.auditchess.com/)). This is the closest overlap. It is per opening plus a W/D/L tree, and its site does not describe per-position repeated-choice flags or post-exit quality.
- **Aimchess** "Opening Improver" exists; no public definition ([aimchess.com](https://aimchess.com)).
- **ChessBase Style Report** "Theory" criterion: average evaluation after the opening, length of theoretical lines, breadth of repertoire ([criteria](https://help.chessbase.com/CBase/18/Eng/criteria_of_the_style_report.htm)).

**Why it's not engine review:** Game Review sees one game and cannot tell that the same inaccuracy was played in 14 games. Opening-level tools report results per opening name, while this analysis names the **exact position and the habitual move**. "Post-exit quality" (how well you play once your own knowledge runs out) is not offered by any tool found.

**Training link:** Each flagged position becomes a repertoire card: the position, the habitual move, the better move or moves, and a short engine line. Use spaced repetition. For weak post-exit quality, train "first moves out of book" in that structure. Improvement: the habitual move's share falls in new games (measurable after about 5 new visits), and post-exit WPL falls compared with the pre-training games of the same opening.

**Verdict:** **MVP candidate**: the cheapest engine-backed analysis. Most evals come from the cached Lichess cloud-eval, the logic is deterministic, and the output is concrete. Keep it to the per-position flags for the MVP and add post-exit quality right after.
