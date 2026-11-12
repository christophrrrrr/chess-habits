# Psychology and context: overview

Research sweep, 2026-11-12. Covers:
- tilt;
- session length and fatigue;
- time of day and day of week;
- rating difference;
- round numbers and personal bests;
- rematches;
- resignation and draw habits.

Each strong candidate has its own note:

- [psych-tilt-and-stop-loss.md](psych-tilt-and-stop-loss.md): post-loss performance, a stop-loss rule simulator, and behavioural tilt markers.
- [psych-time-of-day.md](psych-time-of-day.md): rating-adjusted hour and weekday effects with a family-wise test.
- [psych-session-warmup-fatigue.md](psych-session-warmup-fatigue.md): first game of a session (warm-up) and fatigue.
- [psych-resignation-and-draws.md](psych-resignation-and-draws.md): resignation and draw-agreement quality against a human, rating- and clock-conditioned baseline.

## Answer in short

1. **What is new:** existing tools show *raw* context splits. chess.com Insights has results by time of day, day of week and opponent rating; [Audit Chess](https://www.auditchess.com/chess-performance-analyzer) shows sessions and streaks; browser extensions block play after losses. None of them:
   - adjusts for opponent strength and rating lag;
   - says whether a pattern is real (CI, minimum sample, multiple-comparison control);
   - tests a rule (for example "stop after 2 losses") against the player's own history before recommending it.

   That combination is the Kiebitz gap. One more analysis exists nowhere: **resignation and draw decisions measured against how players of your level score from that position**.
2. **Population effects are small, and smallest for strong players.**
   - Lichess tilt is about −7 Elo after a loss and −24 after 5+ losses in a row. For 2000+ players there is no significant effect after a single loss, and a 30+ minute break removes the effect ([chess-tilt, 9.4M player-games](https://github.com/romanbreyten/chess-tilt)).
   - A hierarchical Bayesian study of 1700–1900 and GM accounts found little consistent effect of the previous result; only a few individuals showed one ([Gee et al. 2025](https://arxiv.org/abs/2503.21713)).
   - Time of day changes move speed and accuracy, but not rating outcomes on average ([Leone et al., Cognition](https://www.sciencedirect.com/science/article/abs/pii/S0010027716302414)).
   - **Implication:** Kiebitz must look for *large personal* effects and must say "no effect ≥ X Elo" convincingly. Expect many 1800+ users to get that answer for tilt.
3. **Per-player statistical power is the binding constraint.** The per-game residual SD is about 0.46. With 80% power at α = 0.05, each group needs about 160 games to detect 100 Elo, 640 for 50 Elo, and 2,550 for 25 Elo.
4. **A pilot on the product owner's own games** (`chrisaxm`, 2,290 rated games) found:
   - **one real-looking personal effect:** rated rapid between 06:00 and 12:00 local time scores **−155 Elo** against his level (n = 82, CI −212 to −101, family-wise permutation p = 0.003, the same sign in 2023–24 and 2025–26);
   - **no outcome tilt.** Every generic stop-loss rule would have removed games he played at or above his level;
   - **clear behavioural tilt markers** in rapid: after a loss he starts the next game within 60 s 64% of the time (36% after a win) and spends about 11% less time on moves 10–25;
   - a resignation pattern worth checking with the engine: in rapid he resigns at a median material deficit of −1, while his opponents resign to him at −3.

## Shared method: the context engine

All outcome-based splits use the same engine. Build it once in the insights service.

| Step | Definition |
|---|---|
| Pre-game rating | chess.com gives *post*-game ratings per game ([API docs](https://www.chess.com/news/view/published-data-api)), so use the player's rating in the previous game of the same time class. Lichess PGNs give pre-game ratings directly. |
| Skill baseline `R_skill` | Median pre-game rating over ±25 neighbouring games of the same time class, excluding the game itself. This removes the rating-lag bias: a naive model flipped the sign of the Lichess tilt estimate ([chess-tilt](https://github.com/romanbreyten/chess-tilt)). |
| Expected score | `E = 1/(1+10^((R_opp − R_skill)/400))`. chess.com uses Glicko ([help](https://support.chess.com/en/articles/8566476-how-do-ratings-work-on-chess-com)); RD per game is not in the archive, so the plain Elo curve is an approximation. The Elo curve is also miscalibrated at large gaps ([Sonas](https://en.chessbase.com/post/the-elo-rating-system-correcting-the-expectancy-tables)), which matters only for rating-gap splits. |
| Residual | `r = S − E`. Display as Elo: `mean(r) / (mean(E(1−E))·ln10/400)`, about 7 Elo per percentage point near E = 0.5. |
| Session | New session after a gap of more than 30 min (end of one game to start of the next), across all time classes. |
| Uncertainty | 95% CI by **cluster bootstrap over sessions** (2,000 resamples). Games in a session are not independent. |
| Multi-bucket dimensions | One family-wise **permutation test** per dimension: shuffle labels between sessions and compare the observed max |bucket residual| with the shuffled distribution. |
| Many findings on one page | **Benjamini–Hochberg** at q = 0.10 across all displayed splits. |
| Minimum data | Show a finding only with at least 100 games in the smaller group. Otherwise show "not enough data" with the **minimum detectable effect** `MDE ≈ 2.8·0.46·√(1/n₁+1/n₂)` converted to Elo. |
| Out-of-sample check | The effect must have the same sign in the older and newer half of the games; confirm again on games played after the finding was shown. |
| Later | Empirical-Bayes shrinkage towards population priors (for example tilt about −7 Elo) once Kiebitz has many users. |

Output labels: **Finding** (passes everything), **No effect larger than X Elo** (enough data, CI includes 0), **Not enough data** (n below the minimum).

Practical notes:
- **Time zone.** The chess.com public API has no time-zone field. Store the browser's IANA zone and convert with DST. Python's `zoneinfo` needs the `tzdata` package on Windows; the pilot failed without it.
- **API fields.** The documented archive fields omit `rated` and `time_class`, but the real JSON contains them. On 2026-11-12 the keys were: `accuracies, black, eco, end_time, fen, initial_setup, pgn, rated, rules, tcn, time_class, time_control, url, uuid, white`. The PGN has `UTCDate`/`UTCTime` (start), `EndDate`/`EndTime`, `Termination` and `[%clk]`.
- **Exclusions.** Exclude variants (`rules != chess`), unrated games (keep them only as the warm-up and adherence signal) and daily games from all session analyses.

## Candidates evaluated

Scores are 1–5, where 5 is best. Novelty means "no existing tool does it". Reliability means trustworthy for one player with a few hundred to a few thousand games.

| # | Candidate | Exists in | Novelty | Value 1800+ | Reliability | Effort | Verdict |
|---|---|---|---|---|---|---|---|
| 1 | Post-loss / loss-streak performance, rating-adjusted with MDE | Audit Chess (raw streaks); extensions assume it | 3 | 3 | 2 | S | **MVP** (inside context report) |
| 2 | Stop-loss rule simulator + adherence tracking | none found (extensions use fixed rules) | 5 | 4 | 3 | S | **MVP** |
| 3 | Behavioural tilt markers (requeue speed, time use, stopping after loss) | none found | 5 | 3 | 4 | S | Later (requeue speed can ship in MVP, it needs only timestamps) |
| 4 | Time of day, rating-adjusted, family-wise test | chess.com Insights Calendar (raw, Diamond); Audit Chess (raw) | 3 | 4 | 3 | S | **MVP** |
| 5 | Day of week | chess.com Insights Calendar; Audit Chess | 2 | 2 | 2 | S | Drop (optional switch later) |
| 6 | Warm-up: first game of session | none found | 4 | 3 | 3 | S | Later |
| 7 | Fatigue: residual vs game index / minutes in session | Audit Chess (raw "long sitting") | 3 | 3 | 2 | S | Later |
| 8 | Rating difference ("fear of higher-rated", playing down) | Lichess Insights "Opponent strength"; chess.com Insights "results by opponent rating" | 1 | 2 | 2 | M | Drop |
| 9 | Round numbers / personal best (quitting, performance near thresholds) | none as a product; research only | 3 | 2 | 2 | S | Drop (maybe a fun fact) |
| 10 | Rematch behaviour | none found | 2 | 1 | 1 | S | Drop (control variable in #1) |
| 11 | Resignation quality vs rating- and clock-conditioned human expected score | none found (only counts by method) | 5 | 4 | 4 | M | **Later, first after MVP** |
| 12 | Agreed-draw quality (agreed when better or worse) | none found | 4 | 2 | 2 | M | Later (bundle with #11) |
| 13 | Draw-offer behaviour (offers, declines) | none; offers not in chess.com data | — | 2 | 1 | — | Drop (not observable) |
| 14 | Playing on too long in lost positions | none found | 3 | 1 | 3 | M | Drop (cheap online, little to gain) |

### Why the dropped ones are dropped

- **Rating difference (#8).**
  - Existing tools already show results by opponent rating, so it fails the vision test.
  - Matchmaking keeps most games within ±50 points (70% of the owner's), so there is little contrast.
  - Any "you underperform against stronger players" pattern is confounded by the miscalibration of the Elo/Glicko expectation at large gaps: Sonas found actual results match about 5/6 of the formula's gap ([ChessBase](https://en.chessbase.com/post/the-elo-rating-system-correcting-the-expectancy-tables)).
  - The owner's pilot shows the problem: blitz against +50 to +150 opponents gave −93 Elo [−161, −12] (n = 56), but this is one of more than 100 comparisons and would not survive correction.
  - The "opponent identity" effect is also weak in field data: a lab-predicted stereotype-threat effect did not appear in 5.5M FIDE games ([Stafford 2018](https://eprints.whiterose.ac.uk/121102/)).
  - It would only be worth building with a population-calibrated expectation curve.
- **Round numbers and personal bests (#9).**
  - The research is solid. On FICS, the probability of quitting jumps 4.5 percentage points (about 20%) right after a new personal best, and ratings ending in 01 see 3.5 points more quitting than ratings ending in 99. Players also over-perform by about 1 percentage point near their personal best ([Anderson & Green 2018, PNAS](https://pmc.ncbi.nlm.nih.gov/articles/PMC5828569)).
  - The owner shows the same quitting pattern: P(stop) is 0.39 after crossing a hundred upward vs 0.29 otherwise (n = 103).
  - But this is rating-protection *behaviour*, not a skill weakness, and it gives no training action. His rapid residual within 25 points of his personal best is −61 Elo (n = 338), which is mostly regression to the mean at rating peaks rather than "rating anxiety".
- **Rematch (#10).** It is rare: the owner has 112 rematches across 3.3 years, which is too few. Use it as a control in tilt; the Lichess tilt effect grew to −8.7 Elo when rematches were excluded ([chess-tilt](https://github.com/romanbreyten/chess-tilt)).
- **Draw offers (#13).** chess.com result codes include `agreed` but no offer events ([API](https://www.chess.com/news/view/published-data-api)). Whether Lichess exports draw offers was not verified.

## Fit per time control

| Time control | Best analyses | Why |
|---|---|---|
| Bullet | #1/#2 tilt and stop-loss simulator, #7 fatigue, #3 requeue speed | Many games per session (owner: 412 bullet games at session index 11+), so the most power for session effects. Few resignations (most games end by flag or mate). |
| Blitz | #1/#2, #4 time of day, #11 resignation (clock-aware) | A mix of session volume and meaningful resignations. |
| Rapid | #4 time of day, #6 warm-up, #11/#12 resignation and draws, #3 behavioural markers | Short sessions (median 2 games), so tilt contrasts are underpowered, but many sessions give many first games. Many resignations (owner: 460). |
| Classical | #4, #11 only, over long histories | Few games. chess.com's archive `time_class` showed only bullet/blitz/rapid/daily in the owner's data, so classical analyses wait for Lichess. |
| Daily | #11 resignation only | No sessions and no move timestamps, so the context splits do not apply. |

## Recommendation for the MVP (deadline 2026-11-24)

Build one **"Context report"** endpoint in the insights service. It needs no engine, no new data sources and no extra containers; it uses only game metadata the games service already imports.

1. Context engine (residual, `R_skill`, sessions, cluster bootstrap, permutation, BH, MDE): about 200 lines of numpy and pandas, easy to unit-test for the 70% coverage rule.
2. Three cards, each labelled Finding / No effect ≥ X / Not enough data:
   - **After a loss** (#1), with the **stop-loss rule simulator** (#2), plus requeue speed after a loss vs a win (#3, timestamps only);
   - **Time of day** (#4);
   - each card ends with a suggested rule and, once adopted, an adherence count.
3. Post-MVP order: #11 resignation quality (needs browser Stockfish and an offline lookup table built from the [Lichess database](https://database.lichess.org/), CC0), then #6 warm-up, #3 time-use markers and #7 fatigue.

## Open questions

- Where should the 30-minute session threshold sit for rapid? Should it be relative to time control (for example 3× the base time)? Gee et al. used start-to-start gaps of 5 min (bullet) and 7 min (blitz).
- How many Kiebitz users are needed before empirical-Bayes shrinkage beats the published priors? Can priors be borrowed from the Lichess open database instead (CC0, compute once offline)?
- Lookup table vs Maia-2 value head for resignation expected scores: which is better calibrated at 1800–2500 with low clocks? This needs an offline comparison on held-out Lichess games.
- Is the owner's morning effect a warm-up effect, a sleep effect, or a pre-work time constraint? The data cannot separate these. The next step is a self-report tag ("rushed / tired / fine") on a few sessions. That tag is a design idea, not researched.
- Does a rule shown by Kiebitz change behaviour, and does adherence improve results? This can only be measured after launch; it needs the adherence tracking described in the notes.
- Gaze, later: do the behavioural tilt markers (faster requeue, faster moves after a loss) also show up as shorter or narrower scanning in the gaze data?

## Sources

- [romanbreyten/chess-tilt: fixed-effects analysis of 11M Lichess games](https://github.com/romanbreyten/chess-tilt) (not peer reviewed)
- [Gee, Seese, Curley & Ward 2025, Investigating Experiential Effects in Online Chess, arXiv:2503.21713](https://arxiv.org/abs/2503.21713)
- [Adhikari, Anatolyev & Dagaev 2023, Do mistakes provoke new mistakes? IEEE Trans. Games](https://pages.nes.ru/sanatoly/Papers/TiltChess.htm)
- [Anderson & Green 2018, Personal bests as reference points, PNAS](https://pmc.ncbi.nlm.nih.gov/articles/PMC5828569)
- [Leone et al., Time to decide, Cognition](https://www.sciencedirect.com/science/article/abs/pii/S0010027716302414) and [BPS summary](https://www.bps.org.uk/research-digest/studying-fast-chess-see-how-decision-making-varies-through-day)
- [Purohit & Srivastava 2026, A Metacognitive Appraisal of Quitting in Chess, Cognitive Science](https://doi.org/10.1111/cogs.70193)
- [Stafford 2018, Female chess players outperform expectations when playing men, Psychological Science](https://eprints.whiterose.ac.uk/121102/)
- [Sonas, The Elo rating system: correcting the expectancy tables](https://en.chessbase.com/post/the-elo-rating-system-correcting-the-expectancy-tables)
- [Devine, Tilt and Hype in Online Chess (blog)](http://seandevine.org/blog/chessBlog.html)
- [chess.com Published Data API](https://www.chess.com/news/view/published-data-api), [chess.com Insights help](https://support.chess.com/en/articles/8708925-what-is-insights-on-chess-com), [chess.com ratings help](https://support.chess.com/en/articles/8566476-how-do-ratings-work-on-chess-com)
- [Lichess insight dimensions (source)](https://github.com/lichess-org/lila/blob/master/modules/insight/src/main/InsightDimension.scala), [Lichess database](https://database.lichess.org/), [Lichess accuracy / Win%](https://lichess.org/page/accuracy)
- [Aimchess](https://aimchess.com), [Audit Chess](https://www.auditchess.com/chess-performance-analyzer)
- Tilt extensions: [Tilt Breaker](https://addons.mozilla.org/firefox/addon/tilt-breaker/), [ChessEloShield](https://addons.mozilla.org/firefox/addon/chesseloshield/), [EloGuard](https://chromewebstore.google.com/detail/eloguard-chess-tilt-prote/jeephfmfnonhlgeodhpjagafacjaalph), [ChessBreak write-up](https://nitin.is-a.dev/blog/improving_my_rating), [zwischenzug](https://github.com/CodewithJha/zwischenzug)
- [Maia-2 paper](https://arxiv.org/abs/2409.20553), [Maia-2 repo](https://github.com/CSSLab/maia2), [Chess Engine Lab: evaluation, clock and score](https://chessenginelab.substack.com/p/evaluation-time-score)

**Pilot method:**
- Public chess.com archive of `chrisaxm`, fetched serially on 2026-11-12: 2,670 games, of which 2,290 are rated standard bullet, blitz or rapid with a known previous rating.
- Local time assumed to be Europe/Lisbon.
- Computed with the context engine above. The scripts were scratch work and are not committed; the definitions above are enough to reproduce them.
