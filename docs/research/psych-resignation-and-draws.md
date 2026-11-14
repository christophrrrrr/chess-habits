# Resignation and draw-agreement habits

**Question:** Do you resign (or agree draws) in positions where players of your level still score well, and how many points does that cost you compared with how your opponents behave?

**What to measure:**

1. **Resignation set.** All rated games where the player's `result` is `resigned`. The chess.com archive also includes the final position (`fen`), the move count, and both clocks from the last `[%clk]` comments.
2. **Expected score at resignation, `E_res`.** This is the score the resigner would expect by playing on.
   - Evaluate the final FEN once with Stockfish (browser WASM, fixed depth for example 18, or about 1 s).
   - Map the evaluation to a human expected score with a lookup table `P(score | eval bucket, rating band, time class, own-clock bucket, opponent-clock bucket)`.
   - Build the table offline once from the Lichess open database. It is CC0; about 6% of standard games carry `[%eval]`, and all games since April 2017 carry `[%clk]` ([database.lichess.org](https://database.lichess.org/)).
   - Alternatives: the Maia-2 value head (MIT licence, rating-conditioned, but it outputs a White-perspective expected score and ignores the clock; [paper](https://arxiv.org/abs/2409.20553), [repo](https://github.com/CSSLab/maia2)), or the Lichess Win% curve `50 + 50·(2/(1+e^(−0.00368208·cp)) − 1)`. That curve is calibrated on strong players and has no clock term, so use it only as a fallback ([Lichess accuracy page](https://lichess.org/page/accuracy)).
3. **Metrics per time class:**
   - **Premature-resignation rate:** share of resignations with `E_res ≥ 0.15`. The threshold is a setting; also show 0.10 and 0.25.
   - **Points given away:** `Σ E_res` over all resignations, per 100 games. Expected points left on the table.
   - **Clock context:** share of resignations where the opponent had less than 15% of the base time left, or less than 10 s in bullet and blitz. Low clocks change conversion odds a lot: in Lichess 3+0, advantages convert much less reliably once clocks drop to about 10–30 s ([Chess Engine Lab, 2026](https://chessenginelab.substack.com/p/evaluation-time-score)).
   - **Peer baseline from the same data:** the same metrics for *opponents resigning against the player*. These are players of the same level in the same pool. This gives a fair baseline without extra data.
4. **Engine-free proxy (shown first, replaced once evals are in):** material balance at resignation from the final FEN (P=1, N=B=3, R=5, Q=9), the player vs their resigning opponents.
5. **Agreed draws:**
   - The chess.com API records only the result `agreed`. Offers and declined offers are **not** in the PGN or JSON, so draw-offer behaviour cannot be analysed.
   - For agreed draws: `E_draw` is the player's expected score in the final position (same lookup). Report the share agreed with `E_draw ≥ 0.60` ("you agreed draws when better") and with `E_draw ≤ 0.40` (good saves). This split also uses the rating difference.
6. **Playing on too long:** the number of moves played after the expected score first fell below 0.03 in losses by checkmate. This needs a full-game eval and costs only time online, so it is low priority.

**Data needed:**
- From the chess.com archives: `result`, final `fen`, `[%clk]`, ratings, time class.
- One Stockfish evaluation per resigned or agreed game (in the browser).
- A static lookup table built once from the Lichess database (or Maia-2).

**Reliability:**
- **Sample size is good.** Resignations are frequent at 1800+. The owner has 460 rapid and 103 blitz resignations, so rates have tight intervals (Wilson CI: about ±5 percentage points at n = 400).
- **Noise sources:**
  - **Evaluation choice.** Resigned positions often contain a deep forced line, and a shallow eval may call them "equal". Use enough depth, and treat |eval| < 1.0 together with a mate-in-N found at higher depth as lost.
  - **Calibration.** The table must be conditioned on rating *and* clock, otherwise every bullet resignation looks premature.
  - **Selection.** Opponents' resignations are only those positions in which *they* chose to resign, so the peer baseline compares resigning thresholds, not positions.
- **Research:** in a Lichess sample, higher skill and stronger opponents were associated with a lower hazard of resigning. A history of quitting raised the chance of later quitting, but a very recent quit lowered it ([Purohit & Srivastava 2026, Cognitive Science](https://doi.org/10.1111/cogs.70193), [PDF](https://www.cgs.iitk.ac.in/user/nsrivast/platipus-lab/publications/2026-metacognitive-appraisal-quitting.pdf)). That paper confirms resignation is measurable from game records but does not estimate *premature* resignation. **No published estimate of premature-resignation rates was found.**
- **Pilot on the product owner's data** (engine-free proxy only):

| | Rapid | Blitz | Bullet |
|---|---|---|---|
| His resignations | 460 | 103 | 63 |
| Median material at his resignation | −1 | −2 | −6 |
| Share of his resignations with material ≥ −1 | **53%** | 42% | 6% |
| Median material when *opponents* resigned to him | −3 | −3 | −7 |
| Share of opponents' resignations with material ≥ −1 | 36% | 38% | 18% |

- **Pilot reading:** in rapid he resigns at a smaller material deficit than his opponents do. This is a hypothesis to check with the engine: positions with level material are often lost to a mating attack or a forced tactic. Agreed draws: 41 in rapid, 2 in blitz, 0 in bullet, which is too few for an individual draw finding.

**Effort:**
- **M** overall.
- Browser: Stockfish WASM, one eval per resigned or agreed game. 500 games at about 1 s each is roughly 10 minutes, run in the background.
- Offline, once: a Python script that builds the lookup table from a few months of the Lichess database.
- Insights service: store `E_res`, compute rates and the peer baseline.
- The material proxy is **S** and needs no engine.

**Prior work:**
- chess.com Insights shows wins and losses *by method*, including resignation counts ([help](https://support.chess.com/en/articles/8708925-what-is-insights-on-chess-com)). Game Review shows the eval of one game.
- [Lichess Insights](https://github.com/lichess-org/lila/blob/master/modules/insight/src/main/InsightDimension.scala) has a "Game termination" dimension (counts only).
- Aimchess has "resourcefulness" and "advantage capitalization" scores ([aimchess.com](https://aimchess.com)), which are about play in worse or better positions, not the decision to resign.
- Not found: any tool that measures the quality of resignation and draw decisions against a rating- and clock-conditioned human baseline.

**Why it's not engine review:**
- The engine is only an input. The output is a *decision habit* ("you resign positions where 2300 players still score 22% on average, more often than your opponents do"), aggregated over hundreds of games and compared with human peers, not with Stockfish.
- Game Review never asks whether you should have resigned.

**Training link:**
- **Rule:** "In blitz and rapid, do not resign while the opponent has less than 30 s or your expected score is above 15%; play 5 more moves." Also: "Before agreeing a draw, check the clock difference."
- **Practice:** play out the player's own prematurely resigned positions against Maia at the opponent's rating, to show that they were holdable.
- **Measure:** premature-resignation rate and points given away per 100 games, before vs after, plus the rate of saved points in games that went on past a "resign-worthy" moment.

**Verdict:** **Later.** It is the first post-MVP candidate in this area. It is novel, the sample sizes are good, and it is directly actionable for strong players. It needs the browser engine and the offline lookup table, which are too much for the 24 Nov deadline. The engine-free material proxy may appear in the MVP only as a clearly labelled hint.

**Sources:**
- [chess.com Published Data API (result codes, `fen`)](https://www.chess.com/news/view/published-data-api)
- [Lichess database](https://database.lichess.org/)
- [Maia-2 paper](https://arxiv.org/abs/2409.20553) and [repo](https://github.com/CSSLab/maia2)
- [Lichess accuracy / Win%](https://lichess.org/page/accuracy)
- [Chess Engine Lab: evaluation, clock and score](https://chessenginelab.substack.com/p/evaluation-time-score)
- [Purohit & Srivastava 2026](https://doi.org/10.1111/cogs.70193)
