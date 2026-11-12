# Training loop: from finding to practice to proof

**Question:** How should a Chess Habits finding become practice for a strong (1800+) player, and how do we show, honestly, whether the weakness actually shrank?

Research sweep, 2026-11-12. This is an overview note; it does not follow the per-analysis template. The three strongest mechanisms have their own template notes:

- [training-improvement-tracker.md](training-improvement-tracker.md): measuring whether a finding improved (before/after, control, CI, minimum data).
- [training-personal-rules.md](training-personal-rules.md): habit rules (stop-loss, clock checkpoints, decision deadline) with adherence read from game data.
- [training-own-position-drills.md](training-own-position-drills.md): drill decks built from the player's own critical positions, grouped by cause, with drill formats that train the *process* (spotting threats, knowing when to think), not just the answer.

Speculation is marked as such. Web search budget ran out before every lead could be checked; claims that rest on abstracts or secondary summaries say so.

---

## Bottom line

1. **Every serious tool already turns mistakes into puzzles.** Lichess and chess.com do it per game; Aimchess, Chessable Puzzle Connect, Chessiro, Chess Tempo and several hobby projects do it across games. A "puzzles from your blunders" feature fails the vision test.
2. **What nobody does:** (a) group the drills by the *cause* Chess Habits found (missed threat, under-thinking a critical moment, surprise reply, conversion), (b) use drill formats that train the failing *process* rather than "find the best move", (c) tell apart knowledge gaps from process failures, (d) attach habit rules whose adherence is checked from the clock data, and (e) re-measure the weakness in new games with a confidence interval and a control. No product reviewed re-measures the targeted weakness ([prior-work-gap-map.md](prior-work-gap-map.md), section "Gaps").
3. **For a 2300 player most drill positions are trivial without time pressure.** The mistake was rarely "did not know"; it was "did not look" or "did not spend time here". So the drill must reproduce the condition (time limit matching the time control, the opponent's last move shown, a "think or play?" decision) and the success metric must be in-game behaviour, not drill accuracy. (Reasoning plus Moxley et al. 2012; the size of this effect for our users is untested.)
4. **The measurement is the hard part and the differentiator.** Selecting your worst category and re-measuring it makes it look better even with no training (regression to the mean). In a simulation with six mistake types that are truly identical (25% rate, 100 positions each), the "worst" type improves by **5.5 percentage points on average** in the next window with zero training, and by 5 pp or more in **52%** of runs. Any honest tracker must design this away (split-sample detection, long baseline, untrained control types).
5. **Rating is a useless success metric at this scale.** With a per-game score SD of about 0.45, the 95% CI of a performance rating is about **±61 Elo after 100 games** and ±43 after 200. Use exposure-normalised in-game rates instead.

---

## 1. What learning science says, and what transfers to chess

| Principle | Evidence | Chess-specific caveat | Use in Chess Habits |
|---|---|---|---|
| **Spacing** (distributed practice) | Meta-analysis of 839 assessments in 317 experiments: spaced study beats massed study, and the best gap grows with the retention interval ([Cepeda et al. 2006](https://pubmed.ncbi.nlm.nih.gov/16719566/)). | Shown mostly on verbal recall. Chess drills from own games risk training *recall of that position*, not recognition of new ones. | Schedule reviews (FSRS), but retire an item after it is stable and replace it with a fresh position of the same type. |
| **Retrieval practice** (testing effect) | Testing beats restudy; recall tests beat recognition tests ([Rowland 2014](https://pubmed.ncbi.nlm.nih.gov/25150680/)). Secondary summaries give g ≈ 0.50 overall, larger when the final test is a day or more later (not checked in the full paper). | Solving a position is retrieval; replaying an annotated game is restudy. | Every drill asks the player to produce a move or a judgement before any answer is shown. |
| **Interleaving** | g = 0.42 overall; larger when categories are similar to each other and items within a category vary; negative for word lists ([Brunmair & Richter 2019](https://pubmed.ncbi.nlm.nih.gov/31556629/)). | Chess positions are complex and categories (threat types) look alike, the conditions under which interleaving helps most. | Mix finding types inside a session; do not run a block of 20 "missed threat" items in a row once the player knows the type exists. |
| **Variability of practice** | More varied training makes early learning harder but generalises better ([Raviv, Lupyan & Green 2022](https://eprints.gla.ac.uk/272070)). | Supports many different positions per finding over many repetitions of the same few. | Large, refreshed decks; measure on unseen positions. |
| **Learning from high-confidence errors** | Errors made with high confidence are corrected *more* often after feedback (hypercorrection), and corrections last at least a week ([Fazio, Duke](https://dukespace.lib.duke.edu/items/d6ab09ca-f55c-4efb-9d32-2788bc5838b2)). | A fast, confident blunder by a strong player is exactly this case. | Ask "how sure are you?" (1-3) before revealing; prioritise confident misses. Speculative transfer to chess. |
| **Deliberate practice** | Serious solo study predicts current and peak rating better than tournament play or lessons ([Charness et al. 2005](https://zendy.io/title/10.1002/acp.1106)). Across domains, deliberate practice explains ~12% of performance variance, ~26% for games ([Macnamara et al. 2014](https://www.psychologie.uzh.ch/dam/jcr:658d39fe-2f4b-467f-9ae2-ffeb25caf2b6/McNamara.PsychSci.25.2014.pdf)); about a third for chess after correcting for measurement error ([expertise-literature.md](expertise-literature.md)). A 2021 paper argues individualised practice has a much larger effect (178 chess players; abstract only, not checked) ([Current Psychology](https://link.springer.com/article/10.1007/s12144-021-02326-x)). | Practice helps but is not the whole story; personalisation is the part with most upside. | Chess Habits' whole pitch is individualised practice; claims must stay modest. |
| **Extra deliberation helps everyone** | Extra thinking time improved move quality for both experts and weaker players, on easy and hard problems ([Moxley et al. 2012](https://vivo.weill.cornell.edu/display/pubid22541584)). | The question for a strong player is *where* to spend time, not whether thinking helps. | Basis for "think or play?" drills and time-budget rules. |
| **If-then plans** (implementation intentions) | Original meta-analysis: d = 0.65 over goal intentions alone, 94 tests ([Gollwitzer & Sheeran 2006](https://kops.uni-konstanz.de/server/api/core/bitstreams/eb48c8cf-7855-478e-90ec-1ea6d44f8252/content)). A 2024 re-analysis of 642 tests gives d = 0.15-0.35 after bias correction (as reported by [this summary](https://www.thebehavioralscientist.com/glossary/implementation-intentions); primary not checked). | Effects are real but small; no chess study found. | Phrase every habit rule as "If X, then Y" and track adherence from data. |

**Evidence that puzzle training raises chess rating is weak.** Puzzle and game ratings correlate (a Lichess analysis of 24,000+ players; correlation only) ([ggSayItBack](https://lichess.org/@/ggSayItBack/blog/do-puzzles-matter-a-data-analysis/twAyjQDX)). A non-peer-reviewed Woodpecker study (431,899 puzzle attempts) reports +35 Elo but warns that people who start training may already be improving ([Disco Chess](https://lichess.org/@/DiscoChessApp/blog/woodpecker-method-training-431000-puzzles-60000-rated-games-and-35-elo/yrWsFF1N), read via search summary only). Aimchess claims its personalised puzzles raise ratings "31% faster" in a 12-week randomised field experiment by UBC researchers ([aimchess.com](https://aimchess.com)); no paper, sample size or authors are linked, and we found none. Treat as a vendor claim. **Chess Habits should not promise rating gains; it should measure the targeted behaviour.**

---

## 2. How existing tools turn mistakes into practice (checked 2026-11-12)

| Tool | Source of positions | Format | Scheduling | Grouped by cause? | Re-measures in games? |
|---|---|---|---|---|---|
| Lichess "Learn from your mistakes" | One analysed game | Find a better move; best move on request; can flip to opponent's mistakes ([Lichess blog](https://lichess.org/@/lichess/blog/learn-from-your-mistakes/WFvLpiQA)) | None. Users keep asking for cross-game and spaced versions ([forum](https://lichess.org/forum/lichess-feedback/create-learn-from-your-mistakes-across-all-games)) | No | No |
| chess.com Game Review "Retry" | Key moves of one game | Replay the position, find the best move, Coach comments ([help, updated 2026-09-25](https://support.chess.com/en/articles/8584089)) | None | No | No |
| Chessable MoveTrainer | Courses (repertoire) | Play the course move | 8 levels: 4 h, 1 d, 3 d, 1 wk, 2 wk, 1 mo, 3 mo, 6 mo; a mistake resets to a short interval; each move has its own timer ([support](https://support.chess.com/en/articles/10319267-when-will-the-variations-be-ready-for-my-review)) | No | No |
| Chessable Puzzle Connect | Your chess.com mistakes | Puzzles; 10 (basic) or up to 1,000 (PRO) ([announcement, 2023](https://www.chess.com/news/view/announcing-chessable-3)) | Not stated | No (only "patterns you are likely to see") | No |
| Chess Tempo custom sets | Any tagged problems (premium) | Tactics | Fail: again in 5 min; first success: 1 day; then `gap = last_gap × gap_factor`, factor ~1.3-3 depending on your solve time vs the average ([manual mirror](https://www.gwern.net/docs/www/chesstempo.com/01756e1305cd97d8abb5e2a7380635f9ea40f4fd.html)) | No | No |
| Listudy | Opening repertoire | Each move is a card | Leitner: correct raises the card's box, wrong resets to zero ([blog](https://listudy.org/en/blog/spaced-repetition-for-chess)) | No | No |
| Aimchess | Your games plus generic | Retry Mistakes, Blunder Preventer (pick which of two moves is the blunder), Advantage Capitalization (win your lost-from-winning games vs the computer), Defender, **Time Trainer** ("when to calculate deeply and when to play good-enough"), Intuition Trainer; weekly study plan ([aimchess.com](https://aimchess.com), [Blunder Preventer post](https://medium.com/aimchess/to-improve-your-chess-rating-stop-blundering-duh-398694a6f00)) | Daily sessions; no SR documented | By skill area (6 areas), not by cause | No. A user notes Retry Mistakes pulls old, irrelevant positions and treats every non-best move as a blunder ([review](https://www.chess.com/blog/SheldonOfOsaka/aimchess-a-review)) |
| Chessiro "Smart Shuffle" | Your misplays | Puzzles "weighted toward the patterns you keep repeating"; manual advice: retire after two quick correct solves ([blog, 2026-07-19](https://chessiro.com/blog/puzzles-from-your-own-games)) | Resurfacing, intervals not given; aimed at 800-1800 | Loosely (by area) | No |
| FireChess (Feb 2026) | Up to 5,000 games | Repeated *opening* errors (e.g. "played 14 times, 70% loss") and a drill mode ([HN showcase](https://hnshowcase.com/post/47149131/firechess-find-the-chess-mistakes-you-keep-repeating)) | Not stated | Openings only | No |

**What is missing for strong players:**

1. **The wrong unit.** Tools drill "the best move in this position". For a 2300 player the position is usually easy in hindsight; the failure was not looking at the opponent's threat, not slowing down, or replying on autopilot. Nobody drills *noticing*.
2. **No time realism.** No tool sets the drill clock from the time control and the clock state of the original moment (a bullet mistake at 4 s left is a different skill from a rapid mistake at 6 min left).
3. **No human filter.** Aimchess counts every non-best move; chess.com's Retry wants "the best move". A strong player needs only the positions where players of their level usually find a good move (Maia-filtered), and should get credit for any move that holds.
4. **No cause grouping**, so the player cannot connect "my threat blindness" with a practice set and a number that should go down.
5. **No knowledge-vs-process diagnosis.** No tool asks: if you solve this calmly in the drill but missed it in the game, the problem is process, not knowledge.
6. **No habit layer with verification.** Stop-loss blockers lock the Play button but do not check whether the rule helped ([psych-tilt-and-stop-loss.md](psych-tilt-and-stop-loss.md)). Aimchess's Time Trainer is a puzzle, not a rule checked in your games.
7. **No proof.** No tool shows "your missed-threat rate went from X to Y, CI ..., compared with untrained types".

---

## 3. Chess Habits design: the loop

```
games (import) ──► findings (insights) ──► plan: drills + rules ──► practice (browser)
      ▲                                                                   │
      └────────── new games re-measure the finding metric ◄───────────────┘
```

Each finding gets exactly one **target metric** (in-game, exposure-normalised), a **baseline**, and a **plan** made of up to two parts: a drill deck (for knowledge and recognition) and a personal rule (for habits). The tracker then reports the target metric on new games only.

### 3.1 Drills from the player's own critical positions

Full design in [training-own-position-drills.md](training-own-position-drills.md). Summary:

- **Item selection:** player to move, the played move lost ≥ 10 Win% points (Lichess Win% formula), at least one move holds within 3 Win% of best, and **players of the player's level usually find a holding move** (Maia-2/3 probability of a holding move ≥ 0.5 at the player's rating). Positions that only an engine solves are excluded (vision principle 2). Thresholds are starting values, to be tuned.
- **Grouped by cause**, each with its own format:

| Finding type | Drill format (what the player does) | Why this format |
|---|---|---|
| Missed opponent threat | Step 1: "What does your opponent threaten?" Play the *opponent's* move on the board. Step 2: find your move. | Trains the threat check itself. A puzzle "find the best move" skips step 1. |
| Missed own chance | Find the move; any move within 3 Win% of best counts. | Classic, but human-filtered and with lenient acceptance. |
| Critical moment under-thought (fast move in a position where only one move holds; see [clock-time-vs-criticality.md](clock-time-vs-criticality.md)) | "Think or play?" in 2 s (binary). Then solve with a *minimum* think time. Mixed with non-critical positions from the same games as foils. | Trains recognising when to spend time, which is the actual failure. New. |
| Reply to a surprising move ([clock-surprise-response.md](clock-surprise-response.md)) | Animate the opponent's last move, then ask for the reply. | Reproduces the trigger. |
| Failed conversion | Play out the winning position against Maia at the opponent's rating, with the clock you had. | Format exists (Aimchess vs computer); Chess Habits' addition is the human opponent model and the clock. |
| Time-trouble error | Same position, clock set to what you had (e.g. 8 s), bullet-style. | Time realism. |

- **Time limits follow the time control** of the source game: bullet items 3-5 s, blitz 10-15 s, rapid 30-60 s, classical and daily untimed with "write your candidate moves first". (Starting values, speculation.)
- **Knowledge vs process split:** the first time an item is shown, it is solved untimed. Solved untimed but missed in the game = **process failure** (did not look / did not spend time). Not solved untimed = **knowledge gap** (pattern unknown). The ratio per finding type tells the player whether to study (books, model games) or to change habits (rules). New diagnostic; reliability unknown.
- **Scheduling:** FSRS (open source, MIT, `pip install fsrs`, default desired retention 0.9) ([py-fsrs](https://github.com/open-spaced-repetition/py-fsrs); a ~100-line implementation exists, [Borretti](https://borretti.me/article/implementing-fsrs-in-100-lines)). Map outcomes to FSRS ratings: wrong = Again, correct but over the time limit = Hard, correct within limit = Good, correct in under half the limit = Easy (Chess Tempo uses solve time the same way). **Retire** an item after 3 consecutive Good/Easy answers once its interval exceeds 21 days, and replace it with a fresh position of the same type. Reason: we want pattern recognition on new positions, not memory of 30 positions.
- **Transfer probes:** about 1 in 5 items per session is a *probe*: a never-seen position of the same type, from newer games or from a held-out half of the player's positions. Probe accuracy and probe solve time are the drill-level indicator. Accuracy on reviewed items is shown, but never as evidence of improvement.

### 3.2 Habit training that is not a puzzle

Full design in [training-personal-rules.md](training-personal-rules.md). Rules are written as if-then plans, chosen from the findings, and checked automatically on every imported game. Examples that are observable from chess.com data without an engine:

| Rule (if-then) | Adherence check from data | Linked finding |
|---|---|---|
| If I lose 2 rated games in a row in a session, then I pause ≥ 30 min. | Gap between the 2nd loss's `end_time` and the next game's start (`UTCDate`+`UTCTime`). | Tilt ([psych-tilt-and-stop-loss.md](psych-tilt-and-stop-loss.md)) |
| If it is move 20 in rapid, I have ≥ 50% of my base time. | `[%clk]` at ply 40/41. | Time trouble ([clock-time-trouble.md](clock-time-trouble.md)) |
| If a think passes 3× my median move time and I am not lost, I play my best candidate. | Count of moves above the deadline. | Long thinks ([clock-long-thinks.md](clock-long-thinks.md)) |
| If the opponent captures or checks, I spend ≥ 3 s (blitz) / 10 s (rapid) before replying, unless the recapture is forced. | Clock time on replies to captures/checks (PGN parse, no engine). Forced = single legal move or only recapture. | Missed threats (proxy) |
| If I play rated rapid, then only between X and Y o'clock. | Local start time. | Time of day ([psych-time-of-day.md](psych-time-of-day.md)) |
| Daily: if the position has a capture or check available to either side, I wait ≥ N minutes before replying. | Reply latency ([clock-daily-latency.md](clock-daily-latency.md)). | Quick-reply errors |

A "blunder-check routine" (before each move: checks, captures and threats for the opponent) is standard coaching advice, but **its execution cannot be observed** from the PGN. Only a proxy is observable (no sub-2-second moves in non-forced positions in rapid). Gaze tracking (after the course) could observe it directly: share of moves preceded by a look at the opponent's active pieces. We found no controlled study showing that a blunder-check routine reduces blunders; Moxley et al. 2012 only shows that extra deliberation improves move quality.

### 3.3 Measuring improvement

Full design in [training-improvement-tracker.md](training-improvement-tracker.md). Key rules:

1. **Target metric = exposure-normalised in-game rate**, e.g. missed threats per 100 positions in which the opponent had a real threat, or time-trouble entries per 100 rapid games. Never raw counts (they move with the number and kind of games played) and never rating.
2. **Regression to the mean:** we pick findings *because* they look bad, so they will look better next time anyway ([Barnett et al. 2005](https://doi.org/10.1093/ije/dyh299)). Our simulation: 6 identical types, true rate 25%, 100 positions each, select the worst, re-measure: mean "improvement" 5.5 pp, ≥ 5 pp in 52% of runs. Defences:
   - **Split-sample detection:** detect the finding on one half of the games (e.g. odd game IDs), compute the baseline on the other half. The baseline is then not inflated by selection.
   - **Long baseline:** the last 200-500 relevant positions, not the window where the problem first showed.
   - **Control types:** report the change in the trained type *minus* the change in untrained types over the same period (difference-in-differences). This removes general form, engine-depth or opponent-pool shifts.
   - **Shrinkage:** show finding rates shrunk toward the player's overall rate (beta-binomial / empirical Bayes) so small categories do not look extreme.
3. **Confidence intervals by game-level cluster bootstrap** (positions within a game are correlated), consistent with the other notes ([clock-and-time.md](clock-and-time.md), [psychology-and-context.md](psychology-and-context.md)). Wilson intervals for quick single-proportion displays ([Wilson score interval](https://en.wikipedia.org/wiki/Binomial_proportion_confidence_interval#Wilson_score_interval)).
4. **Minimum data:** to detect a change from 30% to ~21% (9 pp) with 80% power needs about **400 exposure positions per window**; 200 per window only detects ~13 pp. With clustering (about 3 exposures per game, intra-game correlation ~0.1, design effect ~1.2; speculation) that is roughly 20% more. Show the **minimum detectable effect** next to every "no clear change".
5. **Honest presentation:** four states only: *Too early* (below the minimum), *No clear change*, *Likely improved*, *Likely worse*. Always show n, the CI, the control trend, and the sentence "This shows a change, not that the training caused it."

### 3.4 Fit per time control

| Time control | Best training lever (speculation, to be validated with the tracker) | Drill timer | Typical rules |
|---|---|---|---|
| Bullet (1+0, 2+1) | Pattern speed, premove discipline, flag handling | 3-5 s | Premove only forced recaptures; simplify when ahead on the board and behind on the clock ([clock-flag-losses.md](clock-flag-losses.md)) |
| Blitz (3+0 to 5+5) | Threat noticing after captures/checks; surprise replies | 10-15 s | Minimum pause after capture/check; stop-loss |
| Rapid (10+0 to 30+0) | Time allocation to critical moments; long-think control | 30-60 s, plus "think or play?" | Clock checkpoint at move 20; 3× median deadline |
| Classical | Calculation, knowledge gaps | Untimed, candidates first | Candidate-move list before long thinks |
| Daily | Quick replies in tactical positions | Untimed | "Sleep on it" latency rule |

The owner's data (2,670 games: rapid 1,310, bullet 846, blitz 461, daily 53) supports measurement for rapid and bullet now; blitz needs 6-12 months for most per-type metrics; daily needs pooling or will rarely leave "Too early" ([prior-work-gap-map.md](prior-work-gap-map.md)).

---

## 4. Candidate analyses evaluated

Scores 1-5. Novelty = how far beyond existing tools; Value = for 1800+ players; Reliability = how trustworthy the output is at realistic sample sizes. Effort S/M/L. MVP = feasible in the course slice (by 2026-11-24, no engine) or the first slice right after.

| # | Candidate | Exists in | Nov | Val | Rel | Eff | Verdict |
|---|---|---|---|---|---|---|---|
| 1 | **Improvement tracker** with split-sample baseline, untrained-type control, cluster bootstrap CI, MDE, 4 honest states | None found (chess.com "Past Performance" compares general stats only) | 5 | 5 | 4 | M | **MVP** (on engine-free metrics first) |
| 2 | **Personal if-then rules with adherence checked from game data** (stop-loss, clock checkpoint, think deadline, capture/check pause, play window) | Stop-loss browser blockers (no measurement) | 4 | 4 | 4 | S | **MVP** |
| 3 | **Cause-grouped drill decks from own positions**, Maia-filtered, lenient acceptance, FSRS with retirement | Aimchess Retry Mistakes, Chessable Puzzle Connect, Chessiro, Chess Tempo (none grouped by cause or human-filtered) | 3 | 4 | 3 | M | later (needs browser engine + Maia) |
| 4 | **Threat-identification drill** (play the opponent's threat first, then your move) | None found | 4 | 5 | 4 | M | later (first engine feature) |
| 5 | **"Think or play?" criticality recognition drill** with foils | Aimchess Time Trainer is related but generic positions | 5 | 5 | 3 | M | later |
| 6 | **Knowledge-vs-process split** (solved untimed but missed in game) | None found | 5 | 4 | 3 | S (once 3 exists) | later |
| 7 | **Transfer probes** (accuracy on unseen positions of the same type) | None found | 4 | 4 | 3 | S | later (with 3) |
| 8 | **Time-control-matched drill clocks** (bullet 3-5 s ... rapid 30-60 s, or the original clock) | Chess Tempo uses solve time for scheduling, not per source time control | 3 | 3 | 4 | S | later (feature of 3) |
| 9 | Confidence rating before reveal (hypercorrection), prioritise confident misses | None found in chess tools | 3 | 3 | 2 | S | later |
| 10 | Conversion play-out vs Maia at opponent rating with original clock | Aimchess Advantage Capitalization (vs computer) | 2 | 3 | 3 | M | later (format inside 3, not a feature) |
| 11 | Interleaved "contrast pairs" (your habitual move works here, fails there) | None found | 4 | 3 | 2 | L | later (research first) |
| 12 | Gaze-verified blunder check (look at opponent's active pieces before moving) | None found | 5 | 4 | 2 | L | later (after course, gaze research) |
| 13 | Dose-response view (reviews done vs change in target metric) | None found | 3 | 2 | 2 | S | later (weak causal evidence) |
| 14 | Single-game "retry your mistakes" | Lichess, chess.com | 1 | 2 | 4 | S | drop |
| 15 | Generic weekly study plan | Aimchess, Chessigma, Chessiro | 1 | 2 | 3 | M | drop |
| 16 | Opening-repertoire SR from own deviations | Chessable, Chessbook, Listudy, FireChess | 1 | 3 | 4 | M | drop (link out; [clock-opening-speed.md](clock-opening-speed.md) covers the time angle) |
| 17 | Rating change as the success metric | chess.com, everyone | 1 | 1 | 1 | S | drop (±61 Elo CI after 100 games) |
| 18 | Drill accuracy on reviewed items as proof of improvement | Implicit in all SR tools | 1 | 1 | 1 | S | drop (measures memory of the item) |

---

## 5. Suggested build order

1. **Course MVP (by 2026-11-24):** in the insights service, a `finding` with a target metric and baseline, a `rule` with adherence, and the tracker view for two engine-free findings: time-trouble entry rate (rapid) and post-loss residual / stop-loss rule. This gives the full loop (finding → rule → re-measure) without an engine and is a real "feature beyond CRUD".
2. **First slice after the course:** browser Stockfish evals → threat-identification drills and missed-own-chance drills with FSRS, knowledge-vs-process split, transfer probes.
3. **Then:** Maia filter for "learnable" positions, "think or play?" drills (needs criticality from [clock-time-vs-criticality.md](clock-time-vs-criticality.md)), surprise-reply drills.
4. **After gaze research:** observable blunder-check habit.

Data model sketch (insights DB; all fits within two services, no queues, no scheduled jobs: due dates and measurements are computed when the UI asks):

- `finding(id, account_id, type, time_class, target_metric, detected_on_half, baseline_value, baseline_n, baseline_ci_low, baseline_ci_high, created_at)`
- `rule(id, finding_id, kind, params_json, adopted_at, retired_at)`
- `drill_item(id, finding_id, fen, side_to_move, prompt_type, accepted_moves_json, source_game_id, ply, time_limit_s, is_probe, fsrs_state_json, due_at, retired_at)`
- `review(id, drill_item_id, answered_at, move_uci, correct, ms_taken, confidence, fsrs_rating)`
- `measurement(id, finding_id, window_from, window_to, value, n_exposures, n_games, ci_low, ci_high, control_delta, mde, state)`

---

## Open questions

1. Do drills from a player's own positions transfer to new positions better than generic themed puzzles for 2000+ players? Nobody has published this; Aimchess's "31% faster" claim has no paper. Chess Habits could test it on its own users with a randomised split (half of a finding's positions drilled, half held out as probes).
2. What share of a strong player's critical mistakes are process failures (solved untimed) vs knowledge gaps? If it is very high, drills should mostly be "noticing" drills and rules, not puzzles.
3. How many exposure positions per type does a 2300 player produce per 100 games (e.g. opponent-threat positions)? This decides how long "Too early" lasts. Needs the browser engine run on the owner's games.
4. Which acceptance threshold (3 Win%? 5?) feels fair to strong players and still trains the right thing?
5. Does the knowledge-vs-process split stay stable on re-test, or does the first untimed attempt already change the answer (the player has seen the game)?
6. Can rules be shown at the moment of play without our own board (chess.com is the playing interface)? Until gaze/own board exists, the loop relies on a weekly adherence report.
7. Is the Lichess puzzle database (CC0 per [database.lichess.org](https://database.lichess.org/)) usable as a source of extra probe positions per theme, and do its themes map to Chess Habits finding types?

## Sources

- Cepeda et al. 2006, Distributed practice in verbal recall tasks: https://pubmed.ncbi.nlm.nih.gov/16719566/
- Rowland 2014, The effect of testing versus restudy on retention: https://pubmed.ncbi.nlm.nih.gov/25150680/
- Brunmair & Richter 2019, Similarity matters: interleaved learning meta-analysis: https://pubmed.ncbi.nlm.nih.gov/31556629/
- Raviv, Lupyan & Green 2022, How variability shapes learning and generalization: https://eprints.gla.ac.uk/272070
- Fazio, Understanding the hypercorrection effect: https://dukespace.lib.duke.edu/items/d6ab09ca-f55c-4efb-9d32-2788bc5838b2
- Charness et al. 2005, The role of deliberate practice in chess expertise: https://zendy.io/title/10.1002/acp.1106
- Macnamara, Hambrick & Oswald 2014: https://www.psychologie.uzh.ch/dam/jcr:658d39fe-2f4b-467f-9ae2-ffeb25caf2b6/McNamara.PsychSci.25.2014.pdf
- Current Psychology 2021, individualised practice in chess (abstract only): https://link.springer.com/article/10.1007/s12144-021-02326-x
- Moxley, Ericsson, Charness & Krampe 2012: https://vivo.weill.cornell.edu/display/pubid22541584
- Gollwitzer & Sheeran 2006: https://kops.uni-konstanz.de/server/api/core/bitstreams/eb48c8cf-7855-478e-90ec-1ea6d44f8252/content ; 2024 re-analysis as summarised at https://www.thebehavioralscientist.com/glossary/implementation-intentions
- Barnett, van der Pols & Dobson 2005, Regression to the mean: https://doi.org/10.1093/ije/dyh299
- py-fsrs: https://github.com/open-spaced-repetition/py-fsrs ; Implementing FSRS in 100 lines: https://borretti.me/article/implementing-fsrs-in-100-lines
- Chessable review intervals: https://support.chess.com/en/articles/10319267-when-will-the-variations-be-ready-for-my-review
- Chessable 3.0 / Puzzle Connect: https://www.chess.com/news/view/announcing-chessable-3
- Chess Tempo spaced repetition (manual mirror): https://www.gwern.net/docs/www/chesstempo.com/01756e1305cd97d8abb5e2a7380635f9ea40f4fd.html ; manual: https://ChessTempo.com/manual/en/manual.html
- Listudy spaced repetition: https://listudy.org/en/blog/spaced-repetition-for-chess
- Lichess, Learn from your mistakes: https://lichess.org/@/lichess/blog/learn-from-your-mistakes/WFvLpiQA ; forum request: https://lichess.org/forum/lichess-feedback/create-learn-from-your-mistakes-across-all-games
- chess.com Game Review help: https://support.chess.com/en/articles/8584089
- Aimchess: https://aimchess.com ; review: https://www.chess.com/blog/SheldonOfOsaka/aimchess-a-review ; Blunder Preventer: https://medium.com/aimchess/to-improve-your-chess-rating-stop-blundering-duh-398694a6f00
- Chessiro: https://chessiro.com/blog/puzzles-from-your-own-games
- FireChess: https://hnshowcase.com/post/47149131/firechess-find-the-chess-mistakes-you-keep-repeating
- Puzzle vs rating analyses: https://lichess.org/@/ggSayItBack/blog/do-puzzles-matter-a-data-analysis/twAyjQDX ; https://lichess.org/@/DiscoChessApp/blog/woodpecker-method-training-431000-puzzles-60000-rated-games-and-35-elo/yrWsFF1N
- Lichess open database (CC0): https://database.lichess.org/
- Own calculations (2026-11-12, Python): MDE for two proportions `(1.96+0.84)·√(p(1−p)·2/n)`; Elo SE `0.45/√N / (0.25·ln10/400)`; regression-to-the-mean simulation, 4,000 runs, 6 types × 100 positions, true rate 25%.
