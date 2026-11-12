# Personal rules with adherence tracking (habit training that is not a puzzle)

**Question:** Which simple if-then rule (stop after two losses, keep half your clock until move 20, cut long thinks, pause after captures) fits your weaknesses, how often do you actually follow it, and does following it go together with better results?

**What to measure:**

1. **Rule catalogue.** Each rule is written as an if-then plan and has an exact adherence check on imported chess.com data. Parameters come from the player's own finding (e.g. the 3× median comes from their median move time).

| Rule | Exposure (the "if") | Adherence check (the "then") | Source finding |
|---|---|---|---|
| Stop-loss: after 2 consecutive rated losses in a session, pause ≥ 30 min | 2nd consecutive loss in a session (session = gap ≤ 30 min) | Next game's start (`UTCDate`+`UTCTime`) − loss's `end_time` ≥ 30 min, or no next game that day | [psych-tilt-and-stop-loss.md](psych-tilt-and-stop-loss.md) |
| Clock checkpoint: at move 20, ≥ X% of base time left (X from the player's own wins, e.g. 50% in 10+0) | Rapid/blitz game reaching ply 40 | `[%clk]` at the player's 20th move ≥ X% of base | [clock-time-trouble.md](clock-time-trouble.md) |
| Decision deadline: no single think > 3× my median move time unless I am in a slow, quiet position | Every move with ≥ 20% base left | Count of moves with `t > 3·median(t)`; adherence = share of games with 0 or 1 such moves | [clock-long-thinks.md](clock-long-thinks.md) |
| Capture/check pause: after the opponent captures or checks, spend ≥ 3 s (blitz) / 10 s (rapid) unless the reply is forced | Opponent's move is a capture or check and the player has > 1 legal reply that is not the only recapture | Time spent on the reply ≥ threshold (from consecutive `[%clk]` values plus increment) | Missed threats (proxy, no engine) |
| Post-exit pause: on the first move after the opponent leaves my usual line, spend ≥ 2× my median | First ply out of the player's own opening tree | Time spent ≥ 2× median | [clock-opening-speed.md](clock-opening-speed.md) |
| Play window: rated <time class> only between X and Y local time | Every rated game | Local start time inside the window | [psych-time-of-day.md](psych-time-of-day.md) |
| Session cap: max N rated games per session | Every session | Session length ≤ N | [psych-session-warmup-fatigue.md](psych-session-warmup-fatigue.md) |
| Daily "sleep on it": in tactical positions, wait ≥ N min before replying | Daily move with a capture or check available to either side | Reply latency ≥ N min (latency per [clock-daily-latency.md](clock-daily-latency.md)) | Daily quick-reply errors |

2. **Adherence rate per week** = followed / exposures, with counts, shown as a simple strip (one cell per exposure).
3. **Retro-simulation before adoption** (helps choose the rule): over the last 6 months, mark the exposures where the rule was broken anyway and compare outcomes. For the stop-loss rule this is the simulator in [psych-tilt-and-stop-loss.md](psych-tilt-and-stop-loss.md) (mean Elo residual of the games the rule would have prevented). For clock rules: residual and time-trouble rate in games that met vs missed the checkpoint. **Confounded**: falling behind on the clock goes together with harder positions, so this is shown as "how your games went", never as "the rule would have gained X".
4. **Effect after adoption:** the target metric of the source finding, measured by the [improvement tracker](training-improvement-tracker.md) (split-sample baseline, untrained-type control, cluster bootstrap CI, MDE). Secondary: residual in rule-following vs rule-breaking exposures after adoption (still confounded: people break rules when they are already tilted or in trouble).

**Data needed:** chess.com monthly archives: `end_time`, `time_class`, `rated`, results, ratings, PGN tags `UTCDate`/`UTCTime` and `[%clk]` after every move. A PGN move parser (python-chess) for captures, checks and legal-move counts. No engine. The player's time zone for the play window. The rule adoption date (entered in the UI).

**Reliability:**

- Adherence is an exact count, not an estimate. The only judgement calls are the "forced reply" and "quiet position" exclusions (rule-based, documented).
- `[%clk]` has 0.1 s resolution on chess.com ([clock-and-time.md](clock-and-time.md)), so thresholds of 3 s and more are measurable. Daily `[%clk]` is not remaining time; use the latency method from [clock-daily-latency.md](clock-daily-latency.md).
- Exposures per 100 games vary: checkpoint rules get ~100 exposures per 100 games, the stop-loss rule only one per losing streak (the owner needs months for a CI on it), capture/check pauses several per game.
- Effects of if-then plans in general are real but modest: d = 0.65 in the 2006 meta-analysis ([Gollwitzer & Sheeran 2006](https://kops.uni-konstanz.de/server/api/core/bitstreams/eb48c8cf-7855-478e-90ec-1ea6d44f8252/content)), d ≈ 0.15-0.35 after bias correction in a 2024 re-analysis (secondary summary: [The Behavioral Scientist](https://www.thebehavioralscientist.com/glossary/implementation-intentions)). No chess-specific study found. So expect adherence to rise more than results.

**Effort:** **S.** Insights service: `rule(id, finding_id, kind, params_json, adopted_at, retired_at)` and an adherence query per kind over the already-parsed per-move clock table and session table that the clock and psychology analyses need anyway. UI: rule picker on a finding, adherence strip, link to the tracker.

**Prior work:**

- Stop-loss browser extensions lock the Play button after N losses but do not measure whether the rule helped ([prior-work-gap-map.md](prior-work-gap-map.md), [psych-tilt-and-stop-loss.md](psych-tilt-and-stop-loss.md)).
- Aimchess "Time Trainer" practises "when to calculate deeply and when to play a good-enough move" as a puzzle, not as a rule checked in your games ([aimchess.com](https://aimchess.com)).
- Blunder-check routines (checks, captures, threats before every move) are standard coaching advice (e.g. Aimchess's [Blunder Preventer post](https://medium.com/aimchess/to-improve-your-chess-rating-stop-blundering-duh-398694a6f00)); no tool verifies them, and their execution is not visible in a PGN. The capture/check pause is the closest observable proxy. Gaze (after the course) could observe the real routine.
- Extra deliberation improves move quality at all skill levels ([Moxley et al. 2012](https://vivo.weill.cornell.edu/display/pubid22541584)), which supports pause rules at critical moments, not a general "think longer".

**Why it's not engine review:** None of these rules is about a move. They are about clock use and session behaviour across many games, chosen from the player's own findings, and checked automatically afterwards. Game Review and Insights neither suggest such rules nor check them.

**Training link:** The rule *is* the practice: the player follows it in their normal games. Kiebitz shows adherence after every import and the target metric through the tracker. If adherence is high and the target does not move after enough data, the rule is retired and another plan is suggested; if adherence stays low (< 50% after 4 weeks; speculation), Kiebitz suggests an easier rule (e.g. "after 3 losses" instead of 2) rather than repeating the same advice.

**Verdict:** **Build for MVP.** Engine-free, small, uses data the games service already imports, and closes the loop (finding → rule → adherence → re-measure) that no competitor closes. Start with the stop-loss and the clock-checkpoint rules.
