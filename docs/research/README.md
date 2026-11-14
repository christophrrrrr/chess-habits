# Research notes

One file per candidate analysis or research question, e.g. `time-vs-criticality.md`, `gaze-threat-check.md`, `maia-human-baseline.md`.

Read [../vision.md](../vision.md) first. Every proposal must pass the test: **"Could chess.com's Game Review already tell you this?"**

## Template

```markdown
# <Analysis name>

**Question:** What does this analysis tell the player, in one sentence?

**What to measure:** The exact metric(s), and how they are computed.

**Data needed:** Games / clock / engine evals / gaze / context. Where it comes from.

**Reliability:** How many games or moves are needed before the finding is trustworthy? Known noise sources?

**Effort:** Rough size to build (S / M / L) and which service it belongs to.

**Prior work:** Do Lichess Insights, Aimchess, chess.com or published research already do this? Links.

**Why it's not engine review:** How it passes the vision test.

**Training link:** What the player should practise if this finding shows a weakness, and how we'd measure improvement.

**Verdict:** Build for MVP / later / drop, with one line of reasoning.
```

## Index

Start with [shortlist.md](shortlist.md) (synthesis, MVP slice, roadmap, decisions, experiments) and [prior-work-gap-map.md](prior-work-gap-map.md) (what every other tool already does). Verdicts are the shortlist's, after the sceptic pass; where they differ from the note's own verdict, the shortlist explains why. Overview notes do not follow the template.

