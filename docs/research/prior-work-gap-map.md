# Prior work and gap map

**Question:** What does every relevant chess-improvement product analyse about a player as of November 2026, and which analyses of *how* a strong (1800+) player plays does nobody offer, or offer only shallowly?

**Scope and method:** Product pages, help-centre articles, changelogs, source code (where open) and papers, checked 2026-11-12. Vendor claims are marked as claims. "Not found" means the official documentation does not mention it; it does not prove the feature is absent behind a login. Speculation is marked as such. This note deviates from the per-analysis template on purpose: it is the backbone for the shortlist, not a single analysis.

**Bottom line:**

1. Everyone grades **moves** (accuracy, classifications, explanations), and many now aggregate them across games: by phase, opening, tactic motif, conversion/defence, and against rating peers. None of that is a Chess Habits feature.
2. **Clock analysis is almost absent for chess.com players.** chess.com shows a per-game time chart only. Lichess Insights can cross move time and clock with accuracy, but only for Lichess games that were server-analysed one by one. Aimchess reports a "behind on the clock" percentage. **Nobody relates time spent to how critical the position was.**
3. **Human-relative difficulty exists only per position** (Maia platform "Blunder Meter"). Nobody aggregates it over a player's own games to separate "mistakes everyone at your level makes" from real blind spots.
4. **Tilt and session effects are not measured by any product.** There are only stop-loss browser extensions (lock the Play button after N losses) and population-level studies.
5. **No product shows sample size or confidence** for its findings, and **none checks whether a specific weakness shrank** after training.
6. **No product combines gaze with game analysis.**

---

## Products

### chess.com Game Review (single game)

- Documented components (help centre, updated 2026-09-25): Game Graph, Accuracy (0-100), move classifications (Brilliant, Great, Best, Excellent, Good, Book, Inaccuracy, Mistake, Miss, Blunder), Key moves, Coach explanations (text and audio), Retry of key positions, "Show Fork / Lost Piece / Checkmate / Idea / Best" buttons, Game Rating (performance estimate for one game), a "Show Time Spent On Move" setting, and a "Skills" toggle [1].
- Game Review v2 (2023) added phase grades (opening / middlegame / endgame accuracy), the "Miss" class, and Coach threat explanations [2].
- 2026 additions: "course check", which flags when you leave the lines of a chess.com opening course you own (2026-09-08) [3]. "Skills" appeared for a subset of members in July 2026 with no official documentation [4]. Celebrity coach voices exist [5].
- Free tier: limited daily reviews; unlimited with Premium; Diamond adds deeper engines [1].
- **Time:** per-move time display inside one game only. No cross-game clock analysis is documented.

### chess.com Insights and Advanced Stats (across games, Diamond only)

- Insights sections [6]: **Games** (games and accuracy over time, accuracy by move number, results by opponent rating, "Similar Players" comparison, "Past Performance", game-ending types, "Game Shapes", **Game Phases**: accuracy and results per phase); **Openings** (top-10 openings, "Mastery" = book moves before leaving theory); **Tactics** (forks, pins, mates found vs missed; pieces left hanging); **Moves** (move-quality shares, accuracy per piece, castling timing); **Calendar** (results and accuracy by **time of day and day of week**); **Geography**.
- Advanced Stats [7]: ratings per time control for Openings, Tactics, Strategy (attacking/defending, activity, pawn structure, space) and Endgames (converting or holding).
- **No time-management metric is documented** in either [6][7].

### chess.com data available to Chess Habits (verified)

- The public API returns monthly archives with full PGN including `[%clk h:mm:ss.s]` after every move (0.1 s resolution) and **no `[%eval]` tags** [8]. Verified on the owner's account (chrisaxm): 2,670 games since 2023-07 (rapid 1,310, bullet 846, blitz 461, daily 53); 2,662 have clock comments.
- The game JSON also has an `accuracies` object (white/black game accuracy) for games that someone has reviewed: 1,446 of the owner's 2,670 games (rapid 1,172, blitz 232, bullet 30, daily 12). This is a per-game number only, not per move. (Field observed in the API response; not described in the API documentation [8].)
- Consequence: every per-move engine analysis needs our own Stockfish run (browser WASM). Clock-only and result-only analyses can run immediately.

### Lichess analysis and Lichess Insights (free, Lichess games only)

