# Gaze: threat check (attention to the opponent's side and king zones)

**Question:** Do you spend less of your thinking time looking at the opponent's side of the board before the moves where you miss their threats?

**What to measure:** Per think (from the opponent's move to your move), board oriented to you, using webcam gaze samples that passed quality checks:

- `opp_share` = dwell time on ranks 5 to 8 (the opponent's half) ÷ dwell time on the board.
- `own_king_share` and `opp_king_share` = dwell time in the 3x3-square zone around each king ÷ dwell time on the board (zones extended to 4x3 when the king is on the edge, so all zones have similar area).
- `threat_region_share` (variant) = dwell share in the quadrants that contain the opponent's pieces that attack your half (computed from the position, coarsened to quadrants).
- Each think is labelled from the game: **missed-threat mistake** (your move loses ≥ 10 win-probability points and the engine's refutation is a move by the opponent that already threatened before your move, i.e. the threat existed in the position you were thinking about), **other mistake**, or **good move**. The label comes from the mistake-type analysis (engine evals computed in the browser).
- The finding: the player's mean `opp_share` on missed-threat thinks minus the mean on good-move thinks of similar length and phase (matched by think-time bucket and game phase), with a bootstrap confidence interval. Also `opp_share` as a function of think time (do long thinks narrow onto one's own plans?).

Observed shares are biased towards the base rate by webcam error (my simulation: a true 30% zone share is observed as about 15%), so only within-player comparisons are valid.

**Data needed:** Gaze (WebEyeTrack in the browser), move times and moves from Lichess Board API games or Kiebitz "guess the move" sessions, engine evaluations for mistake labels. Board coordinates come from our own board component.

**Reliability:** Half-board assignment is 84 to 95% correct at 1.5° to 5° error on a desktop board, and 3x3 king zones about 56 to 75% at 3° to 4° (my simulation, see [gaze-tracking.md](gaze-tracking.md#2-what-the-accuracy-means-on-a-chessboard)). The limit is the number of missed-threat events: a 2300+ player makes perhaps one every few rapid games (estimate, to be measured from the owner's chess.com history). For a difference of half a standard deviation at 80% power, about 30 to 50 events against many good moves are needed (standard two-sample power arithmetic, my estimate). That is dozens of real rapid games, so the training-session version (positions from the player's own games where they missed a threat, mixed with control positions) is the realistic first setting. Noise sources: drift (corrected with move-click recalibration), lighting changes, peripheral vision (strong players can see a threat without looking at it ([de Winter et al. 2023](https://www.journalofexpertise.org/articles/volume6_issue1/JoE_6_1_deWinter_etal.pdf))), and board flipping errors.

**Effort:** M. UI: gaze capture, calibration, region assignment, per-move features (Web Worker). Insights service: `gaze_move_features` table, matching with mistake labels, bootstrap comparison. Depends on the mistake-type analysis.

**Prior work:** No product or open project links gaze to move quality ([prior-work-gap-map.md](prior-work-gap-map.md), G10). Lichess Insights, Aimchess and chess.com Insights use no gaze. Research links relevance to expertise at the region level: experts' first dwell favours the relevant half of the board, novices' does not ([Sheridan & Reingold 2014](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2014.00941/full)); experts put more fixations on pieces relevant to the best move within the first five fixations (Charness et al. 2001, described in the same paper). No study tests attention to the opponent's side as a predictor of missed threats. **This is a hypothesis.**

**Why it's not engine review:** Game Review can say that you missed a threat on move 23. It cannot say that you looked at the opponent's half for 12% of your think on the moves where you missed threats, against 25% on your other moves. That is a behavioural cause, measured across many games, and only gaze can provide it.

**Training link:** If confirmed: a "threat first" drill in Kiebitz training sessions. For each position, the player first marks the opponent's threats (or answers "what does the opponent want?") before choosing a move; Kiebitz uses positions where the player missed threats before. Improvement is measured as (a) `opp_share` on missed-threat-type positions rising towards the player's good-move level, and (b) the rate of missed-threat mistakes per 100 moves in real games falling, checked over the following months.

**Verdict:** Later (first gaze analysis to build after the course). The measurement is the most robust of all gaze metrics; the link to mistakes is unproven and must first be checked on the owner's data.
