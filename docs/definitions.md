# Definitions

One place for every definition the analyses use. The code follows this file; if they disagree,
the code is wrong. Background and sources: [research/shortlist.md](research/shortlist.md)
(section 2.3 resolves the contradictions between research notes).

## Games and players

| Term | Definition | Code |
|---|---|---|
| Time class | chess.com's `time_class`, except live games with `T_est ≥ 1500 s` count as **classical** (chess.com files them under rapid). Daily games are excluded from every analysis. | `GameRecord.category` |
| `T_est` | Estimated game time per player: `base + 40 × increment` (seconds). | `GameRecord.t_est` |
| Clock before own move k | Own clock after the previous own move; `base` before move 1. chess.com's `[%clk]` is the clock *after* the move, increment included, at 0.1 s resolution. | `GameRecord.clock_before` |
| Time spent on own move k | `clock_before(k) + increment − clock_after(k)` | `GameRecord.time_spent` |
| Session | Consecutive live games where the next game starts at most **30 minutes** after the previous one ended (start from the PGN `UTCDate`/`UTCTime`, end from the archive's `end_time`). | `prepare()` |
| Requeue | Starting the next game within **60 s** of the previous game's end. | `after_loss.QUICK_REQUEUE` |
| Lost / won on time | PGN `Termination` "… won on time" with the player's result loss / win. | `GameRecord.lost_on_time` |
| Final material | Player's material minus the opponent's in the final position (P=1, N=B=3, R=5, Q=9). **Winning** ≥ +3, **losing** ≤ −3, otherwise level. A lower bound for "winning": research E3 measured precision 0.96 and recall 0.48 against Stockfish. | `games.final_material` |

## Ratings and results

| Term | Definition |
|---|---|
| Post-game rating | chess.com's game `rating` fields are **after** the game (verified on real data). |
| Pre-game rating | The player's post-game rating in their previous game of the same time class. The opponent's pre-game rating is their post-game rating plus the player's rating change (close to zero-sum). |
| `R_skill` (strength) | Median pre-game rating over the 25 games before and after, in the same time class. Removes the regression-to-the-mean artefact of using the current rating. |
| Expected score | Elo formula with `R_skill` vs the opponent's pre-game rating. |
| Residual | Actual score (1 / 0.5 / 0) minus expected score. All result findings compare residuals. |
| Elo equivalent | `Δscore × 400 / (ln 10 × 0.25)` ≈ `Δscore × 695` (exact near an expected score of 0.5). |

## Clock profile

| Term | Definition |
|---|---|
| Time-trouble entry | Clock before some own move k is below **10 % of `T_est`** and the player still makes **at least 5 more moves** (so a mating finish in time trouble does not count). Games need at least 10 own moves with clock data. |
| Scramble | Same with **3 %**. |
| Onset move | First own move k with an entry. |
| Self-inflicted | At the onset move, the opponent had more time left than the player. |
| Where the time went | Time spent on own moves 2 to onset−1, split into **opening** (own moves 2–12), **spikes** (moves of at least **4×** the player's median think time on moves 13–40 for that time class) and **drain** (the rest). Each entry game is assigned the category that most exceeds the same split in calm games (moves 2 to the median onset). Shown only with ≥ 30 entry games. |
| Pace | Median clock left as a share of `T_est` after own moves 10, 20, 30 and 40, in wins vs losses (needs ≥ 10 games per cell). |
| Net clock points | `(won on time while losing + ½ won while level) − (lost on time while winning + ½ lost while level)`, per 100 games. |

## Statistics

| Rule | Value |
|---|---|
| Interval | 95 % percentile interval from a **cluster bootstrap** (2,000 resamples, fixed seed): sessions for anything about consecutive games, games otherwise. |
| Minimum detectable effect | `MDE = 2.8 × bootstrap SE` (80 % power at α = 0.05). "No effect" always means "none larger than the MDE". |
| Multiple testing | Benjamini–Hochberg over all contrasts in one run that have enough data. **Finding**: q ≤ 0.05. **Exploratory**: q ≤ 0.10. Otherwise **no clear effect**. |
| Minimum sample | Score findings: ≥ **100** games in the smaller group. Behaviour rates: ≥ **30**. Below that: **not enough data**, no claim. A time class with fewer than 20 games gets no cards. |
| Early estimate | Clock profile from fewer than 100 games. |
| Stop-loss rules | A rule *helps* if the games it would have skipped have a residual whose 95 % interval lies below the other games; *costs* if above; needs ≥ 30 skipped games. |

## Rules

| Term | Definition | Code |
|---|---|---|
| Rule | A suggestion from a card that the player adopts: a **clock checkpoint** or a **stop-loss rule**, per time class. At most one active rule per kind and time class. | `rules` table |
| Clock checkpoint | "Keep at least X of your clock after own move M" (M = 20 by default). A game that reaches move M **keeps** it if the clock after that move is at least `X × T_est`. | `rules.clock_units` |
| Suggested X | The 25th percentile of the clock share after move 20 in the player's wins (a floor 3 in 4 wins clear), rounded down to 5 %, at least 5 %. Needs ≥ 30 wins that reached move 20. | `clock._checkpoint` |
| Stop-loss rule | "Stop after 2 losses in a row", "3 in a row" or "3 losses in one session". A session in which the rule said stop **keeps** it if no further game of that time class followed. | `rules.stop_units` |
| Baseline | The player's last **300** games (or sessions) before `adopted_at`, scored as if the rule had applied. | `rules.BASELINE_UNITS` |
| Rule verdict | Share kept after adoption minus share kept in the baseline, game-cluster (checkpoint) or session-cluster (stop loss) bootstrap, same labels and Benjamini-Hochberg pass as every other card. **Too early** (`not_enough_data`) until 30 games or sessions on both sides. It is a before/after comparison, not a controlled experiment, and the card says so. | `rules.check_rule` |
| Changing a rule | Changing the threshold resets `adopted_at`: the count starts again. | `PATCH /rules/{id}` |

## More habits

| Term | Definition | Code |
|---|---|---|
| Warm-up | First game of a session (`session_index = 1`) vs later games in sessions; residual contrast, session-cluster bootstrap, ≥ 100 games per side. | `habits.warm_up` |
| Time of day | Start hour in the player's time zone (the UI sends `utc_offset_minutes`; times are shifted before sessions are built, which does not change gaps). Windows 0–6, 6–12, 12–18, 18–24 h. Per window: mean residual with a 95% session-cluster interval; vs the rest of the day: contrast with Bonferroni over 4 windows (p × 4 ≤ 0.05), ≥ 100 games inside and outside. | `habits.time_of_day` |
| Opening time | `1 − clock after own move 12 / T_est`. Per opening family (chess.com name without the move list, up to the first word such as Defense, Opening, Game or Variation; for generic families such as Queens Pawn Opening or Indian Game up to the second), ≥ 20 games, at most 8: median share used and mean residual with a 95% game-cluster interval. Descriptive, not corrected for multiple openings. | `habits.opening_time` |
| Premove | Own move whose time spent is exactly 0.1 s (1 tenth). Card only in bullet and blitz, with ≥ 50 such moves and at least 3× as many 0.1 s as 0.2 s moves. Shares by clock left (> 50 %, 25–50, 10–25, 5–10, < 5 % of `T_est`). | `habits.premoves` |
| Form | Per calendar month: games, median post-game rating, mean residual (from 10 games). | `habits.form` |
| Chart points | Means with a 95% cluster-bootstrap interval (1,000 resamples), descriptive only. Session chart: games 1 to 7 and 8+, ≥ 30 games per point. Curves: medians from ≥ 10 games per point. | `stats.cluster_mean`, `clock._charts` |
| Your plan | Items: significant (finding/exploratory) negative score contrasts, stop-loss rules that help, time windows that are clearly worse, openings whose interval lies below 0. Rank: cost in Elo × share of the time control's games affected. | `ui/src/plan.ts` |

## Deep analysis (Stockfish in the browser)

| Term | Definition | Code |
|---|---|---|
| Engine pass | Stockfish 19 lite single-threaded (stockfish.js 19.0.1, WASM, Web Worker), 100,000 nodes, MultiPV 2 on every own position with 2+ legal moves in the player's most recent N live games. If the played move is neither of the two, one more search restricted to it (`searchmoves`). Centipawns from the player's side; mate = ±(10000 − moves). | `ui/src/deep/run.ts` |
| Win% | Lichess curve `50 + 50·(2/(1+e^(−0.00368208·cp)) − 1)`. | `deep.win_pct` |
| Critical moment | `10 ≤ W_best ≤ 95` and `W_best − W_second ≥ 10`; not in check, not a recapture on the square of the opponent's last move, more than 3 legal moves. Only move: gap ≥ 20. | `deep.critical_moments` |
| Found | The played move loses < 3 win% points against the best move. | `deep._decision_points` |
| Move type | Of the best move: check, capture, castle, king, pawn, retreat (a piece other than pawn or king moving towards its own back rank), quiet. | `ui/src/deep/replay.ts` |
| Breakdowns | Find rate with a 95% Wilson interval, by move type, clock left (> 50, 25–50, 10–25, < 10 % of `T_est`), time taken vs the player's median think (< 0.5×, > 2×), purpose (only move to hold: `W_second < 35 ≤ W_best`; to win: `W_best ≥ 65 > W_second`). Rows need ≥ 20 positions; the card needs ≥ 30. | `deep.critical_moments` |
| Endings | Engine evaluation of the final position (one search, 100,000 nodes) of games ending by resignation, on time or by agreement. Resigned too early: expected score left ≥ 0.15 (also 0.10, 0.25), next to the opponents' resignations in the same games. Time losses winning/losing: ±300 cp. Agreed draws when better: expected score ≥ 0.60. In the plan only when the player's rate is 5+ points above the opponents'. | `deep.endings`, `ui/src/plan.ts` |
| Opening autopilot | Position key: FNV-1a hash of the first four FEN fields before each of the first 20 own moves. Known: the same key in ≥ 3 earlier games of the time control. Time per move as a share of `T_est`; book exit = first own move in a new position. | `deep.opening_autopilot` |


| Term | Definition | Code |
|---|---|---|
| Reference player | A chess.com account with `kind = reference`: a grandmaster to compare with. Imported and analysed exactly like your own account; the UI imports only its last **12** months. | `players.kind`, `ui/src/importer.ts` |
| Comparison | Your latest analysis run next to the reference player's, per time control both have. Nothing is recomputed from games. | `compare.compare` |
| Rows | Time trouble, scramble and self-inflicted shares (from the clock profile), the median move where time trouble starts and the clock left at move 20 in wins (descriptive only, not tested), and the effects of the cost of time trouble, quick requeues after a loss and play after a loss. | `compare.ROWS` |
| Difference of shares | You minus the reference, 95% Newcombe hybrid score interval, two-proportion z-test. Needs ≥ 30 games on both sides. | `compare._difference` |
| Difference of effects | You minus the reference; each side's standard error is taken from its 95% interval (`(high − low) / 3.92`), combined as independent. Only when both sides have enough data for their own card. | `compare._difference` |
| Verdict | Benjamini-Hochberg over every tested row of the comparison: q ≤ 0.05 **clearly different**, q ≤ 0.10 **maybe different**, otherwise **no clear difference**. Effects are measured against each player's own expectation, so they compare habits, not strength. | `compare.compare` |