- Analysis board: Stockfish evaluation graph, accuracy (Win% and Accuracy% formulas published [9]), ACPL, a move-times chart, "Learn from your mistakes" (retry your own mistakes from one game) [10].
- Puzzle Dashboard ranks puzzle themes where you score worst ("Improvement areas") [11]. That is based on puzzles, not on your games.
- **Insights** is a free query builder (metric x dimension). From the source code [12]:
  - Metrics: Average centipawn loss, Centipawn loss bucket, Accuracy, Move time, Game result, Game termination, Performance, Rating gain, Opponent rating, Moves per game, Piece moved, **Tactical awareness** ("how often you take advantage of your opponent mistakes"), **Luck** ("how often your opponent fails to punish your mistakes"), Material imbalance, **Time pressure** (clock % left), Blurs, **Time variance**.
  - Dimensions: Date, Variant, Game phase, Result, Termination, Color, Opening family/variation, Opponent strength, Piece moved, **Move time**, Castling sides, Queen trade, Material imbalance, Move blur, **Time variance** ("Very consistent < 0.25 ... Very variable > 0.75"), CPL range, **Evaluation**, Accuracy, **Winning chances**, **Time pressure** ("100% = full clock, 0% = flagging"), Game source.
  - Peer comparison: "peers" are players in a narrow band around your rating [13].
  - Accuracy/CPL/awareness metrics need games with server analysis ("requiresAnalysis") [12].
- So for Lichess games you can already ask "accuracy by move time" or "ACPL by time pressure". You cannot ask about **criticality** (how many moves hold), and you cannot ask about chess.com games.

### Aimchess

- Six scored categories: Tactics, Endgame, Advantage capitalization, Resourcefulness, Time management, Opening performance, compared against peers/opponents [14][15].
- Lessons: Advantage Capitalization Trainer, Opening Improver, Blunder Preventer, Retry Mistakes, Defender, **Time Trainer**, Intuition Trainer, and more. Also a weekly personalised study plan [14].
- Free: one 40-game report per month. Premium $7.99/month: unlimited reports, up to 1,000 games [14].
- The "time management" number shown to users is "behind on the clock X% of moves" (user reports [16][17]). **No published formula** for any category.

### Maia Chess platform (maiachess.com, University of Toronto CSSLab)

- Models: Maia-1 (2020, GPL-3.0), Maia-2 (2024, MIT), **Maia-3** (2026, Chessformer transformer, **AGPL-3.0**, 57.1% move-matching vs 52.0% for Maia-2, covers **Lichess blitz 600-2600**) [18][19][20].
- Platform v1 (2025-07-10) [21]: "Moves by Rating" graph, **"Blunder Meter"**, "Move Map", opening drills against Maia, puzzles, "Bot-or-Not" Turing test, Hand and Brain. Maia-3 now powers the platform [18].
- Blunder Meter = sum of Maia's move probabilities over moves in three buckets by win-rate loss: good (< 5 %), ok (5-10 %), blunder (> 10 %) (thresholds in `src/constants/analysis.ts`) [22]. It runs in the browser with `onnxruntime-web` and `@lichess-org/stockfish-web` [22].
- **Per position only.** No profile across a user's own game history. Personalised per-player models exist in research (Maia-Individual, KDD 2022; Maia4All, TMLR 2026, about 20 games) but are not released as a product [23][24].

### ChessBase 26 / Fritz 20 (desktop)

- **Style Report** (since CB18, Nov 2024): Tenacity, Aggressiveness, Risk, Endgame, calibrated to modern GMs; "a more natural curve only emerges after more than 200 games" [25][26].
- **Error Report**: where a player tends to err, compared to an average GM, with "Blunder Elo" [27].
- CB26 (Nov 2025): new Opening Report, Monte-Carlo analysis, "AI Consult" [28]. Fritz 20 imitates a player's style using the style analysis [26].
- **Let's Check**: a shared cloud database of engine evaluations. Position knowledge, not player analysis [29].
- No clock analysis is documented.

### DecodeChess

- Explains one position at a time in five tabs: Threats, Good Moves, Plans, Functionality, Concepts [30]. No cross-game or clock analysis is documented.

### Chessable

- Course learning with MoveTrainer spaced repetition [31]. Nothing analyses your own games. The only link to your games is chess.com's "course check" in Game Review, which excludes Chessable-only purchases [3].

### Chess Tempo

- Tactics trainer with ratings and per-theme statistics; Stockfish game analysis; premium users get tactics problems extracted from their own rated games [32][33]. No clock or behaviour analysis is documented.

