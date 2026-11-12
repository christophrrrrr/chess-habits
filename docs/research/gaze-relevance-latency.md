# Gaze: how fast you find the region that matters (training sessions)

**Question:** In which kinds of positions does your gaze reach the important part of the board late, and does practice make it faster?

**What to measure:** Only in Kiebitz training sessions, where the important region is known before the player sees the position:

- For each position, the **relevant region** is the quadrant (or half, for wide ideas) containing the from- and to-squares of the solution's first two moves, or of the threat the player must answer. If those squares fall in two quadrants, both count.
- `rel_latency` = time from the position appearing to the first run of ≥ 300 ms of gaze inside the relevant region.
- `rel_early_share` = dwell share in the relevant region during the first 5 s. This mirrors the "first dwell" and "first five fixations" measures of [Sheridan & Reingold 2014](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2014.00941/full) and Charness et al. 2001 (described there).
- `irrel_share` = the same for a control region of the same size with no relevant content.
- Per player and per position type (puzzle theme from the Lichess puzzle tags, or Kiebitz's own mistake type, game phase, piece configuration): median `rel_latency`, mean (`rel_early_share` − `irrel_share`), and solve rate.
- Optional design: like Sheridan & Reingold, show two versions of a position that differ by one piece so that the relevant half flips. This rules out "the player always looks at the kingside first".

**Data needed:** Gaze and solution timing in training sessions. Positions from (a) the player's own games, at moments where they went wrong (from chess.com or Lichess imports; engine labels), and (b) the Lichess puzzle database, CC0, 6.19 million puzzles with ratings and themes ([database.lichess.org](https://database.lichess.org/)). Works for chess.com-only users and for any time control (set the timer per session: 5 s, 20 s, 60 s).

**Reliability:** The best of the gaze candidates. Halves and quadrants are classified correctly for 70 to 95% of samples (my simulation, [gaze-tracking.md](gaze-tracking.md#2-what-the-accuracy-means-on-a-chessboard)), the relevant region is known exactly, and a session yields 30 to 60 positions per half hour (my estimate). Per-theme comparisons need about 30 positions per theme. Calibration happens right before the session and sessions are short, which limits drift ([Lau & Kasneci 2026](https://arxiv.org/abs/2605.02898): shorter sessions give better data). Noise: puzzles signal "there is a tactic", which changes search; the player's habitual first-look direction (handled by the flipped-version design); centre-of-screen bias at position onset (use a fixation cross outside the board before each position).

**Effort:** M. UI: training session mode with gaze, position onset timing, region definitions. Insights service: store sessions and per-position features, aggregate by theme. Shares the gaze pipeline with the other gaze notes; needs no Lichess Board API.

**Prior work:** Lab studies show the effect between groups: only experts (CFC mean 2223) favoured the relevant half in their first dwell (2.19 vs 1.39 fixations), novices did not; experts found the best move in 93% of trials vs 52% ([Sheridan & Reingold 2014](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2014.00941/full)). Experts also reached a target region faster (407 vs 719 ms, [Sheridan & Reingold 2013](https://pmc.ncbi.nlm.nih.gov/articles/PMC3790829/)). Puzzle trainers (Lichess puzzles, chess.com Puzzles, Aimchess) measure solve rate and time, never where the player looked. No product measures this.

**Why it's not engine review:** It does not grade any move. It measures perception: "in back-rank and knight-fork positions, your eyes reach the key area 2.5 s later than in other themes, and your solve rate there is lower." Game Review and puzzle ratings cannot see this.

**Training link:** Short, timed perception drills in the slow themes (5 to 10 s per position, the player only has to click the key region or the key piece), repeated with spaced repetition. Improvement is measured directly by the same metric: `rel_latency` and solve rate per theme falling over weeks, and, as a transfer check, fewer real-game mistakes of the matching type.

**Verdict:** Later, but first in line among gaze features: it works for chess.com users, for every time control, does not depend on the Lichess Board API, and directly replicates the best-established chess eye-tracking result. Also the best setting to validate the gaze pipeline on the owner before trusting real-game gaze.
