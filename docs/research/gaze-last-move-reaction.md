# Gaze: reaction to the opponent's last move

**Question:** Do you look at what your opponent just did, and how quickly, and is skipping that look followed by mistakes?

**What to measure:** For each of your thinks, using the opponent's last move (from-square F, to-square T):

- `lm_zone` = the 3x3-square zone around T, plus the 3x3 zone around F (the from-square matters for discovered attacks and for what the moved piece stopped defending).
- `lm_latency` = time from the opponent's move appearing to the first run of ≥ 200 ms of gaze samples inside `lm_zone`. Censored at the player's move time if it never happens.
- `lm_early_share` = dwell share in `lm_zone` during the first 3 s of the think (or the first 30% of the think, whichever is shorter, for fast time controls).
- `lm_looked` = `lm_latency` < 3 s (binary).
- Per player: the rate of `lm_looked` and the median `lm_latency`, split by (a) whether the opponent's move created a new threat (engine: the opponent's best next move gains ≥ 10 win-probability points if you pass) and (b) whether your reply was a mistake. Key number: the mistake rate after threat-creating moves when `lm_looked` is false vs true.
- Exclude zones that overlap your own last moved piece's zone, where gaze would be there anyway, and recaptures, where looking is trivial.

**Data needed:** Gaze, move timestamps (Lichess Board API game stream or Kiebitz training sessions that replay the opponent's last move as an animation before the player's turn), engine evaluations for the threat and mistake labels.

**Reliability:** The zone is about 3x3 squares, so this is at the edge of webcam resolution. At 4° error on a desktop board, a sample is counted in the zone 56% of the time when the player looks at its centre and 9% of the time when they look 3 squares away (my simulation, [gaze-tracking.md](gaze-tracking.md#2-what-the-accuracy-means-on-a-chessboard)). Requiring a 200 ms run of samples cuts false hits. Per-move values are noisy; per-player rates over 200+ thinks are usable. The link to mistakes needs about 30+ mistakes after threat-creating moves, so many games or targeted training sessions. Big confounder: **the last-move highlight** on the board and strong players' peripheral vision ([de Winter et al. 2023](https://www.journalofexpertise.org/articles/volume6_issue1/JoE_6_1_deWinter_etal.pdf); [Reingold et al. 2001](https://www.cs.umb.edu/~marc/pubs/reingold_et_al_psysci2001.pdf) found 15.9% of expert check-detection trials needed no eye movement at all). A player may register the move without moving their eyes. Bullet and blitz premoves make this metric meaningless for those moves.

**Effort:** S on top of the gaze pipeline (one more zone per move). UI computes features; insights service aggregates.

**Prior work:** None in products. In the lab, experts reach relevant regions faster: time to first fixation 407 ms vs 719 ms for novices on a target region ([Sheridan & Reingold 2013](https://pmc.ncbi.nlm.nih.gov/articles/PMC3790829/)), and only experts' first dwell favours the relevant half ([Sheridan & Reingold 2014](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2014.00941/full)). Nobody has measured attention to the opponent's last move in real games. The vision lists "reaction to the opponent's last move" as a candidate ([vision.md](../vision.md)).

**Why it's not engine review:** Game Review sees only the moves. "After your opponent's quiet moves you look at them in only 40% of your thinks, and half of your missed threats follow exactly those moves" is a habit, not a move evaluation.

**Training link:** The "what changed?" habit: in training sessions, the opponent's move is shown, and the player must name what it attacks or what it gave up before moving (quick multiple choice). Improvement: higher `lm_looked` rate after threat-creating moves, and a lower mistake rate after such moves in real games.

**Verdict:** Later. Cheap once the gaze pipeline exists, and the most intuitive gaze finding for players. But the peripheral-vision problem means a "did not look" reading may be wrong for strong players, so we need validation before showing it as a finding.
