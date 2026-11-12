# E3: Do the MVP clock cards survive their confounds?

**Status:** run on 2026-11-12 on real chess.com data. Scripts: [experiments/e3_clock_confounds/](../../../experiments/e3_clock_confounds/).

**Short answer:** Mostly yes. (1) Final material ≥ +3 is a **precise** sign of "winning" in a flag loss (precision 0.96), but it **misses half** of the flag losses the engine calls winning (recall 0.48). The MVP card may use it as a lower bound ("at least N"). (2) For the owner, the score gap between games with and without time trouble does not shrink at all when the position at move 20, its sharpness and the rating gap are controlled (ratio 1.02-1.08 in all three time classes, CIs exclude 0). The cost is carried by **self-inflicted** time trouble. Other players show smaller or no costs, so it is personal. (3) The 0.1 s premove detector works: exact 0.1 s move times are 5-40× more common than 0.2 s, except for one player who never premoves.

## Hypothesis

From [shortlist.md](../shortlist.md) section 8 (E3): final material is a good proxy for "winning" in flag losses. The score gap between games with and without time trouble partly survives after controlling for the position at move 20 and its sharpness, so the clock card may state more than an association.

Pass: (a) precision ≥ 0.85 for "winning", otherwise the MVP uses the one-eval version; (b) the time-trouble coefficient keeps ≥ 50% of its raw size with a CI excluding 0, otherwise the card shows rates and onset only.

## Data

