# Maia-3 as the human baseline

**Question:** Across many games, which of your mistakes would most players at your rating also make, and which do they usually avoid? In other words, where are your blind spots relative to peers, and how much do you lose compared with what a peer would lose in the same positions?

**What to measure:**

Notation:
- `s` is a position with the user to move.
- `R` is the user's rating and `R_o` the opponent's, both converted to the Lichess blitz scale (see Data needed).
- `P_R(m|s)` is Maia-3's move probability: softmax over the *legal* moves of `logits_move`, with `elo_self = R` and `elo_oppo = R_o`.
- `ΔW(m)` is the win-% loss of move `m` from the mover's point of view: `Win%(best) - Win%(after m)`. Win% comes from the Stockfish centipawn score with the Lichess formula `50 + 50 * (2 / (1 + exp(-0.00368208 * cp)) - 1)`.

Per position:
1. **Peer expected loss** (human difficulty): `E_R(s) = Σ_m P_R(m|s) * ΔW(m)`. Compute it over Maia's top-k moves (k ≤ 5, stop once cumulative probability ≥ 0.90), renormalised. Store the covered mass. Each extra move costs one shallow Stockfish search (depth 10) of the position after it. This follows Anderson et al., who found that position difficulty predicts blunders better than skill or time.
2. **Peer blunder probability:** `B_R(s) = Σ_m P_R(m|s) * [ΔW(m) ≥ 10]`.
3. **Played move probability:** `p_played = P_R(m_played|s)` and surprisal `-log2 p_played`.
4. **Mistake label for the user's move:** a *mistake* has `ΔW(played) ≥ 10`. It is **surprising** if `B_R(s) ≤ 0.15` (peers rarely go wrong here) and **natural** if `B_R(s) ≥ 0.40`. In between it is neutral. Thresholds are starting values to tune on data.
5. **Superhuman filter:** if the engine's best move has `P_{R+200}(best|s) < 0.03`, the "missed" move is one that even somewhat stronger humans almost never find. Do not count it as a blind spot.

Aggregated over a context `C` (phase, material, clock bucket, opening family, "after an unexpected opponent move", ...):
- **Excess loss:** `X(C) = mean over s in C of [ΔW(played) - E_R(s)]`, in win-% points per move. Report a 95% CI by bootstrapping over **games** (moves within a game are not independent).
- **Surprising-mistake rate:** `count(surprising mistakes in C) / count(positions in C)`, compared with the rate across all the user's positions.
- **Opponent surprise** (input for other notes): `S(m_o) = -log2 P_{R_o}(m_o|s_o)` for the opponent's previous move.

