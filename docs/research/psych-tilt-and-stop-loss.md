# Tilt check and stop-loss rule simulator

**Question:** Do you actually play worse after a loss (or a run of losses) in the same session, and would a "stop after N losses" rule have helped you, or cost you points?

**What to measure:**

All metrics are per time class (bullet, blitz, rapid), rated games only, compared against the player's own baseline.

1. **Performance residual per game.** `r = S − E`, where `S` is the score (1 / 0.5 / 0) and `E = 1 / (1 + 10^((R_opp − R_skill) / 400))`.
   - `R_skill` is a *smoothed* estimate of the player's strength: the median of the player's pre-game ratings over the 25 games before and 25 games after (same time class, the game itself excluded). Do **not** use the raw pre-game rating: after a loss the rating is temporarily too low, so the next game looks like over-performance. The Lichess tilt study saw its naive estimate flip sign (+4.4 Elo instead of −7) for exactly this reason ([chess-tilt](https://github.com/romanbreyten/chess-tilt)).
   - Pre-game rating = the player's post-game rating in their previous game of the same time class (chess.com only gives post-game ratings, see Data needed).
   - Convert a mean residual to Elo for display: `ΔElo ≈ mean(r) / (mean(E·(1−E)) · ln(10)/400)`. Near E = 0.5, 1 percentage point ≈ 7 Elo.
2. **Session.** A new session starts when the gap between the previous game's end and this game's start is more than 30 minutes (same threshold as the Lichess study; make it a setting).
3. **Tilt contrasts** (mean residual, in Elo):
   - after a loss vs after a win, within a session;
   - after 1 / 2 / 3+ consecutive losses in the session;
   - after a loss with a quick requeue (< 2 min) vs after a loss followed by a longer break. Both groups follow a loss, so this contrast is less sensitive to rating lag than "after loss vs after win".
4. **Stop-loss rule simulator.** For each candidate rule (stop after 2 consecutive losses, after 3 consecutive, after 3 or 4 total losses in a session, after −X rating points in a session), mark the games the rule would have prevented. Report:
   - number and share of games skipped;
   - their mean residual in Elo with a 95% CI ("these games went X Elo below / above your level");
   - the rating points actually won or lost in them. Show this only as secondary context: it is biased towards "keep playing", because after losses the rating is low and partly bounces back anyway.
5. **Behavioural tilt markers.** These are continuous values, so they are much less noisy than results.
   - **Requeue speed:** median gap and share of next games started within 60 s, after a loss vs after a win.
   - **Time use:** share of the base time spent on moves 10–25, from `[%clk]`, after a loss vs after a win.
   - **Session extension:** probability of stopping after a loss vs after a win.

**Data needed:**
- chess.com monthly archives (`/pub/player/{user}/games/{YYYY}/{MM}`): `end_time`, `time_class`, `rated`, `white`/`black` `rating` and `result`, and the PGN tags `UTCDate` + `UTCTime` (start) and `[%clk]`.
- The API documentation says the per-game rating is the rating *after* the game ([chess.com Published Data API](https://www.chess.com/news/view/published-data-api)), so derive the pre-game rating from the previous game.
- No engine is needed.
- Daily games are excluded: they are not played in sessions.

**Reliability:** This is the weak point, and the UI must be honest about it.
- **Population effects are small.** Lichess, 9.4M player-games with player fixed effects: −7 Elo after one loss (95% CI −7.4 to −6.4), −24 Elo after 5+ losses in a row, and about 0 after a 30+ min break. The drop was −16 Elo under 1200 and −7 at 1600–2000; at **2000+ there was no significant drop after one loss** (about −11 after five straight) ([chess-tilt](https://github.com/romanbreyten/chess-tilt), not peer reviewed).
- **For strong players specifically**, a hierarchical Bayesian model on Lichess bullet and blitz found little evidence of a consistent effect of the previous result in the 1700–1900 and GM cohorts. Only "a small proportion" of individual players showed one ([Gee et al. 2025](https://arxiv.org/abs/2503.21713)).
- **Inside one game**, small inaccuracies are followed by more inaccuracies, while serious blunders tend to make players more careful ([Adhikari, Anatolyev & Dagaev 2023, IEEE Trans. Games](https://pages.nes.ru/sanatoly/Papers/TiltChess.htm)).
- **Detectable effect size for one player** (80% power, α = 0.05, residual SD ≈ 0.46 measured on the owner's games). Per group you need about 160 games to detect 100 Elo, about 640 games for 50 Elo, and about 2,550 games for 25 Elo.
  - So a typical 7 Elo tilt can never be shown for an individual. Chess Habits can only find **large personal effects**, or report "no effect larger than X Elo".
  - Show the minimum detectable effect next to every "no effect" result.
- **Rules before showing a finding:**
  - at least 100 games in the smaller group;
  - session-level cluster bootstrap CI (2,000 resamples) that excludes 0;
  - Benjamini–Hochberg correction across all splits shown on the page;
  - the same sign in the older and newer half of the games (out-of-sample check).
  - Optional later: shrink each personal estimate towards the population prior (empirical Bayes; the prior mean is about −7 Elo, scaled by rating band).
- **Noise sources and confounds:**
  - rating lag and regression to the mean (handled by `R_skill`);
  - **selection**: we only see games of players who chose to continue, so the most tilted players may have quit ([chess-tilt](https://github.com/romanbreyten/chess-tilt));
  - rematches against the same opponent;
  - mixing time classes inside one session;
  - long-term improvement (use the centred skill window);
  - draws.

**Pilot on the product owner's data** (chess.com `chrisaxm`, 2,290 rated bullet/blitz/rapid games, Jul 2023 to Nov 2026, fetched 2026-11-12):

| | Bullet (757) | Blitz (314) | Rapid (1,219) |
|---|---|---|---|
| After loss vs own level (skill-adjusted) | −28 Elo [−57, +4] | +47 [−3, +101] | +27 [−8, +62] |
| After win | +43 [+3, +79] | −17 [−60, +23] | −32 [−61, −6] |
| Stop after 2 consecutive losses: games skipped | 535 (71%), skipped games +19 Elo [−13, +51] | 95 (30%), +34 [−2, +96] | 122 (10%), +28 [−18, +80] |
| Stop after 3 consecutive losses: games skipped | 368 (49%), +36 [−4, +84] | 43 (14%), +5 [−16, +70] | 40 (3%), +16 [−52, +86] |
| Next game started < 60 s after a loss / after a win | 84% / 90% | 76% / 66% | **64% / 36%** |
| Share of base time used on moves 10–25, after loss / after win | 0.495 / 0.489 | 0.422 / 0.430 | **0.340 / 0.382** |

- **No outcome tilt.** Every simulated stop-loss rule would have skipped games that he played at or *above* his level. The generic "stop after 3 losses" rule built into browser extensions would have cost him rating, not saved it.
- **The behavioural markers do move.** In rapid he requeues much faster after a loss (median 42 s vs 83 s) and spends about 11% less time on moves 10–25. In his case this has not translated into worse results (yet).
- This pattern ("behaviour changes, outcomes don't") is itself a finding no tool shows. CIs are 95% cluster bootstrap by session.

**Effort:** **S** for the residual engine, tilt contrasts and rule simulator (pure SQL/pandas over game metadata) and **S** for the behavioural markers (clock parsing is shared with the clock analyses). Both belong in the insights service. The statistics engine (residual, `R_skill`, bootstrap, BH, MDE) is shared with the time-of-day and session notes.

**Prior work:**
- **Browser extensions apply fixed, non-personal rules:**
  - [Tilt Breaker](https://addons.mozilla.org/firefox/addon/tilt-breaker/) blocks new games after every loss;
  - [ChessEloShield](https://addons.mozilla.org/firefox/addon/chesseloshield/) adds a cooldown after a loss;
  - [EloGuard](https://chromewebstore.google.com/detail/eloguard-chess-tilt-prote/jeephfmfnonhlgeodhpjagafacjaalph) uses a loss limit or rating floor;
  - ChessBreak blocks after 3 consecutive losses ([author's write-up](https://nitin.is-a.dev/blog/improving_my_rating));
  - [zwischenzug](https://github.com/CodewithJha/zwischenzug) unlocks after a pulse-based cooldown.
- **Stats tools:** [Audit Chess](https://www.auditchess.com/chess-performance-analyzer) shows sessions and streaks as raw results, with no rating adjustment, CI or sample size.
- **The big platforms:** chess.com Insights ([help page](https://support.chess.com/en/articles/8708925-what-is-insights-on-chess-com)) and [Lichess Insights](https://github.com/lichess-org/lila/blob/master/modules/insight/src/main/InsightDimension.scala) have no "previous result" or session dimension. Aimchess scores six skill areas (tactics, endgame, advantage capitalization, resourcefulness, time management, opening) ([aimchess.com](https://aimchess.com)), not sessions.
- **Not found:** any tool that tests *whether a stop rule would help this player* before recommending it.

**Why it's not engine review:** It uses no move evaluation at all. It explains the player's behaviour across sessions, and Game Review only sees one game.

**Training link:**
- **Rule:** if the simulator shows a significant negative effect (for example "games after 2 consecutive losses: −60 Elo, n = 180, CI excludes 0"), suggest a personal rule: "after 2 losses in a row, take a 30-minute break or switch to puzzles". The 30 minutes come from the Lichess finding that a 30+ minute break removes the effect.
- **No effect:** if no effect is found, say so explicitly ("no tilt larger than 60 Elo; a stop rule would cost you about N games of practice"). This is also useful: it frees the player from a superstition.
- **Measure:** track adherence (sessions in which the rule was followed vs broken, read from the game data) and compare residuals of rule-breaking games against the rest over the next 1–3 months.

**Verdict:** **Build for MVP**, as part of one "context report" with the time-of-day split. It is cheap, needs no engine, and is novel in its honest, personal and testable form. The rule simulator is the actionable piece. Expect "no effect" for many 1800+ players, and design the UI so that this is a useful answer.

**Sources:**
- [chess-tilt (Lichess, 11M games)](https://github.com/romanbreyten/chess-tilt)
- [Gee et al. 2025, arXiv:2503.21713](https://arxiv.org/abs/2503.21713)
- [Adhikari et al. 2023](https://pages.nes.ru/sanatoly/Papers/TiltChess.htm)
- [Devine, Tilt and Hype in Online Chess (blog, 2014 Lichess data, no rating-lag control)](http://seandevine.org/blog/chessBlog.html)
- [chess.com Published Data API](https://www.chess.com/news/view/published-data-api)
- Extensions and tools linked above