Owner (`chrisaxm`) and the five E2 players (P1-P5, chess.com titled lists, see [e2-after-loss.md](e2-after-loss.md)), fetched serially from the [chess.com Published-Data API](https://www.chess.com/news/view/published-data-api).

- **Flag games:** every rated live game lost or won on time (`timeout` in the result codes): owner all 564 (273 lost, 291 won); others the latest 150 each (lost 238, won 426). 1,228 games, 2,456 engine positions.
- **Time-trouble model:** latest rated games reaching own move 20: owner rapid 600, blitz 254, bullet 600; P1 blitz 300, P3 rapid 300, P3 blitz 300 (P1 rapid had only 5 time-trouble games in 300, so it was skipped). 15,912 positions.
- **Premoves:** every own move time of all six players (14,000-230,000 moves per player and time class).

## Method

1. **Material vs engine.** Final position and the position 10 own moves before the end. Material from the player's view (P=1, N=B=3, R=5, Q=9): winning ≥ +3, level −2..+2, losing ≤ −3. Stockfish 19 at 1M nodes, MultiPV 1, Win% from the [Lichess formula](https://lichess.org/page/accuracy): winning ≥ 75, level 25-75, losing ≤ 25. Precision = P(engine winning | material winning); recall = P(material winning | engine winning). The mirror for won-on-time games uses "losing". Wilson 95% intervals. A "stable" variant also requires the same material bucket 2 plies earlier, to drop mid-exchange snapshots.
2. **Time trouble** as in [clock-time-trouble.md](../clock-time-trouble.md): clock after an own move below 10% of `T_est = base + 40 × inc` with ≥ 5 own moves still to play. **Self-inflicted** = the opponent had more clock at that moment.
3. **Position controls.** Stockfish 19, 100k nodes, MultiPV 2 at own moves 15-20 (shared cache with E2). `W_move20` = best-move Win% before own move 20 (player's view); sharpness = mean `C_gap = W(best) − W(2nd)` over moves 15-20; rating gap = opponent's reconstructed pre-game rating − `R_skill` (E2 definition).
4. **Model** (fractional logit, score 1 / 0.5 / 0), per player and time class:
   - raw: `score ~ tt`;
   - main: `score ~ tt + rating_diff + W_move20 + sharpness`;
   - as specified: `score ~ tt + self_inflicted + rating_diff + W_move20 + sharpness`. With the self-inflicted term in, the `tt` coefficient means "time trouble that was **not** self-inflicted", so the main model (without it) is the one compared with the raw coefficient.
   - Game bootstrap, 1,000 resamples; the ratio main/raw is computed within each resample.
5. **Premove detector.** Share of own move times (own move 1 dropped) at exactly 0.1, 0.2 and 0.3 s. chess.com charges exactly 0.1 s per premove ([chess.com help](https://support.chess.com/en/articles/8562432-what-are-pre-moves-and-how-do-they-work)).

## Results

### 1. Material proxy vs engine

| Games | n | Material says winning | Engine says winning | Both | **Precision** | Recall |
|---|---|---|---|---|---|---|
| Lost on time, all players | 511 | 75 | 150 | 72 | **0.96** [0.89, 0.99] | 0.48 [0.40, 0.56] |
| - bullet | 264 | 55 | 97 | 53 | 0.96 [0.88, 0.99] | 0.55 [0.45, 0.64] |
| - blitz | 178 | 12 | 33 | 11 | 0.92 [0.65, 0.99] | 0.33 [0.20, 0.50] |
| - rapid | 69 | 8 | 20 | 8 | 1.00 [0.68, 1.00] | 0.40 [0.22, 0.61] |
| - owner only | 273 | 52 | 94 | 50 | 0.96 [0.87, 0.99] | 0.53 [0.43, 0.63] |
| Won on time ("losing"), all players | 717 | 95 | 161 | 87 | **0.92** [0.84, 0.96] | 0.54 [0.46, 0.62] |
| - owner only | 291 | 38 | 61 | 34 | 0.89 [0.76, 0.96] | 0.56 [0.43, 0.67] |

Confusion for lost-on-time games (rows material, columns engine): winning → 72 winning / 2 level / 1 losing; level → 71 / 105 / 6; losing → 7 / 90 / 157. Most misses are flag losses with level material where the engine sees a winning position. The "stable" variant did not help (precision 0.95, recall 0.41). Ten own moves before the flag, the engine already called 159 of the 511 lost-on-time positions winning (vs 150 at the end).

Owner in numbers: 273 games lost on time, of them **52 with ≥ +3 material but 94 winning by the engine**; 291 won on time, 38 while ≤ −3 but 61 losing by the engine. Bullet alone: 41 vs 70 of 199. Net clock points over the owner's 2,290 rated live games: −14 by material, −33 by engine.

### 2. Does the time-trouble gap survive position controls?

Fractional-logit coefficient of entering time trouble (95% game-bootstrap CI):

| Player, class | Games (tt) | Score with / without tt | W at move 20, tt / no tt | Raw | + rating gap | **Main (+ W20 + sharpness)** | **Main / raw** |
|---|---|---|---|---|---|---|---|
| owner rapid | 600 (124) | 0.41 / 0.56 | 52.8 / 52.5 | −0.59 [−0.99, −0.21] | −0.55 | **−0.61** [−1.07, −0.17] | **1.04** [0.63, 1.41] |
| owner blitz | 254 (44) | 0.34 / 0.61 | 55.4 / 52.4 | −1.10 [−1.74, −0.50] | −1.01 | **−1.13** [−1.97, −0.43] | **1.02** [0.71, 1.38] |
| owner bullet | 600 (152) | 0.32 / 0.54 | 57.6 / 56.8 | −0.92 [−1.31, −0.56] | −0.89 | **−0.99** [−1.45, −0.60] | **1.08** [0.94, 1.27] |
| P1 blitz | 300 (61) | 0.56 / 0.52 | 52.7 / 54.5 | +0.14 [−0.38, +0.68] | +0.16 | +0.22 [−0.41, +0.91] | undefined (raw ≈ 0) |
| P3 rapid | 300 (42) | 0.50 / 0.63 | 51.6 / 53.5 | −0.52 [−1.14, +0.14] | −0.41 | −0.50 [−1.23, +0.21] | 0.98 [−1.0, 2.3] |
| P3 blitz | 300 (90) | 0.54 / 0.61 | 52.5 / 56.7 | −0.28 [−0.77, +0.21] | −0.25 | −0.11 [−0.65, +0.45] | 0.40 [−7, 5] |

The owner's games that later enter time trouble were **not** worse at move 20 (52.8% vs 52.5% in rapid) and not sharper (mean C_gap 5.9 vs 6.2). W_move20 itself predicts the score strongly (owner rapid +0.36 logit per 10 Win% points [0.26, 0.46]), so the control works; it just does not explain the time-trouble gap.

**Self-inflicted vs mutual time trouble** (specified model, owner): rapid: not-self-inflicted `tt` +0.57 [−0.22, +1.43], extra for self-inflicted −1.68 [−2.71, −0.84]; bullet: +0.72 [−0.06, +1.57] and −2.25 [−3.28, −1.37]. Time trouble costs the owner points when he alone is short of time. When both are short, there is no measurable cost. (Blitz and the other players have too few non-self-inflicted entries for stable estimates.)

### 3. Premove detector

| Player | Bullet 0.1 s / 0.2 s / 0.3 s | Blitz | Rapid |
|---|---|---|---|
| owner | 9.8% / 1.8% / 2.7% | 6.0% / 0.6% / 1.8% | 5.1% / 0.35% / 1.2% |
| P1 | 11.8 / 1.4 / 3.1 | 7.2 / 0.4 / 1.2 | 3.2 / 0.08 / 0.17 |
| P2 | 17.3 / 2.2 / 5.5 | 7.5 / 0.6 / 1.8 | 1.0 / 0.09 / 0.18 |
| P3 | 13.2 / 1.4 / 1.7 | 7.1 / 0.5 / 0.9 | 4.2 / 0.17 / 0.31 |
| P4 | 8.9 / 1.5 / 2.0 | 3.0 / 0.4 / 0.5 | 0.8 / 0.12 / 0.10 |
| P5 | 0.24 / 0.24 / 0.48 (829 moves) | 0.0 / 0.0 / 0.06 | 0.0 / 0.0 / 0.02 |

The spike at exactly 0.1 s is 5-40× the 0.2 s level for everyone who premoves. P5 shows no spike at all (probably premoves switched off), which is what a working detector should show. The 0.2 s bin is lower than 0.3 s for most players, so a "≤ 0.2 s" rule would mix premoves with real fast moves; use exactly 0.1 s.

### Pass / fail

| Criterion | Result |
|---|---|
| (a) material precision for "winning" ≥ 0.85 | **Pass:** 0.96 [0.89, 0.99] (lost on time), 0.92 [0.84, 0.96] (won on time, "losing"). But recall is only 0.48-0.54. |
| (b) time-trouble coefficient keeps ≥ 50% with CI excluding 0 | **Pass for the owner** in rapid, blitz and bullet (ratios 1.02-1.08, all CIs exclude 0). Not testable or not significant for P1 and P3 (no raw gap to keep). |

## What it means for Kiebitz

1. **Flag-loss card:** the material proxy can ship in the MVP, worded as a lower bound: "lost on time with at least 3 points of material up: 52 games (the engine would count about twice as many)". The stretch item (one browser eval of the final position) is worth it: it nearly doubles the count (owner: 52 → 94) with almost no false positives. Net clock points by engine: −33 for the owner over 2,290 games.
2. **Time-trouble card may state a cost, for players where it holds, with care.** For the owner the gap is not explained by the position at move 20, sharpness or rating gap. The card can say "games where you got into time trouble scored 15-27 points lower per 100 games, and this is not because you were already worse at move 20". It should still not say "caused", because the position between move 20 and the onset is not controlled (see caveats).
3. **The decomposition is the finding:** self-inflicted time trouble carries the cost; mutual scrambles do not. That supports the shortlist's "self-inflicted share" and "where the time went" metrics as the core of card 2, and it is new relative to every tool in the gap map.
4. **It is personal.** P1 shows no time-trouble cost in blitz (+0.14), P3 a smaller, uncertain one. So "time trouble hurts you" is a per-player finding, not a universal truth. That is what Kiebitz wants.
5. **Premove detector:** use exactly 0.1 s. It is chess.com-specific and fails silently for players with premoves off (P5), so show the premove card only when the 0.1 s spike exists.

## Caveats

- Controls are measured at move 20. Time-trouble onset usually comes later, and a position that turns bad between move 20 and the onset can cause both long thinks and the loss. A stricter test compares positions at the onset move with matched games at the same move number; not done here.
- Selection by game length: a game must last ≥ 5 own moves after the onset to count as time trouble, and short wins (opponent collapses early) cannot enter it. This favours the "no time trouble" group.
- "Self-inflicted" is partly mechanical: being behind on the clock raises the flag risk directly.
- 100k nodes for W_move20 and sharpness, 1M for flag positions, no re-verification. Final positions in flag games can be mid-tactic; the engine handles that, material does not.
- Fractional logit on 1 / 0.5 / 0 treats a draw as half a win; few draws in these samples.
- The comparison players are a small titled sample, and only 300 games each.

## Sources

- chess.com Published-Data API: https://www.chess.com/news/view/published-data-api
- chess.com help, premoves cost 0.1 s: https://support.chess.com/en/articles/8562432-what-are-pre-moves-and-how-do-they-work
- Lichess Win% formula: https://lichess.org/page/accuracy
- Stockfish 19: https://github.com/official-stockfish/Stockfish/releases/tag/sf_19
- Kiebitz notes: [clock-flag-losses.md](../clock-flag-losses.md), [clock-time-trouble.md](../clock-time-trouble.md), [clock-bullet-premoves.md](../clock-bullet-premoves.md)
