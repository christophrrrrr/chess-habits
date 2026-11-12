# Shortlist: what Kiebitz should analyse, and in which order

**Status:** synthesis of the first research sweep, 2026-11-12. It reads all notes in this folder (index in [README.md](README.md)), re-applies the vision test against [prior-work-gap-map.md](prior-work-gap-map.md), spot-checks the claims that looked too good, and turns the result into an MVP slice, a roadmap, open decisions and three experiments.

**Method and limits:** The spot checks in section 2 were direct fetches of primary pages on 2026-11-12. The shared web-search budget for this session was used up before this synthesis started, so no new searches were possible. Anything not re-checked here rests on the source notes. Speculation is marked as such.

---

## 1. The answer in one paragraph

Every product on the market grades **moves**, and the newer ones (Audit Chess, Chessigma Supercoach, Aimchess, chess-game-analyzer) also count things across games: accuracy by phase, blunders under time pressure, blown wins, streaks, best hours. None of them publishes its definitions, adjusts for position difficulty or rating lag, or says how sure it is. So the raw ideas ("time pressure", "tilt", "complexity") are not unique any more. What nobody offers is **behaviour measured against what the position demanded and against the player's own baseline, with an honest error bar and a loop that checks the fix**. Concretely, Kiebitz can tell a strong chess.com player:
- where their time trouble comes from, whether it costs *them* points beyond the position they had (E3: for the owner it does, and only when self-inflicted), and how many winning positions the clock takes;
- which kinds of only-moves they miss (quiet, defensive, low clock), compared with their own norm and later with players of their level (Maia-3);
- whether their resignations, stop-loss habits and play times are good decisions for *them*.

Every finding carries n, a 95% interval and a minimum detectable effect, and becomes a rule or drill whose effect is re-measured against a control. The clock and context parts are **reliable and shippable now** without an engine. The criticality and peer parts are the long-term moat but need a browser engine pipeline and a validation run first. E1 showed that "time vs criticality" is not a personal trait and that fast critical moves are not the problem, so the engine slice leads with the only-move find rate. Gaze comes after that.

---

## 2. Sceptic pass

### 2.1 Spot checks (2026-11-12)

