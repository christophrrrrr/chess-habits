# Improvement tracker (did the weakness shrink?)

**Question:** Since you started working on a weakness Kiebitz found, has that weakness actually become less frequent in your new games, by more than chance, regression to the mean and general form would explain?

**What to measure:**

Every finding has one **target metric**: an exposure-normalised rate or mean over a defined set of moments, computed per time class.

1. **Exposure and events per game.** For game *i*: `E_i` = number of exposure moments (e.g. positions where the opponent had a real threat; rapid games that reached move 20; sessions with 2 losses in a row), `k_i` = number of failures among them (missed the threat; entered time trouble; kept playing). Rate `p = Σk_i / ΣE_i`. For continuous targets (e.g. Elo residual, seconds spent), use the mean per exposure.
2. **Windows.**
   - *Detection set:* the games the finding was detected on. To avoid regression to the mean, detection uses only **one half** of the history (games with an odd `game_id` hash).
   - *Baseline:* the **other half** of the pre-adoption history, most recent first, up to 500 exposures (minimum 100). It is never the window where the problem first looked bad.
   - *After:* games started after the plan was adopted (drills or a rule), all of them, no cherry-picked window. A 7-day burn-in is excluded (speculation: it gives the practice time to start).
3. **Change.** `Δ_target = p_after − p_base`.
4. **Control.** The same calculation for the player's **untrained** finding types of the same time class, pooled: `Δ_control`. Report the difference-in-differences `DiD = Δ_target − Δ_control`. This removes shifts that hit every type at once: form, opponent pool, a new engine depth, a new time control mix.
5. **Uncertainty.** 95% CI for `Δ_target` and `DiD` by **game-level cluster bootstrap** (resample whole games within each window independently, 2,000 resamples). Moments within one game are correlated; resampling moves would make CIs too narrow. Same convention as [clock-and-time.md](clock-and-time.md) and [psychology-and-context.md](psychology-and-context.md).
6. **Minimum detectable effect** for the current sample (80% power, α = 0.05): `MDE ≈ 2.8 · √(p(1−p) · (1/n_base + 1/n_after)) · √deff`, with `deff = 1 + (m − 1)·ICC`, `m` = mean exposures per game, ICC estimated from the baseline (default 0.1 until estimated).
7. **State** (updated only at checkpoints, every 50 new games in the time class, to limit false alarms from constant peeking):
   - *Too early:* `MDE > 0.3 · p_base` (cannot yet detect a 30% relative drop).
   - *Likely improved:* upper bound of the DiD CI < 0.
   - *Likely worse:* lower bound > 0.
   - *No clear change:* otherwise, shown with the MDE ("a change smaller than X pp would not be visible yet").
8. **Display.** A rolling line of the target metric over the last 150 exposures, with its bootstrap band, a flat baseline band, a marker at adoption, and the control types' rolling line in grey. Example text:
   > Missed opponent threats (rapid): 31% before (412 positions, 95% CI 27-36%), 24% since 3 Oct (160 positions, CI 18-31%). Untrained mistake types moved −1 pp. Net change −6 pp (CI −14 to +2). **No clear change yet.** Right now only a change of about 12 pp would be visible; after about 400 more threat positions, about 9 pp. This shows a change, not that the training caused it.

   (Numbers checked: Wilson CIs of 127/412 and 38/160; MDE `2.8·√(0.21·(1/412 + 1/n_after))`. Note that a 412-position baseline caps the MDE at ~6 pp however long the after-window gets, so the baseline should be as long as the history allows.)
9. **Shrinkage for the findings list.** Before a finding is created, its rate is shrunk toward the player's overall rate (beta-binomial, prior strength fitted across the player's types). This stops small categories from looking extreme, which is the main source of regression to the mean.

**Data needed:** Whatever the finding's own analysis uses (clock from `[%clk]`, session times from `UTCDate`/`UTCTime` and `end_time`, browser Stockfish evals for engine-based findings), plus the plan adoption date and, for engine-based targets, the engine version and depth stored with every evaluation. A baseline must be recomputed if the engine settings change, or both windows must use the same settings.

