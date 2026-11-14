# E1: Time spent vs criticality

**Status:** run on 2026-11-12 on real chess.com data. Scripts: [experiments/e1_time_vs_criticality/](../../../experiments/e1_time_vs_criticality/). Raw outputs stay outside the repo (see [experiments/README.md](../../../experiments/README.md)).

**Short answer:** Time does track criticality: relative move time rises with the benefit of computation ΔU (pass a). But the "missed alarm" idea is wrong in sign. In critical positions, fast moves go wrong **less** often than slow ones, for all four players, in all slices, and still after controlling for engine difficulty (fail b). Players on the same time control have nearly identical ρ(r, ΔU), so it is not a personal trait worth a card (c is met only on a secondary metric or across different time controls). Per the shortlist's kill rule, the time-vs-criticality card becomes descriptive, and slice 1 leads with the only-move find rate. A new, useful by-product: move time is a strong marker of positions the player *finds* hard, beyond what the engine says.

## Hypothesis

From [shortlist.md](../shortlist.md) section 8 (E1): per player, relative move time rises with ΔU ([Russek et al. 2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC12553403)). In critical positions, the error rate is clearly higher when the player moves fast than when they slow down. The strength of this link differs between players by more than its CI.

Pass criteria: (a) ρ(r, ΔU) > 0 with a CI excluding 0 for the owner's rapid games; (b) error rate critical & fast minus critical & not-fast has a CI excluding 0 (the hypothesis says positive), with ≥ 100 critical & fast moves; (c) at least two players have non-overlapping CIs.

## Data

| Player | Time control | Games | Eligible moves | Critical (C_gap ≥ 10) | Critical & fast |
|---|---|---|---|---|---|
| owner (`chrisaxm`, rapid 2380) | 10+0 rapid, last 300 rated | 298 | 5,489 | 712 | 284 |
| owner | 3+0 / 5+0 blitz, last 150 rated | 147 | 2,274 | 288 | 80 |
| P1 (NM, rapid 2325) | 10+0, last 150 rated | 149 | 2,469 | 275 | 91 |
| P3 (CM, rapid 2500) | 10+0, last 150 rated | 150 | 2,810 | 221 | 68 |
| P5 (NM, rapid 2145) | 15+10 (96%), last 150 rated | 127 | 915 | 112 | 28 |

Comparison players were drawn with a fixed seed from chess.com's public FM/CM/NM lists ([/pub/titled](https://www.chess.com/news/view/published-data-api)), filtered to rapid 2000-2500, ≥ 500 rapid games and active in the last 60 days ([select_players.py](../../../experiments/fetch_data/select_players.py)). They are anonymised here. Games were fetched serially from the [chess.com Published-Data API](https://www.chess.com/news/view/published-data-api) with a contact User-Agent. P5 plays 15+10, so P5 comparisons mix player and time control.

## Method

As specified in the shortlist, with the deviations marked **(dev)**.

