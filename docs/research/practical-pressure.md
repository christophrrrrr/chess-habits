# Practical pressure balance

**Question:** Do you win by setting your opponents problems they fail to solve, and do you lose by drifting into positions that are hard for *you*? In other words: how much difficulty do you create, and how much do you face, compared with your opponents in the same games?

**What to measure:**

All quantities are per position and use win probability W from Stockfish (Lichess curve: W = 50 + 50·(2/(1+e^(−0.00368208·cp)) − 1), [lichess.org/page/accuracy](https://lichess.org/page/accuracy)) and Maia move probabilities P_r(m | pos), conditioned on the rating r of the player to move and of their opponent.

1. **Expected human loss (difficulty for a player rated r):**
   `EHL_r(pos) = Σ_m P_r(m | pos) · max(0, W(best) − W(m))`
   This is the average win% a player rated r would give away in this position. The sum runs over moves that together cover at least 95% of Maia's probability mass. Moves outside Stockfish's MultiPV get a `searchmoves` eval. This is the human-model version of position difficulty. Difficulty dominates error prediction ([Anderson et al. 2017](https://ar5iv.labs.arxiv.org/html/1606.04956)), and Maia's success probabilities are the strongest known feature for human difficulty ([FedCSIS 2025 entries](https://annals-csis.org/Volume_43/drp/pdf/6771.pdf)).
2. **Pressure created (PC):** the mean of `EHL_opp(position after your move)` over your moves. It measures how hard the positions you hand over are, for a player at your opponent's rating.
3. **Pressure faced (PF):** the mean of `EHL_you(position before your move)` over your moves.
4. **Pressure balance:** `PB = PC − PF`, per game and pooled. The same numbers are computed for the opponents in the same games, which gives a built-in control group of near-equal rating.
5. **Choice gap ("did you pick the testing move?"):** among the moves you could have played that lose at most 2 win% (that is, "objectively fine"), compare the PC of the move you chose with the highest PC available. `ChoiceGap = max_PC_safe − PC_chosen`. A large average gap means you regularly choose safe moves that ask nothing of the opponent.
6. **Optional risk measure** ([Carow & Witzig 2025](https://download.uni-mainz.de/RePEc/pdf/Discussion_Paper_2404.pdf)): the variance of `EHL_opp` over the opponent's 5 best replies (within 300 cp). It tells "sharp, double-edged" choices apart from "quietly difficult" ones.

Restrictions, following the literature: plies 16 to 80; |eval| < 300 cp before the move (decided positions add noise; [Regan et al. 2014](https://researchconnect.buffalo.edu/en/publications/human-and-computer-preferences-at-chess/) show that error scales with |eval|); skip moves made with under 10 s left (blunder rates jump below about 10 s, [Anderson et al. 2017](https://ar5iv.labs.arxiv.org/html/1606.04956)).

Output example (illustrative, not real data): "In equal middlegames your moves leave the opponent an expected 1.9% win to lose, against 2.6% for your opponents. In 41% of moves, a safe move existed that was at least 1% more testing. You are not short of accuracy; you are short of pressure."

**Data needed:** Games with clocks (chess.com PGN with `[%clk]`; Lichess later). Stockfish evals with MultiPV, computed in the browser (WASM), because chess.com PGNs carry no evals. Maia move probabilities: Maia-2 (MIT, Python, rapid/blitz checkpoints, [repo](https://github.com/CSSLab/maia2)) or Maia-3 (AGPL-3.0, ratings 600 to 2600, [repo](https://github.com/CSSLab/maia3)). Player and opponent ratings come from the PGN headers.

**Reliability:**

- **Noise sources:** (a) Maia is trained on Lichess blitz/rapid. Bullet is out of distribution, and the model has no clock input. (b) Maia-2 groups all players above 2000 into one bucket, which is bad for 2400 users; Maia-3 goes to 2600 Lichess blitz, but the mapping from chess.com ratings is unknown. (c) EHL inherits Stockfish depth noise. Depth 12 to 14 is probably enough for differences of a few win% (speculation; needs a check against depth 20 on a sample). (d) Opening theory inflates or deflates PC; excluding plies before 16 handles most of it.
- **Sample size (estimate, speculation until tested):** PC and PF are means over about 25 eligible moves per game. Their per-game SD is unknown. Assuming a per-move SD of about 3 win% and weak correlation within a game, 100 games (about 2,500 moves) give a standard error of roughly 0.06 win% on the mean, enough to detect gaps of 0.3 win% between player and opponents. Report the bootstrap CI over games, and show no finding below 50 games per time control.
- **Validation before shipping:** On a public Lichess sample, check that PB predicts game score beyond the rating difference. Logistic regression of the result on Elo difference + PB; the PB coefficient must be clearly positive. If it does not predict results, drop the feature.

**Effort:** L. Insights service: data model, aggregation and peer comparison. Browser: Stockfish WASM with MultiPV per position. Maia inference: either server-side Python (Maia-2 runs on CPU) in the scale-to-zero container as a batch job per import, or in the browser if Maia-3 can be exported to ONNX (unverified). Rough compute (speculation): 100 games × 40 positions × MultiPV-8 at depth 12 in WASM ≈ 30 to 60 min of browser time. It needs to be incremental and resumable.

**Prior work:**

- No consumer tool measures difficulty *created for the opponent*. chess.com Insights: accuracy, phases, tactics found/missed, openings ([support](https://support.chess.com/en/articles/8708925-what-is-insights-on-chess-com)). Aimchess: advantage capitalization, resourcefulness, and others ([aimchess.com](https://aimchess.com)). Lichess Insights: phase, move time, material.
- maiachess.com (Maia-3) shows a per-position "position danger" for your level and labels natural vs surprising mistakes in single Lichess games. It does not aggregate across games and does not measure the danger you hand the opponent ([launch post](https://hn.jakechampion.name/reader/https://lichess.org/@/ashtonanderson/blog/introducing-maia-3-free-and-open-source/vCPPRtX3)).
- Community metrics: "ease" for humans (Lichess blog by matstc) and Lc0 WDL sharpness = (2 / (ln(1/W−1) + ln(1/L−1)))² ([Chess Engine Lab, 2024](https://chessenginelab.substack.com/p/evaluating-sharpness-using-lc0s-wdl)). These are per-position and not validated against human results.
- Research: in engine-equal positions, human results lean towards one side, and the side that does worse thinks longer ([Park 2026](https://arxiv.org/abs/2607.25655)). Humans steer towards positions with fewer good options ([Regan et al. 2014](https://researchconnect.buffalo.edu/en/publications/human-and-computer-preferences-at-chess/)). Professionals take less risk under time pressure and more after their own mistakes ([Carow & Witzig 2025](https://ideas.repec.org/p/jgu/wpaper/2404.html)).

**Why it's not engine review:** Engine review asks "was your move best?" This asks "how hard was your move to answer for a human at your opponent's level?" Two moves with the same engine eval can differ a lot here. The output is a pattern over hundreds of games, compared with your own opponents, not a judgement of single moves. Neither chess.com Game Review nor any Insights product can tell you "you play safe, undemanding moves in equal positions".

**Training link:**

- **Low PC / high ChoiceGap:** a drill that shows positions from your own games where a safe and more testing move existed. You pick the move you would play, then see the more testing alternative and why it is hard to meet (top Maia replies for the opponent's rating and their win% loss). Also study model games in your own structures.
- **High PF:** find which structures and openings produce it (join on ECO or pawn structure), then change the repertoire or study those structures. This links to [structure-familiarity.md](structure-familiarity.md).
- **Measuring improvement:** rolling PC, PF and ChoiceGap over the last 50 games, compared with the baseline before training, with the bootstrap CI. Success means PC rises with no rise in your own excess loss.

**Verdict:** Later (after the MVP). It is the most novel candidate in this sweep and fits strong players best, but it needs Maia plus MultiPV engine evals and a validation step that PB predicts results. A cheap first step after the course: run the validation on a public Lichess sample offline.