| Claim in the notes | Check | Result |
|---|---|---|
| "No product measures tilt or session effects" ([gap map](prior-work-gap-map.md) bottom line 4) | [Audit Chess home page](https://www.auditchess.com/), [Audit Chess analyzer page](https://www.auditchess.com/chess-performance-analyzer) | **Overstated.** Audit Chess imports chess.com and Lichess games. It groups games into sessions, shows "whether your results hold up over a long sitting or fall off after the third game" (it calls this "the classic tilt signature"), losing streaks, best hours, and lists "Confidence Under Pressure" ("on tilt"). Everything is a raw result split: no rating adjustment, no intervals, no sample-size rules, no published session rule. The gap is the *honest, rating-lag-corrected, per-player* version, not the topic. |
| "Clock analysis is almost absent for chess.com players" (gap map) | Audit Chess pages; [Chessigma Supercoach](https://chessigma.com/supercoach); [chess-game-analyzer README](https://github.com/StephanAkkerman/chess-game-analyzer) | **Narrower than stated.** Audit Chess lists "Time Pressure Analysis: how your accuracy and blunder rate shift as the clock runs low" (home page). Its analyzer page does not mention clock analysis, so the vendor contradicts itself. Chessigma's "Discipline" area covers "time pressure, snap moves, flagging", with no definition. The open-source chess-game-analyzer imports chess.com games and reports "mistakes played in under 3 seconds, mistakes made in time trouble and long thinks on obvious moves", plus only-move positions and "whether you found it", with cross-game stats on clock use (0 stars). Plain "accuracy by clock band" and "overthinking obvious moves" therefore fail the vision test. |
| "Nobody relates time spent to criticality" | chess-game-analyzer README; Audit Chess "Position Complexity" | **Holds, barely.** chess-game-analyzer has both ingredients (only-move positions and clock use) per game, but its README does not cross them. Audit Chess shows "how your accuracy holds as positions get sharper", which is accuracy vs sharpness, not time. The idea is in the air; the defensible part is the formula (Russek ΔU), the own-baseline normalisation and the CI. Novelty lowered from 5 to 4. |
| chess.com Insights has no time-management metric | [chess.com Insights help](https://support.chess.com/en/articles/8708925-what-is-insights) (dated 2026-01-27) | **Confirmed.** Sections: Games, Openings, Tactics, Moves, Calendar (time of day and weekday), Geography. Clock appears only as "timeout" in the results by method. |
| Aimchess "time management" is undefined | [aimchess.com](https://aimchess.com) | **Confirmed.** Only the example "behind on the clock for 78% of your moves"; no definition, no tilt, no intervals. The "31% faster" claim still has no paper. |
| chess.com per-game `rating` is post-game (gap map said "probably") | [chess.com Published-Data API](https://www.chess.com/news/view/published-data-api) | **Confirmed**: "the player's rating after the game finished". The docs do not mention `[%clk]` at all, so the clock parser relies on observed behaviour (see [clock-and-time.md](clock-and-time.md)). |
| Lichess tilt is about −7 Elo, none at 2000+, gone after a 30-min break | [romanbreyten/chess-tilt](https://github.com/romanbreyten/chess-tilt) | **Confirmed**, with a caveat the notes omit: the author says the honest range is about **−4 to −7 Elo**, because the rating control includes later games. Not peer reviewed. |
| Strong players allocate time better (Russek et al. 2025) | [Russek et al., Cognitive Science 2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC12553403) | **Confirmed**, but "modest": the time-vs-ΔU link "increases with player Elo in all time-control conditions", with Elo interaction estimates of 0.02 to 3.07 across time controls. ΔU uses depth 1 vs depth-15 ground truth. A per-player ρ is plausible; that it *differs between strong players* is untested (experiment E1). |
| Difficulty predicts errors far better than skill or time (Anderson et al.) | [arXiv 1606.04956](https://arxiv.org/abs/1606.04956) abstract | **Confirmed qualitatively.** The abstract gives no numbers. The notes disagree on the figure: [expertise-literature.md](expertise-literature.md) says 0.73 for difficulty alone and 0.75 for all features; [game-mistake-taxonomy.md](game-mistake-taxonomy.md) cites 0.75 as difficulty alone. Use 0.73. |

### 2.2 Downgrades after the vision test

- **Mistake taxonomy**: MVP → slice 1. It needs the engine pipeline and a null-move probe. Only 37 of 50 low-budget "mistakes" held at 1M nodes ([game-patterns.md](game-patterns.md)). Its own note requires 150-200 hand labels from the owner before showing classes. Audit Chess "Mistake Themes" and FireChess cover the motif version. That is too much risk for 12 days.
- **Conversion and defence profile**: MVP → slice 1. The plain rate exists (Aimchess, Audit Chess "Blown Wins", Chessigma "save rate"). The new part, the expected-score residual, is **biased in v1**: the pilot residual is negative in every time control (−0.17 rapid, −0.13 blitz, −0.28 bullet), because of threshold-crossing selection and a rapid-calibrated Win% curve ([game-conversion-and-defence.md](game-conversion-and-defence.md)). Shipping v1 would tell every user they under-convert. It needs the clock-aware v2 baseline built offline from the Lichess database.
- **Recurring positions / habitual-move flags**: MVP candidate → later, low priority. Exact positions stop recurring after ply 6-9 for the owner, so this is opening prep, not "how you play". FireChess already reports repeated opening errors ("played 14 times, 70% loss"), Chessbook flags deviations, and the Lichess personal explorer plus engine shows the same thing by hand. It is folded into opening autopilot (clock) and the drill decks.
- **Structure familiarity**: MVP → later, behind its own validation. The lab effect (about 1 SD) comes from selected positions; the real-game effect is unknown and "likely much smaller" by the author's own estimate. It needs 200+ earlier games before a game counts and 100+ games per bucket. Run the population check first.
- **Time of day**: kept, but novelty 2, not 3. chess.com Insights Calendar and Audit Chess "best hours" already show raw results by hour. Only the rating adjustment, the family-wise test and the play-window rule are new. It stays as a cheap MVP stretch card because it produced the owner's clearest pilot finding.
- **Long thinks, part A (overthinking forced moves)**: novelty 4 → 2 (chess-game-analyzer, Chessiro). Part B (long-think payoff within criticality bands) is still new.
- **Transition / simplification errors**: novelty 4 → 2 (Audit Chess "Simplification Tendency", Lichess Insights `queenTrade`). Kept as a tag inside the taxonomy.
- **Cost of time trouble (accuracy by clock band)**: novelty 3 → 2 (Lichess Insights, Audit Chess claim). Kept only as the engine-priced add-on to the time-trouble card, within criticality bands.
- **Tilt (outcome)**: reliability stays 2. Per-player power is the binding limit (about 640 games per group to detect 50 Elo), and the owner pilot shows no outcome tilt. The card's value is the stop-loss **simulator** and the **behavioural** markers, plus a credible "no effect larger than X" answer.

### 2.3 Contradictions between notes, and how this shortlist resolves them

| # | Contradiction | Where | Resolution |
|---|---|---|---|
| 1 | Blunder threshold: ΔW ≥ 20 (chess.com 0.20 expected points) vs ΔW ≥ 15 (Lichess 0.3 on the −1..1 scale) | [clock-and-time.md](clock-and-time.md) vs [game-patterns.md](game-patterns.md) | Both agree on **error = ΔW ≥ 10**. Use that as the only threshold in findings. Pick one blunder threshold in a shared definitions file (decision D4). |
| 2 | MVP engine: browser Stockfish depth 12 in the MVP vs MultiPV 2 at 100k nodes plus re-verification vs no engine | [engines-and-human-baseline.md](engines-and-human-baseline.md), [game-patterns.md](game-patterns.md), clock and psych notes | **No per-move engine findings in the MVP.** Depth 12 agrees with depth 22 on only 71.5% of best moves, and even 100k-node mistake labels flipped 13 of 50 times. Slice 1 uses 100k nodes on the user's positions with MultiPV 2, and re-verifies every ΔW ≥ 7 at a higher budget. Criticality labels were stable (47/50), so criticality-based analyses are the safer first engine features. |
| 3 | Lichess cloud eval: "cheapest source" vs "not worth it" | [game-recurring-positions.md](game-recurring-positions.md) vs [engines-and-human-baseline.md](engines-and-human-baseline.md) | **Drop it.** Measured: one request at a time, 0/59 hits after ply 30. Use Kiebitz's own eval cache keyed by EPD in the insights DB. |
| 4 | Stockfish build: "Stockfish 18 lite, about 7 MB" vs "Stockfish 19 lite single, 1.8 MB" | clock notes vs engines note | Use the engines note: stockfish.js 19.0.1 lite single-threaded (1.8 MB, no COOP/COEP needed). |
| 5 | Tilt numbers: gap map's exploratory after-loss differences (bullet −58 ± 50, blitz +82 ± 79, rapid +66 ± 51) vs psych pilot (after-loss vs own level: bullet −28, blitz +47, rapid +27) | [prior-work-gap-map.md](prior-work-gap-map.md) vs [psych-tilt-and-stop-loss.md](psych-tilt-and-stop-loss.md) | The gap map used post-game ratings, which the API confirms (2.1). Use the psych method (smoothed `R_skill`, session-cluster bootstrap). Both agree on direction (bullet slightly negative, blitz and rapid positive or zero) and on the main point: intervals are ±40-80 Elo. |
| 6 | Residual baseline: raw `R_you` vs smoothed `R_skill` | [structure-familiarity.md](structure-familiarity.md) vs psych notes | Use `R_skill` everywhere (pre-game rating reconstructed from the previous game, median over ±25 games). The insights code (PR #2) already does this. |
| 7 | Session rule: gap > 30 min from end to next start (psych notes) vs "end-to-end gap minus the next game's maximum duration, plus 30 min" (insights code (PR #2)) vs start-to-start 5/7 min (Gee et al.) | psych notes, `services/insights/app/analysis/games.py` | One rule, stored in the shared definitions. Prefer end→start, because the PGN has `UTCDate`/`UTCTime` (start) and the archive has `end_time`. The current code has no start time and approximates it. |
| 8 | Minimum sample: 30 games per group (insights code, [game-decision-points.md](game-decision-points.md)) vs 100 games in the smaller group (psych) vs 30 games and 200 moves (clock) | several | Two levels. **Outcome findings** (score residuals) need ≥ 100 games in the smaller group. **Move-level rates** need ≥ 30 games and ≥ 200 moves (or ≥ 30 events). Below that, show "not enough data" with the MDE. |
| 9 | Resampling unit: game (clock, game, training notes) vs session (psych) | several | Session-cluster bootstrap for anything about consecutive games; game-cluster bootstrap for move-level metrics. The current code uses a Welch normal interval over games, which is too narrow for session effects. |
| 10 | Maia-2 as the learnability filter for drills vs "Maia-2 is unusable above 2000" | [training-own-position-drills.md](training-own-position-drills.md) vs [maia-human-baseline.md](maia-human-baseline.md) | Use Maia-3 (pending the weight licence), or drop the filter for 2000+ users until then. |
| 11 | Null-move threat threshold T ≥ 10 vs T ≥ 15 | taxonomy vs drills notes | Decide during taxonomy validation (owner hand labels). |
| 12 | Time-trouble definition: `c < 10%` of `T_est` with ≥ 5 own moves still to play (clock notes) vs clock below 10% of **base** at any point (insights code) | [clock-time-trouble.md](clock-time-trouble.md) vs `analyses.py` (PR #2) | Use `T_est = base + 40 × inc` and the "5 more moves" rule. The current code over-counts games that end with a mate scramble and ignores increment. |
| 13 | "Maia-2 and Maia-3 both run in the browser" vs "no Maia-2 browser export found" | gap map vs clock notes | Moot: Maia-2 is dropped for 1800+ users. |
| 14 | AGPL obligations "if served from our backend" vs "only ONNX weights with our own preprocessing in the browser" | [expertise-literature.md](expertise-literature.md) vs engines note | Both are readings, not legal advice. Weight licence unknown. Decision D2/D3. |
| 15 | Gaze accuracy: "about one square (~100 px)" | [vision.md](../vision.md) vs [gaze-tracking.md](gaze-tracking.md) | Use the gaze note: 2-7° in home use = 1-3 squares. Analyses use halves, quadrants and coarse zones only. vision.md should be corrected. |

---

## 3. Gap map

"Exists" means a documented or vendor-claimed feature as of 2026-11-12 (sources in [prior-work-gap-map.md](prior-work-gap-map.md) and section 2.1). "Undefined" means the vendor names it but publishes no method.

| Analysis | Existing tools | Kiebitz angle |
|---|---|---|
| Move grading, accuracy, classifications, explanations | chess.com Game Review, Lichess analysis, Chessigma, Audit Chess, Chessiro, maiachess.com | None. Engine output is an input only. |
| Accuracy / results by phase, opening, tactic motif | chess.com Insights, Lichess Insights, Aimchess, Audit Chess, ChessBase Error Report | None. |
| Clock summary (time-pressure share, behind on clock, mistakes under time pressure) | Lichess Insights (Lichess games only), Lichess Tutor (partly, release unclear), Aimchess (undefined %), Audit Chess "Time Pressure Analysis" (undefined), Chessigma "Discipline" (undefined), chess-game-analyzer (counts) | Per time control: onset move, self-inflicted share, **where the time went** (opening / single long thinks / steady drain), pace curve from the player's own wins, all with CIs. |
| Flag losses by position | chess.com Insights (timeout counts), Lichess Tutor (flag share vs peers); "flag with good position" exists only as commented-out Lichess code | **Net clock points**: games lost on time while winning vs won on time while losing. |
| Opening time on autopilot | chess.com Insights "Mastery" (book moves, no time), Lichess Insights (absolute buckets) | Seconds spent in positions *you* have reached ≥ 3 times, and time after the opponent leaves your line. |
| Time spent vs criticality | Nobody across games. chess-game-analyzer has only-moves and clock use per game, not crossed; Lichess Insights crosses time with eval only; Chessboard Magic claim without method | ρ(relative time, ΔU), "missed alarms" (critical and fast) and "wasted time" (quiet and slow) vs own baseline; later vs peers. |
| Only-move find rate | chess.com "Great" per move; chess-game-analyzer per game; Audit Chess "Position Complexity" (accuracy vs sharpness) | Non-trivial find rate across games, split by quiet / retreat / defensive / low clock; later difficulty-adjusted. |
| Mistake causes | chess.com "Miss", Insights motifs; Lichess "Tactical awareness"/"Luck"; Audit Chess "Mistake Themes" (motifs); FireChess | Cause classes (missed threat, allowed tactic, missed chance, quiet misjudgement, drift) from a null-move probe, validated by hand, with context over-representation. |
| Conversion and defence | Aimchess, Audit Chess "Blown Wins", Chessigma "save rate", chess.com Advanced Stats, ChessBase | Clock-aware expected-score residual and failure cause (single blow vs drift, clock state). |
| Peer-relative blind spots | maiachess.com per position and per game (Lichess only) | Excess loss vs Maia-3 peers aggregated by context over hundreds of chess.com games. |
| Reaction to the opponent's surprising move | Nobody | Surprise from Maia; time and error on the reply, within criticality bands. |
| Practical pressure (difficulty created vs faced) | Aimchess "Resourcefulness" (outcome), ChessBase "Risk" (style), Audit Chess "Risk Profile" (undefined) | Expected human loss created vs faced, against the opponents in the same games. |
| Tilt and sessions | Audit Chess (raw sessions, streaks, "falls off after the third game"), Chessigma session timeline, stop-loss extensions (rules, no measurement) | Rating-lag-corrected residual, MDE, **stop-loss rule simulator**, behavioural markers (requeue speed, time use after a loss). |
| Time of day | chess.com Insights Calendar (raw), Audit Chess best hours (raw) | Residual vs own level, family-wise permutation test, play-window rule. Narrow gap. |
| Resignation and draw decisions | Counts by method only (chess.com Insights, Lichess Insights) | Expected score at resignation vs a rating- and clock-conditioned human baseline, compared with the opponents' resignations. |
| Familiarity with own structures | chess.com Advanced Stats "pawn structure" skill rating | Results and later move quality by how often you reached the structure before (unvalidated). |
| Training from own mistakes | Lichess, chess.com, Aimchess, Chessable, Chess Tempo, Chessiro, Noctie, Chessigma, FireChess | Cause-grouped decks, process drills (threat-first, think-or-play), knowledge vs process split. |
| Habit rules | Stop-loss extensions | Rules whose **adherence is counted from game data**, chosen from the player's own findings. |
| Did it improve? | chess.com "Past Performance", Audit Chess "Period Reports" (general stats per period) | Split-sample baseline, untrained-type control, cluster bootstrap CI, MDE, honest states. |
| Uncertainty per finding | Nobody (checked: chess.com, Aimchess, Audit Chess, Chessigma); Lichess shows counts; ChessBase warns in docs | n, 95% interval and MDE on every card; "no effect larger than X" as a first-class answer. |
| Premoves | Chessiro (count per game) | Premove cost and missed premoves in scrambles (chess.com charges exactly 0.1 s per premove). |
| Gaze | Nobody links gaze to move quality | Region-level habits (threat check, last-move reaction, tunnel vision) linked to mistake classes, validated within player. |

---

## 4. Ranked candidates

Scores 1-5 (5 = best) after the sceptic pass; where a score changed from the researcher's, the reasoning says so. Effort: S ≈ days, M ≈ 1-2 weeks, L ≈ weeks plus a pipeline. Duplicates across notes are merged (source notes in brackets).

| # | Candidate [notes] | Nov | Val | Rel | Eff | Verdict | Reasoning |
|---|---|---|---|---|---|---|---|
| 1 | **Honest statistics layer**: n, 95% CI (cluster bootstrap), MDE, Finding / No effect ≥ X / Not enough data, BH across a page [gap map G8, psychology-and-context, training-improvement-tracker] | 4 | 4 | 5 | S | **MVP** | No competitor shows any of it (checked). Cheap, testable, and it makes every other card credible. **E2 (run):** with BH at q = 0.10, 9-13% of shuffled (null) pages still raised a finding, as BH promises; use q = 0.05 for "Finding" and label 0.05-0.10 "exploratory". |
| 2 | **Time-trouble onset, self-inflicted share, where the time went** [clock-time-trouble, gap map G4] | 3 | **5** | 4 | S | **MVP** | Clock-only and exact. The topic exists elsewhere, the decomposition does not. In 1+0 entry is near-universal, so the bullet card reduces to onset and scramble rate. **E3 (run):** for the owner the score gap survives control for the position at move 20, sharpness and rating gap (main/raw ratio 1.02-1.08, CIs exclude 0), and the cost sits in *self-inflicted* time trouble; other players show little or none. Value 4 → 5: a personal, decomposed cost no tool shows. |
| 3 | **Flag losses from winning positions / net clock points** [clock-flag-losses] | 3 | 4 | 4 | S | **MVP** | Exact counts. **E3 (run):** material ≥ +3 has precision 0.96 but recall 0.48 against the engine, so the MVP shows it as a lower bound; one final-position eval nearly doubles the count (owner: 52 → 94 of 273 flag losses). |
| 4 | **After-loss check + stop-loss rule simulator + requeue speed** [psych-tilt-and-stop-loss, gap map G3] | 4 | 3 | 3 | S | **MVP** | The simulator is new (5); outcome tilt is weak per player. **E2 (run):** faster requeue after a loss is a finding for 4 of 5 players (+7 to +39 pp), so it is near-universal: show its size against other players, not as a personal discovery. Results after a loss stay within ±20-40 Elo for players with thousands of games. |
| 5 | **Personal rules with adherence from game data** (start with clock checkpoint and stop-loss) [training-personal-rules] | 4 | 4 | 4 | S | **MVP** | Closes the loop without an engine; adherence is a count, not an estimate. |
| 6 | **Improvement tracker** (split-sample baseline, untrained control, MDE, states) [training-improvement-tracker, gap map G7] | 5 | 5 | 4 | M | **MVP (minimal)** | Ship baseline, MDE and "too early" for the MVP rules. The full DiD view needs post-adoption games that will not exist by 24 Nov. |
| 7 | **Opening autopilot cost and post-exit spend** [clock-opening-speed] | 4 | 3 | 4 | S | **MVP stretch** | Clock-only and novel. Value 4 → 3: big for bullet, small for rapid. |
| 8 | **Time of day, rating-adjusted** [psych-time-of-day] | 2 | 3 | 3 | S | **MVP stretch** | Raw version exists (chess.com, Audit Chess). Kept because it is cheap on the same engine and is the owner's clearest pilot finding (−155 Elo in 06-12 h rapid, family-wise p = 0.003), which depends on the assumed time zone. |
| 9 | **Critical moments: non-trivial only-move find rate by move type** (+ time vs criticality as a descriptive chart) [game-decision-points, clock-time-vs-criticality, gap map G1] | 4 | 5 | 3 | L | **Slice 1 flagship** | One engine pass (MultiPV 2 on own positions). **E1 (run) redirected it:** time does rise with ΔU (owner ρ = 0.13 [0.11, 0.16]), but fast critical moves are *less* often wrong than slow ones (−18 pp [−23, −13]) for all four players, and same-time-control players have the same ρ. So the card must not say "you miss only-moves when you move fast"; per the kill rule, the find rate by move type leads. E1 measured 1.5-2.4 non-trivial critical positions per rapid game. |
| 10 | **Resignation and agreed-draw quality** [psych-resignation-and-draws] | 5 | 4 | 3 | M | **Slice 1** | One eval per game, big samples (owner: 460 rapid resignations). Reliability 4 → 3 until the clock-conditioned lookup table is built and checked. |
| 11 | **Mistake taxonomy** (4 classes + drift, transition and low-clock tags) [game-mistake-taxonomy] | 3 | 4 | 2 | M | **Slice 1, after validation** | Downgraded from MVP (2.2). Novelty 4 → 3 (Audit Chess Mistake Themes, FireChess). Ships only after the owner's hand labels reach ≥ 80% agreement per class. |
| 12 | **Conversion and defence, expected-score residual v2 + failure cause** [game-conversion-and-defence] | 2 | 4 | 3 | M | **Slice 1** | Plain rate exists. v1 residual is biased (2.2). Needs the offline Lichess-database baseline with the same entry rule. |
| 13 | **Threat-first two-step drill + cause-grouped decks + knowledge-vs-process split** [training-own-position-drills, training-loop] | 4 | 4 | 3 | M | **Slice 1** | Drills from own blunders exist everywhere; process drills and the knowledge/process split do not. Needs the engine and the taxonomy. |
| 14 | **Premove patterns (cost, missed premoves)** [clock-bullet-premoves] | 3 | 3 | **4** | S | **Slice 1 add-on** | Cheap, chess.com-specific detector; relevant because the owner plays a lot of bullet. **E3 (run):** exact 0.1 s is 5-40× more common than 0.2 s for every player who premoves, and absent for one who does not; reliability 3 → 4. Show the card only when the spike exists. |
| 15 | **Time-trouble tax** (error rate under 10% clock within criticality bands) [clock-time-trouble] | 2 | 4 | 3 | M | **Slice 1 add-on** | Novelty 3 → 2 (Lichess Insights, Audit Chess claim). Only worth it as the priced version of card 2. |
| 16 | **Long thinks: payoff within criticality bands; overthinking forced moves** [clock-long-thinks] | 3 | 3 | 3 | M | **Slice 1 add-on** | Part A exists (chess-game-analyzer, Chessiro), part B does not. **E1:** long thinks go with *more* errors even after engine-difficulty controls (odds ×1.2-1.4 per doubling of relative time), so "payoff" must be read as "where you found it hard", not as "thinking longer helps". |
| 17 | **Peer excess loss / blind-spot index (Maia-3)** [maia-human-baseline, gap map G2, expertise-literature] | 4 | 5 | 3 | L | **Slice 2** | The strongest long-term differentiator. Needs Maia-3 weight licence, chess.com→Lichess rating mapping and a calibration check. Weak resolution at 2400-2600. |
| 18 | **Reaction to surprising opponent moves** [clock-surprise-response, game-surprise-reaction, gap map G5] | 5 | 4 | 2 | L | **Slice 2** | Directly the vision's example; nobody does it. Needs Maia and matched controls; Maia-3 drops positions under 30 s. |
| 19 | **Practical pressure balance + problem-setting rate** [practical-pressure, game-problem-setting] | 5 | 4 | 2 | L | **Slice 2, after offline validation** | Most novel idea for strong players. Must first show on public Lichess data that pressure balance predicts score beyond rating. PSR (engine-only) is the cheap first step. |
| 20 | **Population baseline tables** (Lichess open DB, 1800-2600 bands) [engines-and-human-baseline] | 3 | 4 | 4 | M | **Slice 2 (infrastructure)** | Feeds cards 10, 12, 17 and 19. CC0 data, built offline, seeded by migration. |
| 21 | **Maia-filtered drills, "think or play?" drill with foils, surprise drills** [training-loop] | 5 | 5 | 3 | M | **Slice 2** | Depends on card 9 (criticality) and Maia. |
| 22 | **Position-type weaknesses** (named structures, context model) [game-position-types] | 3 | 4 | 2 | M | **Slice 2** | Needs hundreds of analysed games per time control and a validated context model. Build the tagger early: it is reused. |
| 23 | **Structure familiarity** [structure-familiarity] | 4 | 3 | 2 | S | **Later, behind validation** | Downgraded from MVP (2.2). |
| 24 | **Warm-up (first game of session)** [psych-session-warmup-fatigue] | 4 | 3 | 3 | S | **Slice 1 add-on** | More power than fatigue (every session has a first game); owner pooled −23 Elo [−46, +1]. Reuses the MVP engine. |
| 25 | **Post-loss move quality** (error rate after a loss instead of score) [expertise-literature, psych] | 4 | 3 | **2** | M | **Slice 1 add-on (secondary check only)** | **E2 (run) failed its precision test:** in standardised units it is no tighter than the result contrast on the same games; in Elo-equivalent terms 1.9-2.8× tighter, but only 1.2-2.2× tighter than results over *all* games, and it costs engine time. Use it to say "faster but not worse", not as the main after-loss metric. |
| 26 | **Behavioural markers beyond requeue** (time use on moves 10-25 after a loss, P(stop)) [psych-tilt-and-stop-loss] | 5 | 3 | 4 | S | **Slice 1 add-on** | Exact, cheap; meaning for results unclear. |
| 27 | **Within-game error cascade** [expertise-literature] | 4 | 3 | 2 | M | **Later** | Mixed evidence (small errors cascade, big ones do not). |
| 28 | **Sensitivity vs consistency profile (Regan s, c)** [expertise-literature] | 4 | 3 | 2 | M | **Research only** | Interesting two-number profile; fitting per context is fragile at small n. |
| 29 | **Fatigue curve** [psych-session-warmup-fatigue] | 3 | 2 | 2 | S | **Later (bullet only)** | Long sessions are rare in rapid (owner: 16 games at index 11+). Note: the insights code (PR #2) already runs a version; keep it only if it passes the MVP statistics rules. |
| 30 | **Daily quick-reply cost** [clock-daily-latency] | 4 | 1 | 1 | S | **Later** | Undocumented clock format; owner plays few Daily games. |
| 31 | **Increment use** [clock-and-time] | 2 | 2 | 4 | S | **Later (small)** | Owner plays almost no increment games. |
| 32 | **Think time vs human-predicted time** (Allie, ChessMimic) [clock-and-time, gap map] | 5 | 4 | 1 | L | **Research only** | Allie is 18 GB; ChessMimic r = 0.41. Not runnable in the constraints. |
| 33 | **Personal Maia (Maia4All)** [expertise-literature, gap map] | 4 | 3 | 1 | L | **Research only** | Code release unconfirmed. |
| 34 | **Recurring positions, habitual-move flags** [game-recurring-positions] | 2 | 3 | 4 | S | **Later, folded into 7 and 13** | Downgraded (2.2). |
| 35 | **Gaze: relevance latency in training sessions** [gaze-relevance-latency] | 5 | 3 | 3 | M | **Slice 3 (first gaze)** | Replicates the best-established eye-tracking result; works for chess.com users; validates the pipeline. |
| 36 | **Gaze: threat check (opponent-side and king-zone share)** [gaze-threat-check] | 5 | 4 | 2 | M | **Slice 3** | Half-board measure is robust; link to mistakes unproven; peripheral vision. |
| 37 | **Gaze infrastructure: move-click recalibration, per-session error** [gaze-tracking] | 3 | 4 | 3 | S | **Slice 3 (prerequisite)** | Assumption that players look at clicked squares is untested. |
| 38 | **Gaze: tunnel vision, last-move reaction** [gaze-tunnel-vision, gaze-last-move-reaction] | 5 | 3 | 2 | M | **After slice 3** | Need many long thinks or validation against peripheral vision. |
| 39 | Gaze: off-screen time, dwell entropy, pre-move sweep | 3 | 2 | 2 | S | **Features only** | Use inside 35-38, not as findings. |
| 40 | Server-side Stockfish; Lichess cloud eval; Maia-1/2 [engines-and-human-baseline] | 1 | 1 | 2 | M | **Drop** | Constraint misfit (240 s timeout, 1 replica) or no coverage of 1800+. |
| 41 | Accuracy by clock band; fast vs slow unconditioned; behind-on-clock share; move-time variance; time share per phase [clock-and-time] | 1 | 2 | 3 | S | **Drop** | Lichess Insights, Aimchess, Audit Chess, Chessiro; confounded without criticality. |
| 42 | Accuracy by phase/opening/motif; plain conversion rate; game shapes; punishing errors standalone [game-patterns, gap map] | 1 | 2 | 4 | M | **Drop** | Fails the vision test. |
| 43 | Rating-difference effects; round numbers/personal bests; rematches; weekday; draw offers; playing on too long [psychology-and-context] | 1 | 1 | 1 | S | **Drop** | Exists, not actionable, or not observable. |
| 44 | Style profile / stylometry; skill-anomalous positions; Maia-implied rating [expertise-literature, engines] | 1 | 1 | 2 | M | **Drop** | Exists (ChessBase, Chessiverse) or flat likelihood above 2400. |
| 45 | Puzzles from own blunders; single-game retry; weekly plan; opening SR; LLM coach; rating gain or drill accuracy as success metrics [training-loop, gap map] | 1 | 2 | 2 | M | **Drop** | Everywhere already, or misleading as evidence. |
| 46 | Gaze: dispersion, fixation metrics, pupil/blink, gaze in chess.com games via an extension [gaze-tracking] | 2 | 1 | 1 | M | **Drop** | Below webcam resolution, emotion-recognition risk, or against chess.com Fair Play. |
| 47 | **"Found it hard" label from think time** (critical positions with a long relative think, especially those that still went wrong) as a drill source and a cheap human-difficulty proxy before Maia-3 [new, from E1] | 4 | 3 | 3 | S | **Slice 1 add-on (needs a test)** | E1: every doubling of relative time goes with 1.2-1.4× error odds after engine-difficulty controls, for all four players; the owner errs in 37.6% of critical positions where he thought ≥ 2× his median. Speculation: these make better drills than random own mistakes; test it against the drill retention data in slice 1. |

---

## 5. Recommended MVP slice (ship by 2026-11-24)

**Name:** *Clock and context profile with honest statistics and one checked rule.*

**Why this slice:** It needs only data the games service already stores (PGN with `[%clk]`, ratings, results, termination, timestamps). It needs no engine, no Maia, no new service and no queue. It is a real "feature beyond CRUD" for the assignment. Every card passes the vision test through its decomposition, its baseline or its statistics, and none of it depends on unvalidated heuristics. The engine-based analyses are more novel but carry label noise that the course timeline cannot validate.

**Starting point (PRs #1 and #2, not yet merged on 2026-11-12):** the insights service already runs `tilt`, `session_fatigue` and `time_trouble` per time class. It uses `R_skill`, reconstructed pre-game ratings, Welch intervals and a 30-game minimum. The games service stores PGN, per-ply clocks, `ended_at`, `result_detail` and base/increment. The slice upgrades this code; it does not start over.

**Scope, in priority order (one developer; analysis work budgeted at about 5 of the 12 days, the rest goes to deploy, monitoring, SLO, docs and Scrum):**

1. **Statistics layer** (insights, about 1 day). Session-cluster bootstrap (2,000 resamples) for session effects, game-cluster bootstrap for move-level rates; MDE `≈ 2.8 · SD · √(1/n₁ + 1/n₂)`; three labels (Finding / No effect larger than X / Not enough data); Benjamini-Hochberg at q = 0.05 over the cards on a page (E2: q = 0.10 gave 9-13% false pages), q 0.05-0.10 shown as "exploratory"; the two minimum-sample levels from contradiction 8. Unit tests carry the 70% coverage rule.
2. **Clock profile card** (about 1.5 days). Per time control, with `T_est = base + 40 × inc`, move 1 dropped:
   - entry rate (`c < 10% of T_est` with ≥ 5 own moves still to play), scramble rate (`c < 3%`), median onset move;
   - self-inflicted share (opponent had more clock at onset);
   - where the time went before onset: opening (own moves 2-12) / spikes (`t ≥ 4 ×` own median for that band) / drain, compared with games without an entry;
   - pace curve: median clock fraction at own moves 10/20/30/40 in wins vs losses;
   - flag losses and wins split by final material (from the final position, replayed with python-chess): lost on time while ≥ +3, won on time while ≤ −3, net clock points per 100 games.
   - The flag count by material is a lower bound (E3: precision 0.96, recall 0.48); word it "at least N".
   - The score link: E3 showed that for the owner it survives the move-20 position control and sits in self-inflicted time trouble. The card may state the score gap as a per-player finding ("not explained by your position at move 20"), never as "caused", and only where the player's own CI excludes 0.
3. **After-loss card** (about 1 day). After-loss vs after-win residual in Elo with MDE; stop-loss simulator for "2 in a row", "3 in a row" and "3 total" (games skipped, their residual and CI); requeue speed after a loss vs a win, shown against the range seen in other players (E2: +7 to +39 pp, near-universal) and paired with "did it cost you?". The start time comes from the PGN `UTCDate`/`UTCTime` (parse in insights, or add a `started_at` column with a games migration).
4. **One rule with adherence** (about 1 day). The player adopts either the clock checkpoint ("≥ X% of base at move 20", X from their own wins) or the stop-loss rule from a card. Insights stores `rule(kind, params, adopted_at)` and shows the adherence count per new import, the baseline with its CI and MDE, and the state "too early" until enough post-adoption games exist.
5. **Stretch, in this order:** opening autopilot cost (card 7); time-of-day card with the browser's IANA time zone stored on the account (card 8); one browser Stockfish eval of the **final position** of each flag loss and resignation (stockfish.js 19 lite single, depth 18, about 1 s each), which upgrades the material proxy and previews resignation quality.

**Out of scope for the MVP:** per-move engine analysis, mistake classes, conversion residuals, Maia, drills, gaze, Lichess import.

**Demo story (Sprint Review):** import `chrisaxm` → the clock profile shows bullet onset and the flag-loss count → the after-loss card says "no tilt larger than X Elo; a stop-after-2 rule would have skipped N games you played at your level", but "you requeue within 60 s after 64% of rapid losses" → adopt the clock-checkpoint rule → adherence strip and "too early" state.

**Risks:** time-zone handling (Windows needs `tzdata`); the `[%clk]` format is undocumented (keep the parser's sanity checks); rating-lag bias if any card bypasses `R_skill`.

---

## 6. Roadmap: the three slices after the course

### Slice 1 (Dec 2026 - Jan 2027): browser engine pipeline and critical moments

- **Pipeline:** stockfish.js 19.0.1 lite single-threaded in N = min(4, cores − 1) Web Workers. 100k nodes (about depth 16) and MultiPV 2 on the user's positions, single PV elsewhere. Re-verify every ΔW ≥ 7 at a higher budget. Newest games first, resumable. Per-ply rows posted to insights and cached by EPD, with `engine_id` stored on every row. The containers stay engine-free ([engines-and-human-baseline.md](engines-and-human-baseline.md)). Ship the GPL source offer with the WASM file.
- **Analyses:** card 9 (critical moments: non-trivial only-move find rate by move type, with time vs criticality only as a descriptive chart, after E1) as the flagship; resignation quality (10); the time-trouble tax, premove and long-think add-ons (14-16); warm-up and post-loss move quality (24-26); the mistake taxonomy (11) once the owner's labels validate it.
- **Training:** threat-first two-step drill and missed-own-chance deck with FSRS (py-fsrs, MIT); knowledge-vs-process split (13); the full improvement tracker with the untrained-type control.
- **Exit criteria:** find-rate cells with ≥ 100 decision points each (E1: 1.5-2.4 per rapid game); verification of every 7 ≤ ΔW < 25 at a higher budget (E1: 15% of those labels flip at 1M nodes); ≥ 300 analysed rapid or blitz games for the owner; criticality labels stable at the chosen budget; browser throughput measured on a normal laptop.

### Slice 2 (Feb - Apr 2027): human baseline (Maia-3) and population tables

- **Prerequisites:** a written answer from CSSLab on the Maia-3 weight licence; the repo licence decided (D2); a reliability diagram of Maia-3 on chess.com rapid and bullet positions; the chess.com → Lichess rating map checked near 2300-2500.
- **Pipeline:** Maia-3 5M ONNX (10.8 MB fp16) via onnxruntime-web, own preprocessing written from the model card (no GPL code copied). Population tables from a slice of one Lichess open-database month (CC0), built offline and seeded by migration.
- **Analyses:** peer excess loss and surprising-mistake rate by context (17); reaction to surprise (18); conversion v2 (12); practical pressure after its offline validation (19); position-type weaknesses (22).
- **Training:** Maia-filtered decks, "think or play?" with foils, surprise-reply drills (21).
- **Lichess import** in the games service (reuse `[%eval]` where present). This is also the prerequisite for real-game gaze.

### Slice 3 (from May 2027): gaze

- **Setting first:** Kiebitz training sessions (guess-the-move from the player's own critical positions from slices 1-2, plus CC0 Lichess puzzles). These work for chess.com users and every time control, and the relevant region is known in advance. Lichess Board API rapid games come second. Never during chess.com play (Fair Play).
- **Pipeline:** WebEyeTrack (MIT) in a Web Worker; move-click recalibration with a per-session error figure (37); quality flags; only per-move aggregates leave the browser (`gaze_move_features` in insights). Opt-in, one-click delete, a DPIA, no emotion inference (EU AI Act Art. 3(39)).
- **Analyses:** relevance latency (35) to validate the pipeline on the owner, then threat-check share vs missed-threat mistakes (36). Tunnel vision and last-move reaction (38) follow if 35-36 show any within-player signal.
- **Exit criteria:** owner pilot (about 300 guess-the-move positions and about 30 Board API rapid games) shows a within-player difference with a CI excluding zero, or the gaze line is parked.

---

## 7. Decisions needed from the product owner

| # | Decision | Why it matters | Recommendation |
|---|---|---|---|
| D1 | Confirm the **engine-free MVP** (section 5) | Overrides the engines note (depth-12 pipeline in the MVP) and the game-patterns note (taxonomy and conversion in the MVP) | Engine-free; the final-position eval is the only stretch |
| D2 | **Repo licence** | Stockfish WASM is GPL-3.0 (source offer needed when served); Maia-3 code is AGPL-3.0 | AGPL-3.0, as the engines note suggests. Note: the repo is currently **private**; serving GPL WASM still needs a source offer |
| D3 | Ask **CSSLab** about the Maia-3 **weight** licence in writing | Hugging Face weights have no licence tag | Send before slice 2 starts |
| D4 | **Shared definitions file** (one place for Win%, error 10, blunder 15 or 20, `T_est`, time-trouble rule, session rule, `R_skill`, minimum samples, bootstrap unit) | Contradictions 1, 6-9, 12 | Create `docs/research/definitions.md` and make the code follow it |
| D5 | **Primary time control** for findings | The owner's recent play is mostly 1+0 bullet (406 of 500 games in Oct 2026), but bullet is the weakest setting for engine, Maia (no positions under 30 s) and gaze analyses | MVP: all time controls for clock and context cards. Engine slices: rapid and blitz first |
| D6 | **Owner's time zone**, and storing the browser's IANA zone per account | The morning finding assumed Europe/Lisbon with DST | Store it on the account from the MVP on |
| D7 | Owner **hand-labels 150-200 own mistakes** (about 3-4 h) | Gate for the mistake taxonomy | Do it in December, before slice 1 ships the taxonomy |
| D8 | **UX for long browser jobs** | Full history = hours of engine time | Analyse the newest 100-300 games first, the rest in the background |
| D9 | **Relabel live games with `T_est ≥ 1500 s` as classical** | chess.com lumps them into rapid | Yes |
| D10 | **Publish metric definitions** in the UI (a methods page) | It is the only defence against Audit Chess, Chessigma and similar tools copying the topics | Yes, with links to these notes |
| D11 | **Whose games** may be analysed | The app accepts any public chess.com username; gaze will add biometric data | Fine for public game data now; gaze needs opt-in, a DPIA and a privacy professional's view |
| D12 | Commit cleaned **pilot scripts** as reproducible prototypes (e.g. `tools/research/`) | The pilot numbers in the notes are not reproducible from the repo today | Yes, after the course deadline |
| D13 | `AI_USAGE.md` row for this research sweep | Required by AGENTS.md | The orchestrator adds it when committing |

---

## 8. Experiments to run now

**All three were run on 2026-11-12; results are in section 9 and in [experiments/](experiments/).**

All three run tonight on a normal Windows laptop with Python 3.12, python-chess, numpy and a native Stockfish binary from [stockfishchess.org](https://stockfishchess.org/download/). Data comes from the chess.com public API: fetch archives serially with a User-Agent that names a contact. Use the owner (`chrisaxm`) plus 3-5 public players rated 2000-2500 with at least 300 rapid or blitz games, chosen from `https://api.chess.com/pub/titled/FM` or `/pub/leaderboards`. Run one Stockfish process per core (`Threads 1`, `Hash 64`) and parallelise over positions. Use game-cluster bootstrap (2,000 resamples) for every interval. Keep scripts and data in a scratch folder; record the engine version and node budget with every number.

### E1. Is time spent related to criticality, and do fast critical moves go wrong more often?

- **Hypothesis:** for each player, relative move time rises with the benefit of computation ΔU (Russek et al.), and the error rate in critical positions is clearly higher when the player moves fast than when they slow down. If the strength of that link differs between players by more than its CI, "time vs criticality" is a personal trait worth a flagship card.
- **Data:** the last 300 rapid and 150 blitz games of `chrisaxm`, and the same for each comparison player.
- **Method:**
  1. Eligible own moves: plies 16-80; clock before the move `c ≥ 10%` of `T_est`; more than 1 legal move; Win% of the best move between 10 and 90.
  2. Move time `t = clk_prev − clk + inc`. Relative time `r = t / median(t)` over the player's own eligible moves in the same time control, clock band (Lichess bands) and phase.
  3. Stockfish MultiPV 2 at 300k nodes: `C_gap = W(best) − W(2nd)`. Stockfish depth 1: move `m₁`. `ΔU = W(best) − W(m₁)`, with `W(m₁)` from the MultiPV list or a `searchmoves` call at 300k nodes. Played-move loss `ΔW` from the same search or `searchmoves`. Win% from the Lichess formula.
  4. Trivial positions removed as in [game-decision-points.md](game-decision-points.md) (recapture on the last-move square, in check, ≤ 3 legal moves).
  5. Re-check every `ΔW ≥ 7` at 3M nodes.
  6. Outputs per player and time control: Spearman ρ(r, ΔU) and ρ(r, C_gap); the 2×2 matrix critical (`C_gap ≥ 10`) vs quiet (`C_gap < 3`) × fast (`r < 0.5`) vs slow (`r ≥ 2`), with share of moves, error rate (`ΔW ≥ 10`) and seconds per cell; non-trivial critical positions per game; positions per second.
- **Pass:** (a) ρ(r, ΔU) > 0 with a CI excluding 0 for the owner's rapid games; (b) the error rate for critical & fast minus critical & not-fast has a CI excluding 0, with ≥ 100 critical & fast moves; (c) per-player ρ or missed-alarm rates differ between at least two players with non-overlapping CIs.
- **Kill or redirect:** if (b) and (c) fail, card 9 becomes a descriptive chart and slice 1 leads with the only-move find rate by move type instead.
- **Runtime estimate:** about 30 eligible moves per game × 450 games × about 0.7 s ≈ 2.6 h single-threaded per player, about 25 min on 6 cores. The measured throughput also answers the open sizing question for slice 1.

### E2. After a loss, do results, move quality or behaviour change, and can we tell from one player's data?

- **Hypothesis:** for strong players, after-loss effects on results are too small to detect per player (intervals of ±40-80 Elo), but move-quality and behaviour measures are 2-3× more precise. A pipeline with BH and MDE should almost never raise false findings on shuffled data.
- **Data:** full rated history of `chrisaxm` (bullet, blitz, rapid) and 5 public players with ≥ 1,000 rated games each.
- **Method:**
  1. Pre-game rating = post-game rating of the previous game in the same time class (the API documents post-game ratings). `R_skill` = median pre-game rating over ±25 games. Residual `r = S − E`.
  2. Session = gap > 30 min from end to next start (start from `UTCDate`/`UTCTime`). Also run the start-to-start 5/7 min rule to see whether the session definition changes conclusions.
  3. Outcome contrast: after-loss vs after-win residual in Elo, with a session-cluster bootstrap CI and the MDE.
  4. Behaviour: share of next games started within 60 s, and share of `T_est` used on own moves 10-25, after a loss vs after a win.
  5. Quality: Stockfish at 100k nodes on own moves 8-40 with `c ≥ 10%` in games played right after a loss or a win in the same session. Compute the error rate (`ΔW ≥ 10`) and the mean ΔW per game, plus the share of critical positions (MultiPV 2, `C_gap ≥ 10`), to check that after-loss games are not simply sharper (the riskier-openings effect reported by Engel).
  6. False-positive check: shuffle previous-result labels between sessions 1,000 times per player and time control, run the full decision rule (minimum n, CI, BH) and count how often it declares a finding.
- **Pass:** (a) the quality contrast's standardised CI is at most half as wide as the outcome contrast's; (b) the shuffled-label finding rate is ≤ 10% per player.
- **Decision it informs:** if (a) holds, the slice-1 after-loss card switches from score to error rate. If (b) fails, the MVP statistics rules get stricter before launch. If no player shows anything on any measure, the card leads with "no tilt larger than X" and the stop-loss simulator.
- **Runtime estimate:** about 1,200 games × 33 positions × 0.17 s ≈ 1.9 h single-threaded, about 20 min on 6 cores; the results and behaviour parts take seconds.

### E3. Do the MVP clock cards survive the obvious confounds?

- **Hypothesis:** (a) final material is a good proxy for "winning" in flag losses; (b) the score gap between games with and without time trouble partly survives once the position at move 20 and its sharpness are controlled, so the clock card may say more than "association".
- **Data:** all of `chrisaxm`'s live games plus the 5 public players from E2.
- **Method:**
  1. For every game lost or won on time, evaluate the final position and the position 10 own moves before the flag with Stockfish at 1M nodes. Compare the material bucket (≥ +3 / −2..+2 / ≤ −3) with the Win% bucket (≥ 75 / 25-75 / ≤ 25): precision and recall of "winning".
  2. For every game reaching own move 20: Win% at own move 20 and a sharpness proxy (`C_gap` at moves 15-20 from MultiPV 2, 100k nodes). Logistic model per time control: `score ~ entered_time_trouble + self_inflicted + rating_diff (R_skill) + W_move20 + sharpness`. Compare the time-trouble coefficient with the raw one, using a game bootstrap.
  3. Check the premove detector: share of own move times at exactly 0.1 s vs 0.2 s per player and time control.
- **Pass:** (a) precision ≥ 0.85 for the "winning" bucket, otherwise the MVP uses the one-eval version (stretch item 5); (b) the time-trouble coefficient keeps ≥ 50% of its raw size with a CI excluding 0, otherwise the MVP card reports rates and onset only, with no cost statement.
- **Runtime estimate:** a few hundred flag games × 2 evals × about 1.5 s, plus about 2,000 games × 6 positions × 0.17 s: under 1 h single-threaded.

---

## 9. Experiment results (run 2026-11-12)

Real chess.com data: the owner plus five titled players (FM/CM/NM, rapid 2000-2500, seeded draw from `/pub/titled`, anonymised as P1-P5). Native Stockfish 19 (official build), about 1 h 45 min of engine time on 7 cores. Scripts and rerun instructions: [experiments/README.md](../../experiments/README.md). Full write-ups: [E1](experiments/e1-time-vs-criticality.md), [E2](experiments/e2-after-loss.md), [E3](experiments/e3-clock-confounds.md).

| Experiment | Verdict | Key numbers | Consequence |
|---|---|---|---|
| **E1** time vs criticality | (a) pass, **(b) fail, reversed**, (c) weak | Owner rapid (298 games, 5,489 moves): ρ(r, ΔU) = 0.131 [0.107, 0.155]. Critical & fast error 8.8% vs critical & not fast 26.9%: **−18.1 pp [−23.0, −13.2]**, same sign for all 4 players, also in "hidden" critical positions and after engine-difficulty controls (odds ×1.32 per doubling of r). ρ(r, ΔU) for the three 10+0 players: 0.131 / 0.137 / 0.138. | Kill rule applies: card 9 leads with the only-move find rate; no "missed alarm" claim; new candidate 47 (think time as a difficulty label). |
| **E2** after a loss | **(a) fail**, (b) borderline fail | Requeue ≤ 60 s rises after a loss for 4 of 5 players with data (owner rapid 65% vs 36%). Results: P1/P3 within ±20-40 Elo (MDE 27-33); owner bullet −71 [−120, −20], rapid +63 [+17, +113]. Quality: same standardised CI width as results on the same games; Elo-equivalent 1.9-2.8× tighter, but only 1.2-2.2× tighter than results on all games. Shuffled pages with a false finding: 9.3-12.6%. | After-loss card leads with behaviour (vs other players) and "no effect larger than X"; quality only as a secondary check; BH q = 0.05. |
| **E3** clock-card confounds | **(a) pass, (b) pass for the owner** | Material ≥ +3 vs engine Win% ≥ 75 in flag losses: precision 0.96 [0.89, 0.99], recall 0.48. Owner time-trouble coefficient after controls / raw: rapid 1.04 [0.63, 1.41], blitz 1.02 [0.71, 1.38], bullet 1.08 [0.94, 1.27]; cost sits in self-inflicted time trouble. P1 blitz shows no cost. Premove spike at exactly 0.1 s: 5-40× the 0.2 s rate. | Clock profile (card 2) is the strongest MVP card; flag count is a lower bound until the final-position eval ships; premove detector validated. |

**Ranking changes from the experiments** (applied in section 4): card 2 value 4 → 5; card 9 renamed and redirected to the find rate; card 14 reliability 3 → 4; card 25 reliability 3 → 2 (secondary check only); new card 47; statistics layer uses q = 0.05. The MVP slice is unchanged in scope; its strongest card is now the clock profile, and the after-loss card leads with behaviour.

**What the experiments did not settle:** whether think-time-based difficulty labels make better drills (card 47); whether the owner's opposite-sign after-loss results (bullet worse, rapid better) are real or a rating-curve artefact; whether the time-trouble cost survives control for the position at the onset move, not just at move 20; browser (WASM) throughput, which E1 measured only natively (about 33 s CPU per rapid game at 300k nodes).

## 10. Sources

Spot-checked for this note (fetched 2026-11-12):
- Audit Chess: https://www.auditchess.com/ and https://www.auditchess.com/chess-performance-analyzer
- Chessigma Supercoach: https://chessigma.com/supercoach
- chess-game-analyzer: https://github.com/StephanAkkerman/chess-game-analyzer
- chess.com Insights help: https://support.chess.com/en/articles/8708925-what-is-insights
- Aimchess: https://aimchess.com
- chess.com Published-Data API: https://www.chess.com/news/view/published-data-api
- romanbreyten/chess-tilt: https://github.com/romanbreyten/chess-tilt
- Russek et al., Cognitive Science 2025: https://pmc.ncbi.nlm.nih.gov/articles/PMC12553403
- Anderson, Kleinberg, Mullainathan: https://arxiv.org/abs/1606.04956

All other claims are cited in the source notes linked from each row. Owner data figures come from the pilots described in those notes, run on 2026-11-12 on the public chess.com archive of `chrisaxm`.
