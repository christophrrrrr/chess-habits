# Conversion and defence profile

**Question:** When you reach a winning position, how many points do you drop compared with what that position is worth for a player of your level and time control, and how do you drop them? And the mirror question: how many points do you save from lost positions?

**What to measure:**

All evals are converted to win% for the side to move with the Lichess formula `W = 50 + 50 * (2 / (1 + exp(-0.00368208 * cp)) - 1)` ([Lichess accuracy page](https://lichess.org/page/accuracy)). The coefficient was fitted on positions from 2300+ rapid games ([lila PR 11148](https://github.com/lichess-org/lila/pull/11148)), so `W/100` is roughly the expected score of a strong rapid player. +2.00 is W ≈ 68 and +3.00 is W ≈ 75.

1. **Winning entry:** the first own move after which `W_after >= 75` holds for 2 consecutive own moves (filters out mid-exchange spikes). Record `W_entry`, ply, phase, own and opponent clock.
2. **Lost entry:** the first own move after which `W_after <= 25` for 2 consecutive own moves.
3. **Headline metrics per time-control group:**
   - `conversion_rate = wins / winning entries`.
   - `conversion_residual = mean(score - E[score | entry])`, where score is 1 / 0.5 / 0. It shows the points dropped per winning game against expectation.
   - `save_rate = (draws + wins) / lost entries`.
   - `save_residual = mean(score - E[score | entry])`.
4. **Expected score `E[score | entry]`:**
   - v1: `W_entry / 100`.
   - v2: a logistic model per time control fitted on [Lichess database](https://database.lichess.org/) games with `[%eval]` and `[%clk]` (about 6% of games have evals) in the player's rating band. Inputs: eval, own clock share, opponent clock share, total material, increment.
   - The clock inputs matter most in bullet, where +3 with 4 s left is not +3 with 40 s.
5. **Failure attribution** (for failed conversions and collapsed defences): find the own moves that carried the drop, meaning the moves whose WPL sums to ≥ 70% of `W_entry - W_lowest`. Tag each with:
   - its mistake class from [game-mistake-taxonomy.md](game-mistake-taxonomy.md);
   - phase;
   - clock bucket;
   - `single-blow` (one move ≥ 70% of the drop) or `slow` (drift).

   Report the distribution, for example "62% of your blown wins in blitz come from one move under 10% clock".
6. **Side metrics:**
   - `conversion_speed`: own moves from entry to `W >= 95` or game end, compared with the own median.
   - `flag_while_winning`: losses on time with `W_after >= 75` at the last own move.
   - `early_resignation`: resignations with `W >= 20` at the last own move. This only applies to positions resigned by the player.
   - `collapse_rate`: worse-but-holdable positions (W 25–45) that drop to ≤ 10 within 3 own moves.

**Data needed:** chess.com PGN plus `[%clk]` and game result/termination (`white.result` / `black.result` codes such as `win`, `resigned`, `timeout`, `agreed`, `repetition`; see the [Published-Data API](https://www.chess.com/news/view/published-data-api)). Single-PV engine evals for every ply are enough. Only the attribution step needs the taxonomy's extra probes.

**Reliability:**
- **Pilot (owner, 40 random games per time control, Stockfish 19 lite WASM at 100k nodes):**

  | | rapid | blitz | bullet |
  |---|---|---|---|
  | games with winning entry (W ≥ 75 twice) | 13 (32%) | 25 (62%) | 21 (52%) |
  | converted | 69% | 68% | 57% |
  | mean `score - W_entry/100` | −0.17 | −0.13 | −0.28 |
  | games with lost entry (W ≤ 25 twice) | 23 (57%) | 23 (57%) | 28 (70%) |
  | saved (draw or win) | 13% | 30% | 32% |

  The samples are tiny. The point is the method and the frequencies, not a finding. Even so, the negative residuals show that v1 (W/100 from a rapid-calibrated curve) over-promises in fast games. That supports the clock-aware v2 expectation. The residual is also negative in rapid, which points to a second bias: **threshold-crossing selection**. Entering at the first time W crosses 75 picks positions whose eval is noisily high, and the true eval then regresses back toward 50. A baseline is only valid if it uses the *same* entry rule on population games. Comparing against plain W/100 is not enough.
- **Engine-free proxy over all 2,642 games:** a stable ≥ 3-pawn material lead (held for 4 plies) occurs in 21% of rapid games and 37% of bullet games. Those games were won 77% (rapid) and 68% (bullet) of the time. Engine-based entries are more frequent, because positional advantages count too.
- **Sample size:**
  - At about 30 winning entries per 100 games, a 95% Wilson CI of ±10 points on a 75% conversion rate needs n ≈ 72 entries, which is about **250 games per time-control group**.
  - The residual has an SD of about 0.4 per game, so its SE at n = 72 is about 0.05.
  - Splits by phase or clock bucket need roughly 3× more.
  - Shrink small cells toward the player's overall rate (beta-binomial prior worth about 20 entries).
- **Noise:**
  - Outcomes depend on the opponent. Control for the rating difference.
  - Bullet and blitz outcomes are dominated by the clock, so the v1 expectation (W only) will flag bullet "failures" that are really clock losses. That is why v2 and `flag_while_winning` exist.
  - Low-node evals are noisier in complex positions but rarely move a position across the 75/25 thresholds for 2 consecutive moves.

**Effort:** S for headline rates with v1 expectation (runs on single-PV evals, in **insights**). M for the v2 expectation model, which needs an offline fit on a Lichess dump and is stored as a small coefficient table. M for attribution, which depends on the taxonomy.

**Prior work:**
- **Aimchess "Advantage capitalization"** ("When you get better positions are you able to convert those into wins?") and **"Resourcefulness"** ("Can you find counter-play even when you're in worse positions?"), with an "Advantage Capitalization Trainer" ([aimchess.com](https://aimchess.com)). One public report example reads "In 20 games you had advantage 3+, 14 of them you won (70%)". That text was seen in the search index for [an Aimchess public report](https://aimchess.com/reports/public/ch/jjungle); the page is script-rendered and was not verified directly. **The basic conversion rate already exists.**
- **Audit Chess "Blown Wins"**: "Every position where you had a decisive advantage and lost it", bucketed by opening, middlegame and endgame ([auditchess.com](https://www.auditchess.com/)).
- **ChessBase Style Report "Endgame Skill"** includes "resistance when materially behind" and "converting material advantages", against GM averages ([criteria](https://help.chessbase.com/CBase/18/Eng/criteria_of_the_style_report.htm)).
- **Lichess Insights** has an `eval` dimension with 11 buckets, so ACPL or accuracy *per move* when winning is visible ([InsightRange.scala](https://github.com/lichess-org/lila/blob/master/modules/insight/src/main/InsightRange.scala)), but not outcome conversion.
- chess.com Insights "Game Shapes" groups games by eval-curve shape ([help](https://support.chess.com/en/articles/8708925-what-is-insights)). Its exact definition is not public.

**Why it's not engine review:** Game Review marks the blunder in one blown game. The conversion *rate* alone does **not** pass the vision test, since Aimchess and Audit Chess show it. What passes is the rest:
- the **expectation-adjusted residual** (points dropped against what the position, clock and level promise);
- the **cause breakdown** of failures (single blow or drift, which mistake class, which clock state);
- the time-control-specific `flag_while_winning` and `early_resignation`.

Headline rates are kept as context only.

**Training link:**
- Failures dominated by `slow` attribution: practise converting won positions against an engine from your own entry positions. Aimchess offers this kind of replay, so Chess Habits uses the player's own entry positions and tracks the residual.
- `single-blow` under low clock: practise safe-move habits and time budgeting when winning.
- High `early_resignation`: a simple behavioural rule ("play on while W ≥ 20 and the opponent has under 30 s").
- Improvement: the residual on new games against the pre-training residual, using the same expectation model.

**Verdict:** **MVP** (headline rates plus residual v1, and `flag_while_winning`). It is cheap, needs only single-PV evals, is easy to explain, and gives the UI a first "you vs. expectation" finding. Attribution and the v2 expectation follow after the course.
