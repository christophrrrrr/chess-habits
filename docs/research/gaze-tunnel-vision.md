# Gaze: tunnel vision (staying stuck in one region)

**Question:** When you go wrong, is it because your attention stayed locked on the first area you looked at, while the better move was somewhere else on the board?

**What to measure:** Per think of at least 8 s (shorter thinks have too few samples), with the board split into quadrants (2x2) and, as a check, a 3x3 grid:

- `first_region` = the quadrant with the most dwell in the first third of the think.
- `persistence` = dwell share of `first_region` in the last third of the think.
- `disengage_slope` = slope of `first_region`'s dwell share over the four quarters of the think (linear regression). Sheridan & Reingold measured exactly this time course and found experts' share declines linearly while novices' does not ([2013](https://pmc.ncbi.nlm.nih.gov/articles/PMC3790829/)).
- `switches_per_10s` = number of changes of the dominant quadrant (smoothed over 500 ms windows) per 10 s.
- `regions_visited` = number of quadrants with ≥ 300 ms of dwell.
- Labels from the engine: the move is a **mistake where the better move lay elsewhere** if it loses ≥ 10 win-probability points and the best move's from- and to-squares are outside `first_region`, while the played move is inside it.
- The finding: mean `persistence` and `disengage_slope` on those mistakes against good moves with matched think time. Also per player: how `persistence` changes with think length (do long thinks stay narrow?).

**Data needed:** Gaze, move times, engine evaluations (best move and its squares). Works in real Lichess Board API games (rapid, classical) and in "guess the move" sessions; best in positions with two competing plans on different wings.

**Reliability:** Quadrants are assigned correctly for 70 to 91% of samples at 1.5° to 5° error (my simulation, [gaze-tracking.md](gaze-tracking.md#2-what-the-accuracy-means-on-a-chessboard)). Noise makes `switches_per_10s` and `regions_visited` too high, so the smoothing window and dwell threshold must stay fixed and comparisons stay within one player. `persistence` and `disengage_slope` average many samples and are the most robust. Needs long thinks, so rapid and classical, or training sessions with 60 s or more per position; not usable in bullet. Mistakes "elsewhere on the board" are perhaps a third of all mistakes (a guess, to check), so 100+ rapid games or a few hundred training positions before a per-player claim. Confounders: the best move can be in the same quadrant (then no signal), and calculation of a long line naturally keeps gaze in one region.

**Effort:** M. UI: per-think time course features. Insights service: matching, slope statistics. Position selection for training needs the engine.

**Prior work:** The Einstellung effect: experts said they were searching for a better solution while their eyes kept returning to the familiar one ([Bilalić, McLeod & Gobet 2008](https://pmc.ncbi.nlm.nih.gov/articles/PMC3790829/), described there), and a familiar solution lowered experts to the level of players about three standard deviations weaker. With the Einstellung move in a corner region (quadrant-sized), experts gradually looked away from it, F(1,66) = 13.12, and those who found the optimal move disengaged most strongly ([Sheridan & Reingold 2013](https://pmc.ncbi.nlm.nih.gov/articles/PMC3790829/)). See also [expertise-literature.md](expertise-literature.md) for familiarity effects. No product measures this. Engine tools see none of it.

**Why it's not engine review:** Game Review says "the best move was Rxe6". It cannot say "in 70% of your mistakes in rapid, your gaze stayed on the kingside for the whole think while the best move was on the queenside". The finding is about how the player searches, not about the move.

**Training link:** "Two-wing" drill: training positions with good options on both wings; the player must name one candidate move in each half of the board before moving. Also a prompt to "do a full-board sweep before committing" in long thinks. Improvement: a steeper (more negative) `disengage_slope` and fewer "elsewhere" mistakes per 100 moves.

**Verdict:** Later. Strongest link to published chess eye-tracking results, and it fits webcam resolution, but it needs long thinks and many games.
