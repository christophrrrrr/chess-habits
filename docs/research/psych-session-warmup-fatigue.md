# Session position: warm-up and fatigue

**Question:** Do you play below your level in the first game of a session (cold start), or after many games in a row (fatigue)?

**What to measure:**

1. **Session** = consecutive games with gaps of at most 30 minutes between one game's end and the next game's start. Count games of all time classes, because a bullet binge before a rapid game still counts as fatigue. `game_index` = position of the game in its session.
2. **Residual per game** as in [psych-tilt-and-stop-loss.md](psych-tilt-and-stop-loss.md): `r = S − E(R_skill, R_opp)`, shown in Elo with a session-level cluster bootstrap CI.
3. **Warm-up contrast:** `game_index = 1` vs `game_index ≥ 2`, per time class.
4. **Fatigue curve:** residual by `game_index` bucket (1, 2–3, 4–6, 7–10, 11–20, 21+). Also by *minutes since session start* (0–30, 30–60, 60–120, 120+), which suits rapid better than game counts.
   - Fit one slope, residual ~ log(1 + game_index), instead of testing every bucket. One test is far less exposed to multiple-comparison noise.
5. **Fatigue marker from the clock:** share of base time used on moves 10–25 and the timeout-loss rate by `game_index`. Players who are tired may speed up or flag more.
6. **Session-length habit:** distribution of session lengths, plus how often sessions end on a loss vs a win.

**Data needed:**
- Game start and end timestamps, time class, ratings and results from the chess.com archives.
- `[%clk]` for the time-use marker.
- No engine.

**Reliability:**
- **Research is thin.**
  - No study found quantifies a per-game fatigue curve in online chess.
  - The Lichess tilt study controlled for "games into the session" but did not report a fatigue result ([chess-tilt](https://github.com/romanbreyten/chess-tilt)).
  - Leone et al. found move speed and accuracy shifting over the day, but no change in rating outcomes ([BPS summary](https://www.bps.org.uk/research-digest/studying-fast-chess-see-how-decision-making-varies-through-day)).
  - Anderson & Green show session ends depend on *rating* events (quitting after a new personal best), which means session length is not random ([PNAS 2018](https://pmc.ncbi.nlm.nih.gov/articles/PMC5828569)).
  - Everything about fatigue in this note is therefore a **hypothesis to test per player** (speculation until data shows it).
- **Sample size:**
  - The warm-up contrast is the most testable, because every session has a first game. A player with 600 sessions has 600 first games.
  - Long sessions are rare for rapid players. The owner has 16 rapid games at index 11+, which is too few for any claim.
  - For bullet, long sessions are common; the owner has 412 bullet games at index 11+.
- **Confounds:**
  - Time of day: first games cluster in certain hours (see [psych-time-of-day.md](psych-time-of-day.md)).
  - Rating lag inside long sessions.
  - Selection: players continue long sessions when they win.
  - Mixing time classes inside a session.
- **Pilot on the product owner's data** (`chrisaxm`):
  - First game of a session: bullet −36 Elo [−106, +39], blitz −59 [−156, +40], rapid −19 [−46, +7]. Pooled: **−23 Elo [−46, +1]** (n = 676), vs later games +5 [−10, +20].
  - The sign is the same in all three time classes, but the effect is not significant on its own. It is also partly entangled with his morning effect.
  - No fatigue pattern: bullet games 6–10 were *better* (+58 Elo), and games 11+ were around 0.
  - Median session length is 2 games (mean 3.4, max 52).

**Effort:** **S**. It uses the same engine and session table as the tilt note. Insights service.

**Prior work:**
- [Audit Chess](https://www.auditchess.com/chess-performance-analyzer) groups games into sessions and mentions results "over a long sitting" and dips such as "your third game", with raw results only (no expected score, CI or sample size).
- chess.com Insights ([help](https://support.chess.com/en/articles/8708925-what-is-insights-on-chess-com)) and [Lichess Insights](https://github.com/lichess-org/lila/blob/master/modules/insight/src/main/InsightDimension.scala) have no session dimension.
- Not found: any tool with a warm-up (first-game) analysis.

**Why it's not engine review:** It is about the player's playing *routine*, not about moves. Game Review has no notion of sessions.

**Training link:**
- **Warm-up effect found:** suggest a fixed warm-up before rated play, for example 10 puzzles or 1 unrated game at the same time control. Measure it by comparing first-game residuals in sessions with a warm-up against those without. Unrated games are visible in the API (`rated: false`), so adherence can be detected automatically.
- **Fatigue slope found:** suggest a session cap ("max N rated games / M minutes per session") and track adherence.
- **Neither found:** say so and show the minimum detectable effect.

**Verdict:** **Later.** Ship it as the second split of the context report once the engine exists, because it reuses everything. The warm-up contrast is the promising part; the fatigue curve will rarely have enough data for rapid players.

**Sources:**
- [chess-tilt](https://github.com/romanbreyten/chess-tilt)
- [Anderson & Green 2018, PNAS](https://pmc.ncbi.nlm.nih.gov/articles/PMC5828569)
- [BPS summary of Leone et al.](https://www.bps.org.uk/research-digest/studying-fast-chess-see-how-decision-making-varies-through-day)
- [Audit Chess](https://www.auditchess.com/chess-performance-analyzer)
- [chess.com Insights help](https://support.chess.com/en/articles/8708925-what-is-insights-on-chess-com)