### Chessbook

- Repertoire builder with spaced repetition and coverage per opening. It connects to chess.com/Lichess and flags moves in your recent games that leave your repertoire [34][35]. A reviewer noted it does not count how often the same deviation happens [35].

### Noctie

- Human-like training bot, colour-graded feedback on every move, a rating test, puzzles from your games. €14/month [36].

### Chessigma

- Free browser Stockfish game review with accuracy and classifications [37].
- "Supercoach" (paid, €6.92-12/month): a "Chess DNA report" from up to 1,000 chess.com games and "250+ metrics", split into **blunders, tactics, the clock, converting winning positions and openings**; a daily plan; "Blunder Shield" drills; an LLM coach called "Froggy" [38][39]. **No metric definitions are published**, so its clock analysis cannot be assessed.

### ChessMonitor

- Profiles and opening statistics for chess.com/Lichess players, an explorer with Stockfish evaluations (June 2025), and a paid "Studio" workspace [40][41]. No clock or behaviour analysis is documented.

### Dr. Wolf (chess.com)

- Beginner coaching app: step-by-step explanations during play, four coach personalities, three free coached games [42]. Not aimed at 1800+.

### LLM / AI coaches (2026 wave)

- **Chessiro**: Stockfish-grounded LLM explanations; "mistake patterns tracked across games" turned into spaced-repetition puzzles; aimed at 0-1800 [43].
- **Chessalyz**: a Socratic coach that asks you questions about a game; flashcards; stats page; **time-management analysis announced as upcoming** (spring 2026) [44].
- **Improve my Chess**: recurring mistakes, "Ask My Games" questions over your history, opponent scouting; aimed at 400-999 [45].
- **Sensei Chess, ChessLogix**: weakness detection and study plans; vendor claims only [46].
- **chess.com Coach**, **Chessigma Froggy**: see above.
- Common pattern: an LLM narrates engine output for single games and clusters blunders by motif. None publishes clock, criticality, tilt or uncertainty metrics.

### Clock-focused tools

- **Chessboard Magic** (free, solo developer): "Time Usage Analysis" shows move-by-move time use and claims to show "hesitating at critical moments". No published method [47].
- **Tilt blockers**: EloGuard (Chrome, stop-loss after N losses in a row), Tilt Breaker (Chrome/Firefox, chess.com and Lichess), a chess.com "Tilt Preventer" userscript [48]. These are **rules**, not measurements.

### Open source (GitHub, checked 2026-11-12)

- Personal weakness finders: `AnishChinnam/chess-weakness-finder` (browser Stockfish; top-3 recurring weaknesses; **mistakes in time trouble per phase**), `yiheinchai/gambit` (weakness clustering, ONNX concept probes, LLM explanations), `ChessVi` (opening leaks), `bdrapeau-poly-crypto/chess-coach` (Leitner drills from your blunders), `MrLokans/chess-blunder-trainer`, `NotJoeMartinez/chess-insights` (chess.com export and charts) [49].
- Population studies: `Antiochian/chess-blunders` (68M Lichess games; blunder rate rises as the clock runs down, with a bump at the low-time alarm) [50]; `romanbreyten/chess-tilt` (11M Lichess games, player fixed effects: about **-7 Elo after a loss vs after a win**, growing to -24 after 5+ losses, **gone after a 30-minute break**) [51]; `alex-tereshkovv/chess-time-pressure-analysis`.
- Gaze: `ryan1woodard/ChessEyeTrackerProjectCapstone` (heatmap only, no move analysis), `vacocella/chess-eyetracking` (play with your eyes), `arlegotin/chess-gaze` (gaze from stream video) [49]. No project links gaze to move quality.
- Caution: several "chess blunder" repos updated on 2026-11-11 with SEO-style names (`stockfish-blunder-lab`, `chess-blunder-autopsy`) look like spam or malware lures. Do not run them.

### Research that defines the frontier