| File | Topic | Verdict |
|---|---|---|
| [shortlist.md](shortlist.md) | Synthesis: gap map, ranked candidates, MVP slice, roadmap, open decisions, experiments | Overview |
| [experiments/e1-time-vs-criticality.md](experiments/e1-time-vs-criticality.md) | E1 result: time vs ΔU and criticality; fast critical moves are not the problem | Experiment (run 2026-11-12) |
| [experiments/e2-after-loss.md](experiments/e2-after-loss.md) | E2 result: after-loss results vs behaviour vs move quality; shuffled-label false-positive rate | Experiment (run 2026-11-12) |
| [experiments/e3-clock-confounds.md](experiments/e3-clock-confounds.md) | E3 result: flag-loss material proxy, time-trouble cost after position controls, premove detector | Experiment (run 2026-11-12) |
| [prior-work-gap-map.md](prior-work-gap-map.md) | What chess.com, Lichess, Aimchess, Maia, ChessBase, AI coaches and OSS already analyse; gaps G1-G10 | Overview (some gaps narrowed, see shortlist 2.1) |
| [expertise-literature.md](expertise-literature.md) | Research on chess expertise and error prediction; methodological rules | Overview |
| [engines-and-human-baseline.md](engines-and-human-baseline.md) | Eval source, browser Stockfish, Maia options, benchmarks, licences, architecture | Browser pipeline: slice 1 (not MVP) |
| [maia-human-baseline.md](maia-human-baseline.md) | Maia-3 peer expected loss and blind-spot index | Slice 2 |
| [clock-and-time.md](clock-and-time.md) | Clock overview: chess.com clock data facts, shared definitions, fit per time control | Overview |
| [clock-time-trouble.md](clock-time-trouble.md) | Time-trouble onset, self-inflicted share, where the time went, cost | **MVP** (clock-only); tax in slice 1 |
| [clock-flag-losses.md](clock-flag-losses.md) | Flag losses from winning positions, net clock points | **MVP** (material proxy) |
| [clock-opening-speed.md](clock-opening-speed.md) | Time on own-repertoire autopilot moves and after leaving the repertoire | **MVP stretch** |
| [clock-time-vs-criticality.md](clock-time-vs-criticality.md) | Time spent vs criticality: missed alarms, wasted time | Slice 1 flagship (with decision points) |
| [clock-long-thinks.md](clock-long-thinks.md) | Overthinking forced moves; long-think payoff | Slice 1 add-on |
| [clock-surprise-response.md](clock-surprise-response.md) | Time and quality after the opponent's unexpected move | Slice 2 (merge with game-surprise-reaction) |
| [clock-bullet-premoves.md](clock-bullet-premoves.md) | Premove share, cost and missed premoves in bullet | Slice 1 add-on |
| [clock-daily-latency.md](clock-daily-latency.md) | Daily chess: cost of quick replies | Later (clock format unconfirmed) |
| [game-patterns.md](game-patterns.md) | Game-pattern overview, engine pilot, statistics rules | Overview |
| [game-mistake-taxonomy.md](game-mistake-taxonomy.md) | Mistake causes: missed threat, allowed tactic, missed chance, quiet misjudgement, drift | Slice 1, after hand-label validation |
| [game-conversion-and-defence.md](game-conversion-and-defence.md) | Converting wins and saving losses against expectation | Slice 1 (needs v2 baseline) |
| [game-recurring-positions.md](game-recurring-positions.md) | Habitual weak moves in recurring positions; post-exit quality | Later, low priority (folded into opening speed and drills) |
| [game-decision-points.md](game-decision-points.md) | Non-trivial only-move find rate by move type | Slice 1 flagship (with time vs criticality) |
| [game-problem-setting.md](game-problem-setting.md) | How often your moves leave the opponent a critical position | Slice 2 (merge with practical-pressure) |
| [game-position-types.md](game-position-types.md) | Excess loss in named pawn structures and imbalances | Slice 2 |
| [game-surprise-reaction.md](game-surprise-reaction.md) | Play after surprising opponent moves, good vs bad surprises | Slice 2 |
| [practical-pressure.md](practical-pressure.md) | Difficulty created for the opponent vs faced (Maia expected human loss) | Slice 2, after offline validation |
| [structure-familiarity.md](structure-familiarity.md) | Results by familiarity with own pawn structures | Later, behind population validation |
| [psychology-and-context.md](psychology-and-context.md) | Context overview and the shared context statistics engine | Overview |
| [psych-tilt-and-stop-loss.md](psych-tilt-and-stop-loss.md) | After-loss performance, stop-loss rule simulator, behavioural tilt markers | **MVP** (simulator and requeue speed) |
| [psych-time-of-day.md](psych-time-of-day.md) | Rating-adjusted time-of-day effect with a family-wise test | **MVP stretch** |
| [psych-session-warmup-fatigue.md](psych-session-warmup-fatigue.md) | First game of a session; fatigue over a session | Warm-up: slice 1 add-on; fatigue: later |
| [psych-resignation-and-draws.md](psych-resignation-and-draws.md) | Resignation and agreed-draw quality vs a human baseline | Slice 1 |
| [training-loop.md](training-loop.md) | From finding to practice to proof; learning science; existing tools | Overview |
| [training-improvement-tracker.md](training-improvement-tracker.md) | Did the weakness shrink: split-sample baseline, control, CI, MDE | **MVP** (minimal); full in slice 1 |
| [training-personal-rules.md](training-personal-rules.md) | If-then rules with adherence counted from game data | **MVP** (clock checkpoint, stop-loss) |
| [training-own-position-drills.md](training-own-position-drills.md) | Cause-grouped drills from own critical positions; process drills | Slice 1 (threat drill), slice 2 (Maia filter) |
| [gaze-tracking.md](gaze-tracking.md) | Webcam gaze: accuracy on a board, literature, libraries, settings, privacy | Overview; slice 3 |
| [gaze-relevance-latency.md](gaze-relevance-latency.md) | Time until gaze reaches the relevant region in training sessions | Slice 3 (first gaze analysis) |
| [gaze-threat-check.md](gaze-threat-check.md) | Dwell share on the opponent's side and king zones before missed threats | Slice 3 |
| [gaze-tunnel-vision.md](gaze-tunnel-vision.md) | Staying stuck in one board region (Einstellung) | After slice 3 |
| [gaze-last-move-reaction.md](gaze-last-move-reaction.md) | Whether and how fast you look at the opponent's last move | After slice 3 |