**Data needed:**
- **Games and clocks:** chess.com PubAPI (games service). `[%clk]` per move in 0.1 s steps; both players' ratings are in the PGN headers.
- **Engine evals:** Stockfish 19 lite WASM in the browser (see [engines-and-human-baseline.md](engines-and-human-baseline.md)). Depth 12 for every position, plus depth 10 on the top-k Maia candidate moves of positions where the user is to move.
- **Maia-3 5M** ([CSSLab/maia3](https://github.com/CSSLab/maia3); ONNX export [bqrio/maia3-onnx](https://huggingface.co/bqrio/maia3-onnx), 10.8 MB fp16). Run it in the browser with onnxruntime-web. Inputs: `tokens` [n, 64, 12] (pieces only, board mirrored when Black is to move), `elo_self`, `elo_oppo`. Outputs: `logits_move` [n, 4352] and `logits_value` [n, 3] (loss/draw/win for the side to move). The move index map is the 4,352-entry UCI table used by Maia-3 (64x64 from-to plus promotions). Black moves are mirrored before lookup. Write the preprocessing ourselves from the model card. Do not copy GPL code from maia-platform-frontend.
- **Rating conversion:** Maia-3 covers **600-2600 Lichess blitz** ([announcement](https://lichess.org/@/ashtonanderson/blog/introducing-maia-3-free-and-open-source/vCPPRtX3)). For chess.com blitz use the ChessGoals table (1800→1950, 2000→2080, 2200→2210, 2400→2340; [ChessGoals](https://chessgoals.com/rating-comparison/)). For chess.com rapid, bridge through chess.com blitz in the same table. Clamp to 2600.
  - Per-user check: `R* = argmax_R Σ log P_R(played)` over ≥ 300 positions, searched in ±200 around the mapped rating.
  - Measured on the owner's games, the likelihood rises from R = 1500 to 2400 and is flat from 2400 to 2600 (mean surprisal 2.19 → 1.95 → 1.95 bits). For 2400+ players, use the mapped rating and do not trust `R*` alone.
- **Cost:** about 77k Maia evaluations per 1,000 rapid games, at roughly 15-25 ms each in the browser (estimate; 9.5-17.8 ms measured natively). Plus ~115k shallow Stockfish searches for the difficulty term.

**Reliability:**
- Maia-3 5M predicts the human move 55.4% top-1 ([paper](https://arxiv.org/html/2605.19091)). Single-position probabilities are noisy, so **never** show a per-move verdict as a finding. Only aggregates count.
- **Sample size:**
  - Contexts with fewer than **200 user positions** or **30 mistakes** get no claim.
  - Example: with 100 mistakes, a 30% surprising share has a 95% interval of about ±9 points (binomial). 1,000 rapid games give ~38k user positions. A strong player's mistake rate is not yet measured, so the number of mistakes per context is unknown.
  - A weekly window of ~50 games supports only one or two coarse contexts.
- **Known noise and bias sources:**
  - **Trained on Lichess blitz** (Jan 2023 to Jul 2025), so it models blitz, not rapid or classical play.
  - **Positions with under 30 s on the clock were dropped in training**, so `E_R` and `B_R` are not valid in time trouble. Exclude those positions, or use the population baseline built from the Lichess open database for them.
  - **chess.com vs Lichess populations differ**, and rating conversion error at 2200+ is unknown.
  - **No castling or en-passant rights in the tokens**, which causes rare errors.
  - **The difficulty term is truncated** at top-k (store the covered mass; drop positions under 0.8).
  - **Stockfish depth 12 noise** in ΔW. Depth 12 agreed with depth 22 on 71.5% of best moves in the Maia platform's own test ([LOADING.md](https://github.com/CSSLab/maia-platform-frontend/blob/main/LOADING.md)). Use win-% thresholds of 10 or more, not small ones.
- **Validation before shipping:** draw a reliability diagram on held-out games of the user and of similar-rated opponents. Bucket positions by `B_R(s)` and compare with the observed mistake rate, separately per time control. If the curve is badly off for chess.com rapid, recalibrate (e.g. isotonic regression per time control) or drop the time control.

**Effort:** M for P(move | R) per position: browser Maia worker, preprocessing, storage in insights. L for the difficulty term and the excess-loss findings, which need extra Stockfish searches and bootstrap CIs. Compute runs in the **browser**. Storage and aggregation belong to the **insights** service, with one row per ply: `p_played, p_engine_best, entropy, top-k moves+probs, human_wdl, E_R, B_R, covered_mass, maia_id`.

**Prior work:**
- **[maiachess.com](https://maiachess.com)** (Maia-3, May 2026) already shows, **per position and per game**:
  - moves by rating,
  - "blunder detection that understands which mistakes are natural and which are surprising for your level",
  - "position danger analysis",
  - a human evaluation bar ([announcement](https://lichess.org/@/ashtonanderson/blog/introducing-maia-3-free-and-open-source/vCPPRtX3)).

  It works on Lichess games and does not aggregate across a player's history or link to the clock.
- **chess.com Game Review** grades moves against the engine and estimates a per-game rating. **Lichess Insights** has no human baseline.
- **Research:**
  - Anderson, Kleinberg and Mullainathan show that position difficulty (share of moves that are blunders) predicts human blunders far better than skill or time remaining ([arXiv 1606.04956](https://arxiv.org/abs/1606.04956), [TKDD version](https://www.cs.toronto.edu/~ashton/pubs/tbase-tkdd.pdf)).
  - Maia-2 ([arXiv 2409.20553](https://arxiv.org/abs/2409.20553)) and Maia-3/Chessformer ([arXiv 2605.19091](https://arxiv.org/abs/2605.19091)) are the models.
  - Individual Maia models: [Learning Models of Individual Behavior in Chess](https://www.microsoft.com/en-us/research/?p=863784).
- **Why not the other models:** Maia-2 (MIT) and Otter ([arXiv 2608.05206](https://arxiv.org/abs/2608.05206)) put every player above Lichess 2000 into one bin, and Maia-1 stops at 1900. That makes them useless for our 1800+ users.

**Why it's not engine review:**
- Engine review says "this move lost 15%".
- This note says "positions like this cost players at your level 3% on average, and you lose 9% in them". It also separates mistakes peers make too (low priority) from mistakes peers usually avoid (blind spots), across hundreds of games and split by context (phase, clock, opening, after a surprise).
- chess.com cannot tell you this because it has no human-at-your-rating model. maiachess.com gives the per-position ingredient but not the cross-game, context-split, confidence-bounded finding.

**Training link:**
- **Surprising mistakes** become drills: the position before the mistake, solved under a time limit that matches the time control, with spaced repetition. They are the highest-value material because peers find these moves.
- **High excess loss in a context** (e.g. "endgames with rooks", "first move after an unexpected reply") points to themed practice in that context.
- **Natural mistakes in high-`E_R` positions** are not blind spots. The advice there is about time allocation, e.g. spending more clock when `E_R` is high (link to the time-vs-criticality note).
- **Measuring improvement:** recompute `X(C)` and the surprising-mistake rate over rolling windows of 200 games (rapid) or 500 games (blitz/bullet). Improvement is claimed only if the bootstrap CIs of two windows do not overlap, or if a pre-registered one-sided test passes. Keep `maia_id` and `engine_id` fixed across windows.

**Verdict:** **Later** (first analysis after the MVP). It is the strongest differentiator for 1800+ players, and the browser pipeline is proven by the Maia platform. But it needs the MVP's eval pipeline first, a calibration check for chess.com rapid, and an answer from CSSLab on the weight licence.