- Anderson, Kleinberg, Mullainathan (KDD 2016): position **difficulty** predicts errors better than skill or time [52].
- Maia papers: human move prediction by rating, per-player models, about 20 games needed with Maia4All [18][23][24].
- ChessMimic (arXiv, June 2026): per-rating transformers predicting moves, **think time** (Pearson r = 0.41; ALLIE reaches r = 0.70) and outcomes for Lichess blitz [53]. This is a possible "expected think time" baseline.
- Sunde et al. (PNAS 2026): in elite play, faster decisions go with better quality after controlling for complexity [54].
- Adhikari, Anatolyev, Dagaev (IEEE ToG 2023): mistakes provoke further mistakes (tilt) in top players' games [55].
- Leela WDL "sharpness" (Chess Engine Lab): a criticality proxy with known node-count sensitivity [56].

---

## Feature matrix

Legend: **Y** = documented feature. **P** = partial or shallow (see note). **C** = vendor claim with no published method. **–** = not found in documentation.

Columns: CC-GR = chess.com Game Review; CC-Ins = chess.com Insights + Advanced Stats; Li-An = Lichess analysis; Li-Ins = Lichess Insights; Aim = Aimchess; Maia = maiachess.com; CB = ChessBase 26/Fritz 20; Dec = DecodeChess; CT = Chess Tempo; Cbk = Chessbook; Cbl = Chessable; Noc = Noctie; Sig = Chessigma (+Supercoach); CMon = ChessMonitor; AI = LLM coaches (Chessiro, Chessalyz, Improve my Chess, Dr. Wolf); OSS = Chessboard Magic, tilt blockers, GitHub projects.

| Analysis type | CC-GR | CC-Ins | Li-An | Li-Ins | Aim | Maia | CB | Dec | CT | Cbk | Cbl | Noc | Sig | CMon | AI | OSS |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Single-game engine grading (accuracy, move classes) | Y | – | Y | – | Y | Y | Y | P | Y | – | – | P | Y | P | Y | Y |
| Natural-language move explanations | Y | – | – | – | – | – | P | Y | – | – | – | – | Y | – | Y | P |
| Key moments / retry a position | Y | – | Y | – | Y | – | – | – | – | – | – | – | – | – | Y | – |
| Per-game time-per-move chart | P | – | Y | – | – | – | P | – | – | – | – | – | – | – | – | Y |
| Accuracy by game phase, across games | – | Y | – | Y | P | – | P | – | – | – | – | – | C | – | P | P |
| Opening performance / repertoire deviations | P | Y | – | Y | Y | P | Y | – | – | Y | – | P | C | Y | P | Y |
| Tactic motifs found vs missed, across games | – | Y | – | P | Y | – | – | – | P | – | – | – | C | – | P | P |
| Converting wins / defending worse positions | – | P | – | P | Y | – | P | – | – | – | – | – | C | – | – | – |
| Comparison with rating peers | – | Y | – | Y | Y | P | P | – | – | – | – | – | – | – | – | – |
| Results by time of day / weekday | – | Y | – | – | – | – | – | – | – | – | – | – | – | – | – | – |
| Style profile (aggression, risk...) | – | – | – | – | – | – | Y | – | – | – | – | – | C | – | – | P |
| Clock usage across games (time pressure share, behind on clock) | – | – | – | Y | P | – | – | – | – | – | – | – | C | – | – | P |
| Accuracy vs remaining clock (cost of time trouble) | – | – | – | Y | C | – | – | – | – | – | – | – | C | – | – | P |
| Accuracy vs own move time (rushing / overthinking) | – | – | – | Y | – | – | – | – | – | – | – | – | – | – | – | – |
| **Time spent vs position criticality** | – | – | – | P | – | – | – | – | – | – | – | – | – | – | – | C |
| Human difficulty of a position (by rating) | – | – | – | – | – | Y | – | – | – | – | – | – | – | – | – | – |
| **Own errors vs what peers would do, aggregated over own games** | – | – | – | – | – | – | – | – | – | – | – | – | – | – | – | – |
| **Reaction to the opponent's surprising move** | – | – | – | – | – | – | – | – | – | – | – | – | – | – | – | – |
| **Measured tilt (performance after a loss)** | – | – | – | – | – | – | – | – | – | – | – | – | – | – | – | P |
| **Session fatigue (game number in session)** | – | – | – | – | – | – | – | – | – | – | – | – | – | – | – | – |
| Drills from own mistakes | P | – | P | – | Y | – | – | – | Y | P | – | Y | Y | – | Y | Y |
| **Closed loop: did this weakness shrink? (with CI)** | – | P | – | – | P | – | – | – | – | – | – | – | – | – | – | – |
| **Sample size / confidence shown per finding** | – | – | – | P | – | – | P | – | – | – | – | – | – | – | – | – |
| **Gaze / attention linked to moves** | – | – | – | – | – | – | – | – | – | – | – | – | – | – | – | P |
| **Time-control-specific analyses** | – | P | – | P | – | P | – | – | – | – | – | – | – | – | – | – |

