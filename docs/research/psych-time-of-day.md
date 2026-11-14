# Time of day and day of week (rating-adjusted)

**Question:** Are there hours or weekdays when you play clearly below your own level, after accounting for opponent strength and chance?

**What to measure:**

1. **Performance residual per game**, as in [psych-tilt-and-stop-loss.md](psych-tilt-and-stop-loss.md): `r = S − E`, with `E` from the smoothed skill estimate `R_skill` and the opponent's rating, shown in Elo.
2. **Grouping.** Group by local start hour in buckets: 00–06, 06–12, 12–18, 18–22 and 22–24. Use 3–4 buckets when there are few games. Also group by weekday, and by weekday × part of day only when the player has more than 3,000 games.
   - Local time comes from the PGN `UTCDate` + `UTCTime`, converted with the user's IANA time zone *including DST*.
   - The chess.com public API has no time-zone field, so store the browser's `Intl.DateTimeFormat().resolvedOptions().timeZone` with the account.
   - Python on Windows needs the `tzdata` package for `zoneinfo`.
3. **Per bucket:** n, mean residual in Elo, and a 95% CI from a session-level cluster bootstrap.
4. **Significance for the whole dimension, not per bucket.** Use a permutation test: shuffle the bucket labels between *sessions* (2,000 times) and compare the observed largest |bucket residual| with the shuffled distribution. This gives one family-wise p-value for "time of day matters at all". Show bucket-level claims only if this test passes (p < 0.05 after Benjamini–Hochberg across all context dimensions shown).
5. **Confounder checks before claiming a time effect.** First, the share of games in the bucket that are the *first game of a session* (see [psych-session-warmup-fatigue.md](psych-session-warmup-fatigue.md)). Second, the time-class mix. Third, whether the effect has the same sign in the older and the newer half of the games.
6. **Secondary: move-time profile by hour.** Median seconds per move on moves 10–30 by hour bucket, since Leone et al. found faster but less accurate moves later in the day.

**Data needed:**
- Game start timestamps, ratings and results from the chess.com archives.
- The user's time zone (from the browser).
- `[%clk]` for the move-time profile.
- No engine.

**Reliability:**
- **Research:** a study of FICS 2–3 minute games (Leone et al., *Cognition*) found decisions became faster and less accurate through the day. However, rating changes showed **no** time-of-day effect overall, and chronotype did not change play quality ([BPS summary](https://www.bps.org.uk/research-digest/studying-fast-chess-see-how-decision-making-varies-through-day), [paper](https://www.sciencedirect.com/science/article/abs/pii/S0010027716302414)).
- **Expectation:** no population-wide "best hour". Any effect is personal (sleep, work, playing before work), which is exactly what a per-player analysis can find.
- **Sample size:** each bucket needs at least 80–100 games. Detecting a 100 Elo gap needs about 160 games per group, and a 50 Elo gap about 640 (residual SD ≈ 0.46).
- **Multiple comparisons:** 5 hour buckets × 7 weekdays × 3 time classes is over 100 comparisons, so at α = 0.05 about 5 false hits are expected by chance. Without the permutation and BH step this feature would mostly show noise.
- **Pilot on the product owner's data** (`chrisaxm`, rapid, 1,219 games, local time Europe/Lisbon *assumed*):
  - **06–12h: n = 82, −155 Elo vs own level [−212, −101].** All other hours: +1 Elo.
  - Family-wise permutation p = 0.003.
  - Same sign in both halves of the data: 2023–24 −111 Elo (n = 51), 2025–26 −219 Elo (n = 31).
  - 72% of these morning games are the first game of a session. Morning first games were −179 Elo, and later morning games −83 Elo (n = 23), so it is partly, but probably not only, a warm-up effect.
  - Weekday (rapid): Wednesday −65 Elo, permutation p = 0.021. This is weaker, and it should not survive BH correction once all splits are counted.
  - Bullet and blitz showed nothing that passed the tests.
  - This is the strongest individual finding in the pilot.

**Effort:** **S**. It uses the same residual engine as the tilt note, plus time-zone handling and the permutation test. Insights service.

**Prior work:**
- chess.com Insights has a **Calendar** section with games, accuracy and *results* by time of day and day of week, for Diamond members ([chess.com help](https://support.chess.com/en/articles/8708925-what-is-insights-on-chess-com)). These are raw results: no opponent-rating adjustment, no confidence interval, no multiple-comparison control.
- [Audit Chess](https://www.auditchess.com/chess-performance-analyzer) shows raw results by hour and day ("58% in the morning but 41% after 9pm").
- [Lichess Insights](https://github.com/lichess-org/lila/blob/master/modules/insight/src/main/InsightDimension.scala) has no time-of-day dimension.

**Why it's not engine review:**
- It uses no engine at all.
- The vision test is only **partly** passed: chess.com Insights already shows raw results by hour. Chess Habits adds three things. It compares results against expectation, which removes the effect of opponent strength and rating drift. It says whether the pattern is real, using a permutation test, a CI and an out-of-sample check. And it turns the result into a rule.
- With raw win rates, a player can easily see a "bad hour" that is pure noise. Build it only with these additions.

**Training link:**
- **Rule:** "Play rated <time class> only between X and Y. Use the bad window for puzzles, study or unrated games." For the pilot, that means no rated rapid before 12:00.
- **Measure:** after the rule is adopted, track rated games played inside the bad window (adherence) and the player's overall residual over the next 1–3 months.

**Verdict:** **Build for MVP**, as part of the context report. It costs little, it produced the owner's clearest finding, and the statistical honesty is the differentiator. Drop the weekday split from the MVP: it adds many comparisons for little value.

**Sources:**
- [Leone et al., "Time to decide: Diurnal variations on the speed and quality of human decisions", *Cognition*](https://www.sciencedirect.com/science/article/abs/pii/S0010027716302414)
- [BPS Research Digest summary](https://www.bps.org.uk/research-digest/studying-fast-chess-see-how-decision-making-varies-through-day)
- [chess.com Insights help](https://support.chess.com/en/articles/8708925-what-is-insights-on-chess-com)
- [Audit Chess](https://www.auditchess.com/chess-performance-analyzer)
- [Lichess insight dimensions (source code)](https://github.com/lichess-org/lila/blob/master/modules/insight/src/main/InsightDimension.scala)