**Reliability:**

- Own calculation, two proportions, 80% power: at a 30% baseline, 100 exposures per window detect only an 18 pp change, 200 detect 13 pp, 400 detect 9 pp, 800 detect 6 pp. At a 20% baseline: 16 / 11 / 8 / 6 pp. Clustering adds about 10-40% (design effect 1.1-1.4 for 3-5 exposures per game and ICC 0.05-0.1; speculation until estimated).
- Rating is not usable as the target: per-game score SD ≈ 0.45 gives a 95% CI of about ±61 Elo after 100 games and ±43 after 200.
- **Regression to the mean is large.** Simulation (4,000 runs): 6 finding types with the same true rate (25%), 100 exposures each; select the worst and re-measure on new data. The selected type "improves" by 5.5 pp on average and by ≥ 5 pp in 52% of runs, with no training at all. Split-sample detection removes this bias; the control comparison removes shared drifts ([Barnett et al. 2005](https://doi.org/10.1093/ije/dyh299)).
- **Remaining noise sources:** the player gets stronger, meets stronger opponents and faces more or harder threats (exposure normalisation helps, difficulty does not fully cancel; the control types share this drift); change of time-control mix (always per time class); seasonal and life factors (the control handles shared ones); training *for* a type changes how often the player *reaches* it (e.g. fewer time-trouble games mean fewer time-trouble exposures; report both the rate and the exposure count).
- **Causality:** none. With one player and no randomisation the honest claim is "changed after you started", not "because of". A within-player randomised design is possible for drills (drill half of the positions of a type, hold out half as probes; see [training-own-position-drills.md](training-own-position-drills.md)), but that measures drill transfer, not in-game change.
- Several findings tracked at once inflate false "Likely improved" states; with more than three tracked, apply Benjamini-Hochberg at the checkpoint (same as the context analyses).

**Effort:** **M** overall, **S** for the engine-free version. Belongs to the insights service: a `measurement` table (window, value, n_exposures, n_games, CI, control_delta, MDE, state) recomputed when new games are imported; a bootstrap of a few thousand games in numpy takes well under a second, so it can run in the request without a background job (fits scale-to-zero and the no-queue rule). One chart and one status chip in the UI.

**Prior work:** No product re-measures a targeted weakness and reports a CI ([prior-work-gap-map.md](prior-work-gap-map.md), gap 5). chess.com Insights "Past Performance" compares general stats between periods; Aimchess scores six skill areas against peers but publishes no uncertainty ([aimchess.com](https://aimchess.com)). Aimchess's "31% faster" training claim cites a randomised experiment without a published paper (same page). Statistical building blocks are standard: [Wilson interval](https://en.wikipedia.org/wiki/Binomial_proportion_confidence_interval#Wilson_score_interval), cluster bootstrap, difference-in-differences, regression to the mean ([Barnett et al. 2005](https://doi.org/10.1093/ije/dyh299)).

**Why it's not engine review:** Game Review grades one game; Insights shows trends of generic metrics with no baseline design, no control and no uncertainty. The tracker answers a different question ("did *this* weakness shrink after I worked on it, beyond chance?") that requires cross-game exposure counting and a statistical design no existing tool shows.

**Training link:** This is the measurement half of every training link in the other notes. It also feeds back: if a finding stays at *No clear change* after enough data (MDE below the effect that would matter), Kiebitz suggests switching the plan (e.g. from drills to a rule, see the knowledge-vs-process split in [training-own-position-drills.md](training-own-position-drills.md)).

**Verdict:** **Build for MVP**, first on engine-free targets (time-trouble entry rate in rapid, post-loss residual). It is the clearest gap in the market, needs no engine, and is the part of vision principle 5 ("Kiebitz checks whether it improved") that no competitor does.