Notes on P and C cells:
- CC-GR time chart: "Show Time Spent On Move" setting, single game [1]. CC-GR openings: book moves and course check [3]. CC-GR drills: Retry key moves of that game.
- CC-Ins conversion: Advanced Stats Endgames "converting or holding" rating, no breakdown [7]. CC-Ins closed loop: "Past Performance" compares periods, not specific weaknesses [6]. CC-Ins and Li-Ins time controls: filters only, not different analyses per time control.
- Li-Ins criticality: you can cross Move time with Evaluation or Winning chances, but evaluation is not criticality (a +5 position can be trivial or need one only move) [12]. Li-Ins tactic and conversion: "Tactical awareness" and "Luck" metrics; "Winning chances" dimension. Li-Ins sample size: shows game counts, no intervals.
- Aim: "behind on the clock %" shown, but formula not published [16]. Aim closed loop: progress dashboards, but nothing checks one weakness against a baseline [45].
- Maia peers and time control: per-position rating comparison only; Maia-2 conditions on rating, not on time control [19].
- CB phases and peers: Error Report vs average GM, Blunder Elo [27]. CB sample size: Style Report warns about fewer than 200 games [26].
- Sig "C": listed in the Chess DNA areas with no definitions [38].
- OSS criticality: Chessboard Magic claim, no method [47]. OSS tilt: stop-loss rules [48] and population studies [51], never a personal estimate. OSS gaze: heatmap only [49].

---

## Gaps

Ordered by how strongly they pass the vision test *and* how much they matter to a 1800+ player. Every gap names a concrete metric. Formulas are proposals for the follow-up notes; they are not validated yet.

### G1. Time spent vs criticality (nobody)

- **Gap:** No tool asks whether you spend your clock where it matters. Lichess Insights crosses time with evaluation, which is not the same thing. Chessboard Magic claims it with no method.
- **Metric proposal:** for each move, criticality `K = 1 - (number of legal moves with win-% loss < 5) / (number of legal moves)`, or the Maia "blunder mass" at the player's rating: `B = sum of P_maia(move | rating)` over moves losing > 10 % win probability. Time share `τ = t_move / (clock_before / est_moves_left)`. Report per player and time control: Spearman ρ(τ, K); **under-think rate** = share of positions with K in the top quartile played with τ < 0.5 *and* an error; **over-think rate** = share of moves with τ > 2 where K is in the bottom quartile.
- **Needs:** per-move Stockfish MultiPV (browser WASM) plus `[%clk]`; Maia for the rating-aware version.
- **Why strong players:** at 2300+, few points are lost to simple tactics; many are lost to clock misallocation (research shows difficulty, not time, drives errors [52]).

### G2. Peer-relative error profile across your own games (nobody)

- **Gap:** Maia shows human difficulty per position [21]. chess.com and Lichess compare aggregate accuracy with peers [6][13]. Nobody combines them over a player's history.
- **Metric proposal:** for each of your moves, the expected error `E = B(position, your rating)` from Maia, and the actual error `A ∈ {0,1}` (win-% loss > 10). **Blind-spot index** per bucket (phase, piece type, motif, material balance) = `(ΣA - ΣE) / sqrt(ΣE(1-E))` (a z-score). Positive = you err more than your peers would in exactly these positions; negative = a relative strength.
- **Caveat:** Maia-3 tops out at 2600 *Lichess* blitz [18]. The owner is ~2380 chess.com; the Lichess equivalent may be near that ceiling (speculation, needs a rating-mapping check). Maia-3 is AGPL-3.0, Maia-2 is MIT [20].

### G3. Measured tilt and session effects, per player (nobody)