1. **Eligible own moves:** plies 16-80; clock before the move ≥ 10% of `T_est = base + 40 × inc`; own move 1 dropped; not in check; > 3 legal moves; best-move Win% between 10 and 90; trivial recaptures removed (best move captures on the square of the opponent's last move, as in [game-decision-points.md](../game-decision-points.md)).
2. **Move time** `t = clk_prev − clk + inc` from `[%clk]`. **Relative time** `r = t / median(t)` over the player's own eligible-by-clock moves in the same time control, clock band (Lichess bands ≥ 50 / 25-50 / 10-25%) and phase (simplified: endgame ≤ 6 minor/major pieces; opening while move ≤ 12; else middlegame) **(dev: simplified phase)**. Fast = `r < 0.5`, slow = `r ≥ 2`.
3. **Engine:** official Stockfish 19 Windows build ([release sf_19](https://github.com/official-stockfish/Stockfish/releases/tag/sf_19)), 1 thread, 64 MB hash, hash cleared per position (deterministic). Depth-1 search first (move `m1`), then MultiPV 2 at 300k nodes (median depth 16). Missing values for the played move and for `m1` from `searchmoves` at 300k. Win% from the [Lichess formula](https://lichess.org/page/accuracy) `W = 50 + 50·(2/(1+e^(−0.00368208·cp)) − 1)`.
   - `C_gap = W(best) − W(2nd)`; `ΔU = W(best) − W(m1)` (Russek's ΔU uses depth 1 vs depth 15, close to our 300k); `ΔW = max(0, W(best) − W(played))`; error = `ΔW ≥ 10`.
   - **(dev)** Re-verification at **1M** nodes (not 3M) and only for `7 ≤ ΔW < 25`, to fit the ~2 h compute budget. In an 8-game pilot at 3M nodes, no move with ΔW ≥ 20 at 300k dropped below 10; the 7-25 band is where labels flip.
4. **Statistics:** game-cluster bootstrap, 2,000 resamples, 95% percentile intervals. Pairwise player differences use independent bootstrap draws. Extra (not in the spec): a logistic model `error ~ log2(r) + C_gap + ΔU + |W−50| + clock band + phase` with game-clustered SEs, to see whether the time-error link survives engine difficulty controls.

## Results

### Main metrics (95% CI)

| Group | ρ(r, ΔU) | ρ(r, C_gap) | Critical moves played fast | Error, critical & fast | Error, critical & not fast | Difference (pp) |
|---|---|---|---|---|---|---|
| owner rapid | **0.131** [0.107, 0.155] | −0.090 [−0.118, −0.062] | 39.9% [36.0, 43.5] | 8.8% [5.7, 12.3] | 26.9% [23.0, 31.1] | **−18.1** [−23.0, −13.2] |
| owner blitz | 0.085 [0.048, 0.123] | −0.010 [−0.054, 0.036] | 27.8% [22.9, 32.5] | 13.8% [5.6, 23.9] | 29.3% [23.1, 36.0] | −15.6 [−25.7, −4.5] |
| P1 rapid | 0.137 [0.097, 0.177] | −0.031 [−0.070, 0.008] | 33.1% [27.3, 39.3] | 22.0% [14.1, 30.4] | 38.0% [30.7, 45.2] | −16.1 [−26.2, −5.5] |
| P3 rapid | 0.138 [0.102, 0.179] | −0.001 [−0.038, 0.039] | 30.8% [25.2, 36.8] | 8.8% [2.9, 16.9] | 32.0% [24.3, 39.4] | −23.2 [−33.0, −12.0] |
| P5 rapid (15+10) | 0.234 [0.171, 0.296] | −0.076 [−0.146, −0.006] | 25.0% [15.9, 34.2] | 10.7% [0, 22.2] | 20.2% [12.2, 28.7] | −9.5 [−22.3, 3.5] |

![ρ(r, ΔU) per player](img/e1-rho-by-player.png)

### The owner's 2×2 matrix (rapid, 5,489 moves; middle speeds shown for completeness)

| | Fast (r < 0.5) | Middle | Slow (r ≥ 2) |
|---|---|---|---|
| **Critical** (C_gap ≥ 10) | 5.2% of moves, error 8.8%, median 1.5 s | 4.8%, 20.2%, 6.4 s | 3.0%, **37.6%**, 25.1 s |
| **Quiet** (C_gap < 3) | 14.4%, 3.7%, 1.8 s | 25.3%, 5.5%, 6.5 s | 22.8%, 11.0%, 25.5 s |

Blitz shows the same shape (critical: fast 13.8%, slow 43.6%; quiet: fast 6.3%, slow 12.2%).

### Is it just "obvious" critical positions? No.

Splitting critical positions by whether the depth-1 move already finds the answer:

| Group | Obvious (ΔU < 3): fast − not fast | Hidden (ΔU ≥ 10): fast − not fast | Odds ratio of error per doubling of r, all moves, controlled | Same, critical only |
|---|---|---|---|---|
| owner rapid | −14.1 pp [−19.1, −9.0] | −15.9 pp [−31.3, +1.2] (n = 169, 40 fast) | **1.32** [1.25, 1.40] | 1.33 [1.20, 1.48] |
| owner blitz | −11.3 [−23.0, +1.7] | −24.5 [−40.8, −6.2] (n = 86) | 1.27 [1.15, 1.40] | 1.55 [1.23, 1.94] |
| P1 rapid | −9.3 [−21.5, +2.9] | −18.8 [−44.2, +8.5] (n ≈ 77) | 1.24 [1.14, 1.35] | 1.21 [1.01, 1.46] |
| P3 rapid | −18.0 [−26.9, −8.3] | −23.5 [−53.9, +10.3] (n ≈ 53) | 1.31 [1.18, 1.44] | 1.49 [1.22, 1.83] |
| P5 rapid | −6.3 [−20.8, +8.9] | −30.0 [−50.0, −11.1] (n ≈ 21) | 1.37 [1.16, 1.60] | 1.40 [0.97, 2.02] |

Even in "hidden" critical positions, where the natural move is a mistake, fast moves are not worse. And after controlling for C_gap, ΔU, balance, clock band and phase, every doubling of relative time goes with 21-55% higher error odds. Spearman ρ(r, ΔW) is +0.16 to +0.24 for every group (owner rapid 0.239 [0.215, 0.263]).

![Error rate by relative time in critical positions](img/e1-critical-error-by-time.png)

### Between players (criterion c)

- Same time control (10+0): owner, P1 and P3 have ρ(r, ΔU) of 0.131, 0.137, 0.138; pairwise differences ≤ 0.007, all CIs overlap.
- Non-overlapping CIs exist only for: owner vs P5 on ρ(r, ΔU) (+0.103 [0.039, 0.171]) and on the critical-fast share (−14.9 pp), both confounded by P5's 15+10 time control (the owner's own blitz-vs-rapid gap is 0.046, the same direction); and owner vs P3 on ρ(r, C_gap) (−0.089 [−0.137, −0.043]). The owner moves fast in more critical positions than P3 (39.9% vs 30.8%, difference CI [2.1, 15.8] pp, but the two CIs overlap).

### Label noise and throughput

- Re-verification at 1M nodes (moves with 7 ≤ ΔW < 25): owner rapid 772 checked, 47 errors dropped below 10, 72 non-errors rose to ≥ 10; blitz 310 checked, 29 down, 30 up. About 15% of labels in that band change, in both directions. A single 300k search is not enough near the threshold.
- Critical positions per game (after the triviality filter): 2.39 (owner rapid), 1.96 (owner blitz), 1.85 (P1), 1.47 (P3), 0.88 (P5).
- Cost (native Stockfish 19, i7-9700F, 7 processes): 23 searched positions per rapid game; 1.0 s CPU per position for depth 1 + MultiPV 2 + searchmoves, 5.9 s for the 10.5% that were re-verified at 1M; 4.6 positions/s wall on 7 cores, so about 25 min for 300 rapid games. Median search depth at 300k nodes: 16. The depth-1 move equalled the best move in 48% of positions.

### Pass / fail

| Criterion | Result |
|---|---|
| (a) ρ(r, ΔU) > 0, CI excludes 0, owner rapid | **Pass:** 0.131 [0.107, 0.155] |
| (b) critical-fast error excess, CI excludes 0, ≥ 100 critical-fast moves | **Fail (reversed):** −18.1 pp [−23.0, −13.2] with 284 moves. The CI excludes 0 on the wrong side. |
| (c) two players with non-overlapping CIs | **Weak:** only on ρ(r, C_gap) (owner vs P3) and in comparisons confounded by time control. Not on the primary metric. |

## What it means for Chess Habits

1. **Drop the "missed alarm" claim.** A card that says "you lose points by moving fast in critical positions" would be false for all four players tested. Fast moves in critical positions are mostly moves the player recognised, so speed is a *consequence* of finding the move, not a cause of missing it. Observational data cannot show what a longer think would have changed.
2. **Time vs criticality as a personal trait is not supported.** ρ(r, ΔU) is real (it replicates Russek et al. per player), but players on the same time control are indistinguishable at 150-300 games. This is consistent with Russek et al., who call the Elo effect on this link "modest". It can stay as one descriptive chart on the critical-moments card, not as the flagship.
3. **Shortlist kill rule applies:** (b) fails and (c) fails on the primary metric, so slice 1 leads with the **non-trivial only-move find rate by move type** ([game-decision-points.md](../game-decision-points.md)). E1 confirms its inputs: 1.5-2.4 non-trivial critical positions per rapid game, so 300 games give 450-700 decision points.
4. **New signal worth keeping: time as "found it hard".** Relative think time predicts error beyond engine difficulty (odds ratio about 1.3 per doubling, every player). Positions where the player thought long and still erred (owner: 37.6% error in critical-slow positions) are where calculation or evaluation broke down. This could be a cheap, per-player difficulty label for drill selection before Maia-3 exists. **Speculation:** not yet tested whether these positions make better drills.
5. **Sizing for slice 1:** about 33 s of native CPU per rapid game at this budget. A browser WASM build is slower (unmeasured here), so the shortlist's "newest 100-300 games first" plan (D8) stands. ΔU needs an extra depth-1 search and searchmoves; given point 2, slice 1 can skip it. Re-verification matters (15% flips in the 7-25 band), so keep it, but only for that band.

## Caveats

- Four players, one owner. The comparison players come from chess.com's titled lists, not from a random sample of 1800-2500 players. Only 150 games each.
- P5 plays 15+10, so P5's differences are not player differences.
- The "fast" and "slow" cuts are relative to the player's own median in the same clock band and phase, using a simplified phase rule. Absolute-time cuts may behave differently.
- Engine budget: 300k nodes (depth ~16), re-verification at 1M instead of the specified 3M, and only for 7 ≤ ΔW < 25. Labels near the threshold stay noisy; the main contrast (−18 pp) is far larger than that noise.
- Move times on chess.com include network effects; irrelevant at rapid scale but not zero.
- The negative fast-vs-slow difference is an association. It does not show that thinking longer *hurts*. The most likely reading is reverse causation: players slow down when they do not see the answer.

## Sources

- Russek et al., *Cognitive Science* 2025, time allocation and ΔU: https://pmc.ncbi.nlm.nih.gov/articles/PMC12553403
- Lichess Win% formula: https://lichess.org/page/accuracy
- chess.com Published-Data API: https://www.chess.com/news/view/published-data-api
- Stockfish 19 release: https://github.com/official-stockfish/Stockfish/releases/tag/sf_19
- Chess Habits notes: [clock-time-vs-criticality.md](../clock-time-vs-criticality.md), [game-decision-points.md](../game-decision-points.md), [clock-and-time.md](../clock-and-time.md)
