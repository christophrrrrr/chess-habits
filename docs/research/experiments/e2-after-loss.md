# E2: After a loss - results vs move quality vs behaviour

**Status:** run on 2026-11-12 on real chess.com data. Scripts: [experiments/e2_after_loss/](../../../experiments/e2_after_loss/).

**Short answer:** Behaviour changes after a loss far more reliably than results do. Every player with enough data starts the next game faster after a loss (4 of 5 with a finding, up to +39 percentage points within 60 s). Results after a loss stay within about ±20-40 Elo for the two players with thousands of games. Move quality is **not** 2-3× more precise per game in standardised units (fail a). It is about 2-3× tighter in Elo-equivalent terms on the same games, but the outcome contrast can use every game while quality is limited by engine time, so most of that gain disappears. The decision rule raises a false finding on 9-13% of shuffled pages, which is what BH at q = 0.10 promises, but just above the 10% target (borderline fail b).

## Hypothesis

From [shortlist.md](../shortlist.md) section 8 (E2): for strong players, after-loss effects on results cannot be detected per player (CIs of ±40-80 Elo). Move quality and behaviour (requeue speed, time used on moves 10-25) are 2-3× more precise. The decision rule (minimum n, CI, BH) almost never raises a finding on shuffled data.

Pass: (a) the quality contrast's standardised CI is at most half as wide as the outcome contrast's; (b) the shuffled-label finding rate is at most 10% per player.

## Data