- **Gap:** Products either ignore tilt or block play after N losses [48]. chess.com Insights has time of day but not "game N of the session" [6].
- **Metric proposal (no engine needed):** residual `r = score - 1/(1+10^((R_opp - R_me)/400))`; sessions split at gaps of 30 minutes or more [51]; tilt effect = `mean(r | previous game in session lost) - mean(r | previous won)`, per time control, with a bootstrap CI; session curve = mean r by game index in session.
- **Reliability (exploratory, owner's data, 2026-11-12):** bullet -58 ± 50 Elo-equivalent (n = 311 after losses / 328 after wins), blitz +82 ± 79 (104/115), rapid +66 ± 51 (265/289). Caveat: chess.com's per-game `rating` field is probably the post-game rating, which biases the residual, so these numbers are not a result. The point is that **95 % intervals are ±50-80 Elo even with hundreds of pairs**, while the population effect is about 7 Elo [51]. Personal tilt findings must show their interval and stay silent when it crosses zero.
- With engine evals later: replace `r` with move accuracy or blunder rate, which is far less noisy than results.

### G4. Clock analysis for chess.com players (shallow elsewhere)

- **Gap:** Lichess Insights already has time pressure and move-time cuts, but only for analysed Lichess games [12]. Aimchess has one undocumented percentage [16]. chess.com has nothing across games [6][7].
- **Clock-only metrics (MVP-able now):** per time control, the time-use curve (median % of base time used by move 10/20/30/40); the move where your clock first drops below 10 % of base (time-trouble entry); flag-loss rate; **clock deficit vs opponent** at moves 20/30/40; increment usage (share of moves under the increment); the result residual `r` (G3) split by "entered time trouble first" vs "opponent did". All are computed from `[%clk]` only.
- **Engine-enabled metrics (later):** blunder rate by clock band versus your own baseline (the Lichess Insights "Time pressure" cut, for chess.com games); **points thrown away on the clock** = games where your win probability was ≥ 80 % and the result was a loss or draw, split by remaining clock.
- Vision test: passes for chess.com users only because no chess.com tool does it. It is the **foundation** for G1, not the headline.

### G5. Reaction to surprise (nobody)

- **Metric proposal:** surprise of the opponent's move `S = -log P_maia(opp_move | opp rating)`. Compare your error rate and think time on the next move for high S (top decile) vs low S. "Your mistakes cluster after unexpected moves" is exactly the vision's cause-not-symptom example.
- Reliability: the high-S decile gives roughly 3-5 events per game (speculation), so a few hundred games are needed.

### G6. Rushing vs overthinking relative to your own baseline (shallow: Lichess only)

- **Metric proposal:** blunder rate as a function of `t_move / median t_move` (your median for that time control and phase), and the "long think then quick blunder" pattern (error on the move right after a think longer than 3x your median).
- Lichess Insights offers Move time x Accuracy for Lichess [12], so this is new only for chess.com and in its personal-baseline normalisation.

### G7. Closed loop with evidence (shallow everywhere)

- Aimchess, Chessigma and the LLM coaches create study plans and drills [14][38][43], but none re-measures the targeted metric and reports "your under-think rate fell from X to Y (CI ...)". chess.com "Past Performance" compares periods of general stats only [6].
- **Metric proposal:** for each finding, a pre-registered metric and window (for example the next 200 rapid games), with a two-sample test against the baseline window.

### G8. Uncertainty shown per finding (nobody)

- Only ChessBase warns about small samples in documentation [26]. No product shows counts plus intervals next to a finding. This is a cross-cutting differentiator (design principle 4), not an analysis.

### G9. Time-control-specific analyses (nobody)

- Existing tools filter by time control but run the same analyses. Chess Habits can choose by format (speculation about weights): bullet → clock deficit, increment usage, flag rate, speed-vs-blunder curve; blitz → time-trouble entry and points thrown away; rapid/classical → G1 criticality and G5 surprise; daily → long-horizon (e.g. move-time in days is meaningless, so use results and conversion only).

### G10. Gaze linked to moves (nobody)

- Confirmed: no product or open project links gaze to move quality [49]. Research only until after the course (separate research note).

### Not gaps (fail the vision test, use only as inputs)

- Accuracy, move classes, explanations, key moments, retries (chess.com, Lichess, Chessigma, LLM coaches).
- Accuracy by phase, openings, tactic motifs, conversion/defence, peer comparison, time of day (chess.com Insights, Lichess Insights, Aimchess).
- Style profiles (ChessBase Style Report, Chessiverse "Chess DNA" with 8 markers [57], Chessigma DNA).
- Drills from your own blunders (Aimchess, Chess Tempo, Noctie, Chessigma, Chessiro, many OSS).
- Opening repertoire deviations (Chessbook, chess.com course check, ChessMonitor).

---

## Sources

1. chess.com Help, "Game Review" (updated 2026-09-25): https://support.chess.com/en/articles/8584089
2. chess.com News, "Game Review Now With New Features" (2023-03-17): https://www.chess.com/news/view/chesscom-launches-game-review-v2
3. chess.com News, "Game Review Now Shows Your Course Deviations" (2026-09-08): https://www.chess.com/news/view/announcing-game-review-course-check
4. chess.com Forum, "Is this a new feature?" (Skills, July 2026): https://www.chess.com/forum/view/game-analysis/is-this-a-new-feature
5. chess.com News, "Choose your coach": https://www.chess.com/news/view/choose-your-coach-on-chesscom
6. chess.com Help, "What is Insights?": https://support.chess.com/en/articles/8708925-what-is-insights
7. chess.com Help, "How do I use Advanced Stats?": https://support.chess.com/en/articles/15451190-how-do-i-use-advanced-stats
8. chess.com Published-Data API: https://www.chess.com/news/view/published-data-api (PGN contents verified against `https://api.chess.com/pub/player/chrisaxm/games/2026/10` on 2026-11-12)
9. Lichess, "Accuracy": https://lichess.org/page/accuracy
10. Lichess blog, "Learn from your mistakes": https://lichess.org/@/lichess/blog/learn-from-your-mistakes/WFvLpiQA
11. Lichess blog, "Some Puzzling Analysis": https://lichess.org/blog/YAMFfhUAAGjN49-C/some-puzzling-analysis
12. lila source, Insights metrics and dimensions: https://github.com/lichess-org/lila/blob/master/modules/insight/src/main/InsightMetric.scala and https://github.com/lichess-org/lila/blob/master/modules/insight/src/main/InsightDimension.scala
13. lila source, peer rating range: https://github.com/lichess-org/lila/blob/master/modules/insight/src/main/PeersRatingRange.scala
14. Aimchess home page and pricing: https://aimchess.com
15. Aimchess user report (six categories vs opponents): https://lichess.org/@/DeepLies/blog/chess-analytics-revealed-how-i-discovered-my-hidden-strengths-and-weaknesses/VqqHKbRC
16. User report of Aimchess "behind on the clock" figure: https://chess.com/forum/view/general/overcoming-time-blindness-in-chess-adhd-autism-monotropism-data-included
17. User report (Aimchess clock %): https://www.chess.com/blog/Jessicamel/beyond-blitz-how-fast-chess-games-impact-performance-in-slow-games
18. Anderson, "Introducing Maia-3: free and open source" (Lichess blog, 2026): https://lichess.org/@/ashtonanderson/blog/introducing-maia-3-free-and-open-source/vCPPRtX3
19. Maia-2 paper (NeurIPS 2024): https://arxiv.org/abs/2409.20553
20. Licences: https://github.com/CSSLab/maia3 (AGPL-3.0), https://github.com/CSSLab/maia2 (MIT), https://github.com/CSSLab/maia-chess (GPL-3.0); Chessformer paper https://arxiv.org/abs/2605.19091
21. Maia platform v1 post (2025-07-10): https://www.maiachess.com/blog/platform-v1 (source: https://github.com/CSSLab/maia-platform-frontend/blob/main/src/lib/blog/posts/platform-v1.md)
22. Maia platform source: https://github.com/CSSLab/maia-platform-frontend (`src/constants/analysis.ts`, `src/hooks/useAnalysisController/utils.ts`, `package.json`)
23. McIlroy-Young et al., "Learning Models of Individual Behavior in Chess" (KDD 2022): https://arxiv.org/abs/2008.10086 ; https://github.com/CSSLab/maia-individual
24. Tang et al., "Learning to Imitate with Less" (Maia4All, TMLR 2026): https://arxiv.org/abs/2507.21488
25. ChessBase, "Style report in ChessBase 18" (2024-11-22): https://en.chessbase.com/post/style-report-in-chessbase-18
26. ChessBase, "Player types in chess: what the ChessBase style report reveals": https://en.chessbase.com/newsroom/post/player-types-in-chess-what-the-chessbase-style-report-reveals?page=0 ; Fritz 20 Handbook: https://books.chessbase.com/perma/c/682ef9abc9750c38fdcf0e63
27. ChessBase, "ChessBase'26: A Player's Guide (3)" (2026-01-30): https://en.chessbase.com/post/128719
28. ChessBase, "ChessBase 26: expand your chess horizon": https://en.chessbase.com/post/chessbase-26-expand-your-chess-horizon ; review: https://en.chessbase.com/post/review-chessbase-26-the-beginning-of-a-new-era
29. ChessBase, "How does the Engine Cloud work?": https://en.chessbase.com/post/tutorial-how-does-the-engine-cloud-work
30. DecodeChess: https://decodechess.com
31. Chessable: https://www.chessable.com
32. Chess Tempo app listing: https://apps.apple.com/app/id1441878094
33. Chess Tempo user guide, statistics: https://fr.chesstempo.com/user-guide/en/userStatisticsSummary.html
34. Chessbook: https://chessbook.com ; App Store: https://apps.apple.com/us/app/chessbook/id6466343415
35. Lichess review of Chessbook: https://en.lichess.org/ublog/B3xp08nE/redirect
36. Noctie: https://noctie.ai
37. Chessigma: https://chessigma.com
38. Chessigma Supercoach: https://chessigma.com/supercoach
39. Chessigma blog, "The AI chess coach": https://www.chessigma.com/blog/the-ai-chess-coach
40. ChessMonitor: https://www.chessmonitor.com
41. ChessMonitor, engine explorer (June 2025): https://www.chessmonitor.com/blog/2025-june-update-explorer-engine-integration
42. Dr. Wolf App Store listing: https://apps.apple.com/app/id1353041020 ; https://chess.com/news/view/dr-wolf-joins-chess-com
43. Chessiro AI coach: https://chessiro.com/ai-chess-coach ; https://chessiro.com/llms.txt
44. Chessalyz spring 2026 update: https://www.chess.com/blog/MattyDPerrine/you-asked-we-built-whats-new-in-chessalyz-spring-2026-updates
45. Improve my Chess, "Best AI Chess Coaches in 2026" (vendor-written, 2026-04-29): https://www.improvemychess.co/learn/best-ai-chess-coaches-2026
46. Sensei Chess: https://senseichess.com/ ; ChessLogix: https://chesslogix.com/
47. Chessboard Magic release notes: https://lichess.org/@/HollowLeaf/blog/chessboard-magic-12-halloween-release/6hqTx1WP ; https://lichess.org/@/HollowLeaf/blog/chessboard-magic-15-release/uzZIeKaP
48. EloGuard: https://chromewebstore.google.com/detail/eloguard-chess-tilt-prote/jeephfmfnonhlgeodhpjagafacjaalph ; Tilt Breaker: https://chromewebstore.google.com/detail/ppajmbmnfchaekapehmjmlbkdkjibimn ; Tilt Preventer: https://greasyfork.org/scripts/475390-chess-com-tilt-preventer/code
49. GitHub: https://github.com/AnishChinnam/chess-weakness-finder , https://github.com/yiheinchai/gambit , https://github.com/ChessVi/ChessVi.github.io , https://github.com/bdrapeau-poly-crypto/chess-coach , https://github.com/MrLokans/chess-blunder-trainer , https://github.com/NotJoeMartinez/chess-insights , https://github.com/ryan1woodard/ChessEyeTrackerProjectCapstone , https://github.com/vacocella/chess-eyetracking , https://github.com/arlegotin/chess-gaze , https://github.com/alex-tereshkovv/chess-time-pressure-analysis
50. Antiochian, chess-blunders: https://github.com/Antiochian/chess-blunders
51. romanbreyten, chess-tilt: https://github.com/romanbreyten/chess-tilt
52. Anderson, Kleinberg, Mullainathan, "Assessing Human Error Against a Benchmark of Perfection" (KDD 2016 / TKDD 2017): https://arxiv.org/abs/1606.04956
53. Johnson, "ChessMimic" (arXiv, 2026-06-03): https://arxiv.org/abs/2606.04473
54. Sunde et al., "Speed, Quality, and the Optimal Timing of Complex Decisions" (preprint; PNAS 2026): https://arxiv.org/abs/2201.10808
55. Adhikari, Anatolyev, Dagaev, "Do mistakes provoke new mistakes?" (IEEE Transactions on Games 2023): https://www.nes.ru/files/faculty/Do-mistakes-provoke-new-mistakes-Evidence.pdf
56. Chess Engine Lab, "Evaluating sharpness using LC0's WDL": https://chessenginelab.substack.com/p/evaluating-sharpness-using-lc0s-wdl
57. Chessiverse, "Chess DNA": https://chessiverse.com/chess-dna