Full chess.com live history (bullet, blitz, rapid) of the owner and 5 public titled players (FM/CM/NM lists, seeded random draw, rapid 2000-2500, ≥ 1,000 live games, see [select_players.py](../../../experiments/fetch_data/select_players.py)), fetched serially from the [Published-Data API](https://www.chess.com/news/view/published-data-api).

| Player | Rated live games | Bullet / blitz / rapid |
|---|---|---|
| owner | 2,290 | 757 / 314 / 1,219 |
| P1 (NM) | 12,183 | 6,186 / 4,692 / 1,305 |
| P2 (NM) | 2,977 | 993 / 1,407 / 577 |
| P3 (CM) | 12,633 | 4,140 / 6,558 / 1,935 |
| P4 (CM) | 4,657 | 1,225 / 2,819 / 613 |
| P5 (NM) | 1,312 | - / 418 / 868 (few back-to-back games) |

Move-quality sample (engine): owner rapid 392 games (196 after a loss, 196 after a win), owner bullet 234, P1 rapid 239, P3 rapid 240; 26,814 positions in total (about 21 min on 7 cores at 100k nodes).

## Method

1. **Residual.** Pre-game rating = post-game rating of the previous rated game in the same time class (the API documents `rating` as "the player's rating after the game finished", [API docs](https://www.chess.com/news/view/published-data-api)). `R_skill` = median pre-game rating over ±25 neighbouring games, the game itself excluded. Opponent's pre-game rating approximated as `opp_post + (my_post − my_pre)` (symmetric rating change; chess.com uses Glicko, so this is approximate). `E = 1/(1 + 10^((R_opp − R_skill)/400))`, residual `S − E`, shown in Elo via `1 / (mean(E(1−E)) · ln10/400)` (≈ 720-785 Elo per point of score here).
2. **Sessions.** New session when the next game starts more than 30 min after the previous one ended (start from the PGN `UTCDate`/`UTCTime`, end from `end_time`). "After a loss/win" = the previous game in the same session was lost/won. Robustness: the start-to-start rule of [Gee et al. 2025](https://arxiv.org/html/2503.21713v2) (5 min bullet, 7 min blitz; not defined for rapid).
3. **Behaviour.** Requeue: next game started ≤ 60 s after the previous one ended. Time use: share of `T_est` spent on own moves 10-25 (games reaching move 25).
4. **Quality.** Stockfish 19, 100k nodes, MultiPV 2, own moves 8-40 with clock ≥ 10% of `T_est`: error rate (`ΔW ≥ 10`), mean ΔW per game, and the share of critical positions (`C_gap ≥ 10` with best-move Win% 10-90) to check that after-loss games are not just sharper. Random sample of up to 200 (owner rapid), 120 (others) games per group.
5. **Intervals.** Session-cluster bootstrap, 2,000 resamples. MDE = 2.8 · SD · √(1/n₁ + 1/n₂).
6. **Decision rule** (as planned for the MVP): per player, 9 tests (outcome, requeue, time use × bullet/blitz/rapid); a finding needs ≥ 100 games in the smaller group, a 95% cluster-robust CI excluding 0, and Benjamini-Hochberg at q = 0.10 across the 9 tests.
7. **False-positive check.** 1,000 times per player: shuffle the previous-result labels in session blocks (sessions permuted, order inside a session kept), rerun the full rule, count pages with at least one finding.
8. **Comparing precision.** (i) As specified: CI width divided by the per-game SD (Cohen's d units), on the same games. (ii) Added, because (i) is nearly equal by construction at equal n: an Elo-equivalent of the quality contrast, `slope(residual ~ mean ΔW per game) × (ΔW after loss − ΔW after win) × Elo factor`, with the slope re-estimated in every bootstrap draw.

## Results

### Results and behaviour after a loss (after-loss minus after-win, 95% CI)

| Player, time class | Games L / W | Result (Elo) | MDE (Elo) | Requeue ≤ 60 s, L vs W | Time use moves 10-25, L vs W |
|---|---|---|---|---|---|
| owner bullet | 315 / 330 | **−71** [−120, −20] | 76 | 84% vs 90%: −5.9 pp [−12.5, −0.2] | 48.5% vs 47.7% |
| owner blitz | 129 / 136 | +69 [−8, +156] | 121 | 76% vs 66%: +9.8 pp [−0.8, +19.5] | 42.2% vs 43.0% |
| owner rapid | 269 / 304 | **+63** [+17, +113] | 78 | **65% vs 36%: +28.9 pp** [21.2, 36.3] | **34.0% vs 38.3%** [−7.1, −1.5] |
| P1 bullet | 2,644 / 2,601 | −4 [−22, +16] | 27 | **94% vs 86%: +7.3** [5.6, 9.0] | 43.6% vs 43.5% |
| P1 blitz | 1,750 / 1,841 | −19 [−43, +5] | 33 | **83% vs 76%: +7.6** [5.0, 10.1] | 40.7% vs 40.7% |
| P1 rapid | 323 / 393 | +19 [−36, +70] | 75 | **73% vs 55%: +17.8** [10.9, 25.0] | 22.6% vs 23.1% |
| P2 bullet | 383 / 449 | −35 [−89, +18] | 74 | 87% vs 83%: +4.6 [−0.6, 10.3] | 39.4% vs 39.6% |
| P2 blitz | 486 / 572 | −9 [−48, +31] | 61 | 79% vs 76%: +3.7 [−1.7, 8.8] | 36.5% vs 37.4% |
| P2 rapid | 133 / 189 | **−119** [−198, −30] | 113 | 73% vs 63%: +10.0 [−0.2, 20.0] | 26.0% vs 24.7% |
| P3 bullet | 1,782 / 1,871 | −4 [−28, +20] | 32 | **98% vs 94%: +4.3** [2.8, 5.9] | 50.1% vs 49.4% |
| P3 blitz | 2,798 / 2,362 | −15 [−33, +4] | 27 | **96% vs 79%: +17.5** [15.5, 19.5] | **43.7% vs 45.3%** [−2.5, −0.6] |
| P3 rapid | 640 / 628 | −14 [−54, +25] | 55 | **90% vs 50%: +39.4** [34.2, 44.4] | 29.3% vs 30.2% |
| P4 bullet | 495 / 547 | −22 [−61, +18] | 59 | **92% vs 88%: +3.9** [0.7, 7.2] | 39.3% vs 39.2% |
| P4 blitz | 926 / 1,167 | +13 [−16, +44] | 42 | **79% vs 69%: +10.9** [6.7, 15.3] | **38.6% vs 40.4%** [−2.9, −0.6] |
| P4 rapid | 105 / 255 | −11 [−92, +72] | 111 | **65% vs 31%: +33.8** [21.4, 45.0] | **23.0% vs 27.9%** [−7.8, −1.9] |
| P5 blitz / rapid | 24 / 171, 12 / 218 | not enough data | 309 / 872 | - | - |

Bold = passes the full decision rule (or, for time use, CI excludes 0). The start-to-start session rule gives the same picture: owner bullet −76 [−126, −18], P1 bullet −8, P3 blitz −16; only the owner's small blitz sample moves (+149 [48, 274], 85 / 67 games).

![Results after a loss vs after a win](img/e2-outcome-after-loss.png)

### Move quality in games right after a loss vs after a win (L minus W, 95% CI)

| Group (games L / W) | Error rate (pp) | Mean ΔW per game | Critical share (pp) | Result in the same games (Elo) | d-units CI width: quality vs result | Elo-equivalent of quality contrast |
|---|---|---|---|---|---|---|
| owner rapid (196 / 196) | −1.9 [−4.5, +0.3] | −0.47 [−1.20, +0.25] | +0.9 [−1.3, +3.1] | +68 [+4, +127] | 0.39 vs 0.37 | +14 [−7, +37] |
| owner bullet (117 / 117) | +1.4 [−1.7, +4.6] | −0.05 [−0.89, +0.82] | −0.1 [−3.7, +3.5] | −34 [−120, +60] | 0.54 vs 0.52 | +2 [−32, +36] |
| P1 rapid (120 / 119) | −0.6 [−3.9, +2.7] | −0.40 [−1.31, +0.49] | −1.6 [−4.9, +1.7] | −19 [−101, +66] | 0.50 vs 0.48 | +20 [−22, +67] |
| P3 rapid (120 / 120) | +0.2 [−1.6, +2.1] | +0.18 [−0.23, +0.61] | −3.1 [−5.9, −0.0] | −6 [−91, +76] | 0.49 vs 0.48 | −14 [−50, +18] |

After-loss games are not sharper (critical share unchanged or lower), so "riskier play after a loss" does not show up here. No quality contrast excludes 0.

### False-positive check (1,000 shuffles per player)

| Player | Pages with ≥ 1 finding (family-wise) | Highest single-test rate |
|---|---|---|
| owner | 9.3% | 2.3% |
| P1 | 10.8% | 2.0% |
| P2 | 12.6% | 3.1% |
| P3 | 11.0% | 1.6% |
| P4 | 11.2% | 1.9% |
| P5 | 0% (no test reaches n = 100) | 0% |

Monte Carlo SE ≈ 1 percentage point. Under a complete null, BH controls the family-wise rate at q, so about 10% is the expected value.

### Pass / fail

| Criterion | Result |
|---|---|
| (a) quality CI ≤ half the outcome CI (standardised) | **Fail.** In d units the widths are equal at equal n (0.39 vs 0.37 for owner rapid; ratio 1.0-1.05 everywhere). In Elo-equivalent terms quality is 1.9-2.8× tighter on the *same* games (CI width owner rapid 44 vs 123 Elo, owner bullet 68 vs 180, P1 90 vs 167, P3 68 vs 167), but only 1.2-2.2× tighter than the outcome contrast on *all* games of that time class (96, 100, 106, 79 Elo), which costs no engine time. |
| (b) shuffled finding rate ≤ 10% per player | **Borderline fail:** 9.3-12.6% for the five players with enough data. The rule behaves as designed (≈ q); it is the target that needs q = 0.05. |

## What it means for Kiebitz

1. **Lead the after-loss card with behaviour, not results.** Requeue speed after a loss is a finding for 4 of 5 players and is exact (timestamps only). But it is nearly universal, so it is not a personal discovery. Show the player's size against other players (+18 to +39 pp in rapid for P1, P3, P4 and the owner) and pair it with "and did it cost you?" (results and quality). For the owner, rapid after-loss games are faster (−4.4 pp of `T_est` on moves 10-25) but not worse: residual +63 Elo, error rate −1.9 pp.
2. **Outcome tilt needs thousands of games.** P1 and P3 (4,000-6,500 games per class) show no after-loss effect beyond about 20-40 Elo (MDE 27-33). With 300-1,300 games per class the MDE is 55-120 Elo. "No effect larger than X" is the honest default answer.
3. **The owner's results:** bullet −71 Elo [−120, −20] after a loss and rapid +63 [+17, +113]. Both pass the MVP rule, in opposite directions. The bullet one supports showing the stop-loss simulator for bullet. Treat both as tentative: the rule's own false-positive rate is about 10% per page, and the earlier pilot ([psych-tilt-and-stop-loss.md](../psych-tilt-and-stop-loss.md)) had smaller values (−28 / +27) with a different rating reconstruction.
4. **Post-loss move quality is not the precision fix the shortlist expected.** Keep it as a secondary check ("faster but not worse"), not as the main metric. Card 25 should drop the "much less noisy" claim.
5. **Make the decision rule stricter before launch:** BH q = 0.05 for findings (expected family-wise false alarm ≈ 5%), label q 0.05-0.10 as "exploratory", or require the effect to hold in both halves of the history.

## Caveats

- Six players; P5 almost never plays back-to-back, so P5 adds nothing.
- The opponent's pre-game rating is approximated; the Elo curve is miscalibrated at large rating gaps ([Sonas](https://en.chessbase.com/post/the-elo-rating-system-correcting-the-expectancy-tables)). After a loss the matchmaker pairs the player with weaker opponents relative to `R_skill`, so any curve error biases after-loss vs after-win residuals. This could explain part of the owner's opposite-sign results.
- `R_skill` uses future games (±25), so it partly absorbs streaks.
- Quality used 100k nodes (no re-verification); the E1 run shows about 15% of labels near ΔW = 10 flip at 1M nodes. This adds noise to quality and is one reason it is not more precise.
- The Elo-equivalent conversion assumes results move with mean ΔW as in the cross-game slope; that slope is partly reverse causation (losing positions produce larger ΔW).
- Shuffling moves labels across time classes; that is fine for a null but makes the shuffled pages slightly different from real ones.

## Sources

- chess.com Published-Data API (post-game ratings, archives): https://www.chess.com/news/view/published-data-api
- Gee, Seese, Curley & Ward 2025, session rules and hierarchical model: https://arxiv.org/html/2503.21713v2
- Sonas on Elo expectancy: https://en.chessbase.com/post/the-elo-rating-system-correcting-the-expectancy-tables
- Kiebitz notes: [psych-tilt-and-stop-loss.md](../psych-tilt-and-stop-loss.md), [psychology-and-context.md](../psychology-and-context.md)
