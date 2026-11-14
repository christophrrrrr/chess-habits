# Reaction to surprising opponent moves

**Question:** Do you play worse, or think too long or too short, right after your opponent plays a move a player like you would not have expected, and does that depend on whether the surprise was a strong move or a mistake?

**What to measure:**

1. **Surprise of an opponent move `m_o` in position `Q`:** `S = -log2 p(m_o | Q)`, where `p` comes from a human move model. With [Maia-2](https://arxiv.org/abs/2409.20553) (MIT, [code](https://github.com/CSSLab/maia2)) or [Maia-3](https://arxiv.org/abs/2605.19091) (AGPL-3.0 code, [repo](https://github.com/CSSLab/maia3)), the model is conditioned on the ratings.
   - *Which rating to condition on is a design choice and is speculative.* Using the **player's** rating as the mover's rating approximates "would someone of your strength have anticipated this?". Using the opponent's rating approximates "was this move unusual for this opponent?". Start with the player's rating.
   - Mark `surprising` if `p < 0.05` (S > 4.3 bits) and `expected` if `p >= 0.30`. The cut-offs are to be tuned on the distribution.
   - **Engine-only fallback** (no Maia): `surprising` if `m_o` is not among the engine's top 3 and is not a capture or check that recaptures material just lost. This proxy is weaker, because many quiet engine-top moves are surprising to humans.
2. **Split by surprise quality,** using the opponent move's own WPL:
   - `good surprise`: WPL ≤ 3 (a strong move you did not see coming).
   - `bad surprise`: WPL ≥ 10 (an unexpected mistake, which creates a chance).
   - `neutral`: everything else.
3. **Response metrics** on the player's next own move and the move after it:
   - `WPL_next`.
   - `chance_taken`, for bad surprises: did the player recover ≥ 50% of the win% the opponent gave away?
   - `time_ratio = t_next / median(t | same clock bucket)`. Move times come from consecutive `[%clk]` values plus the increment.
4. **Matched comparison:** for each surprising event, take control events (after expected opponent moves) from the same player with the same eval bucket, criticality bucket (gap between best and second move, see [game-decision-points.md](game-decision-points.md)) and clock bucket. Report `excess_WPL = mean(WPL_next | surprising) - mean(WPL_next | matched expected)` and the same for `chance_taken` and `time_ratio`. Use a game-cluster bootstrap for CIs.
5. **Lingering effect:** the same excess on own moves +2 and +3 after the surprise. Is the effect a one-move shock or a longer disruption?

**Data needed:** PGN and `[%clk]` (chess.com); engine evals (best, second best, and the opponent move's WPL) from the browser Stockfish job; a Maia model run on the opponent's moves.
- Maia-3's smallest model checkpoint is about 21 MB (`maia3-5m.pt` on [Hugging Face](https://huggingface.co/UofTCSSLab/Maia3-5M)) and is PyTorch. Running it in the browser would need an ONNX export. *Untested; speculative.*
- Maia-3 was trained on Lichess **blitz** (Jan 2023 to Jul 2025) and drops positions where the mover had less than 30 s, per the [paper](https://arxiv.org/abs/2605.19091). Surprise estimates for bullet and for time-trouble positions are therefore out of distribution.
- Maia-2's top rating bucket is "≥2000" ([paper](https://arxiv.org/abs/2409.20553)), which is coarse for a 2300+ player. Maia-3 uses 100-point bins from 600 to 2600.

**Reliability:**
- Events are plentiful: every game has several opponent moves with Maia `p < 0.05`. Each event, though, is a single move with a heavy-tailed WPL. Expect to need about 150 or more surprising events, which is about 50 to 100 games, before an excess of 2 or 3 win% per move separates from zero. *Estimate; verify with real data.*
- Main confounder: surprising moves are more often **opponent mistakes**, and mistakes create critical positions with big possible losses. Matching on criticality and splitting by surprise quality handles most of this. Without the split, the analysis would only rediscover "positions after opponent blunders are sharp".
- Model mismatch: the opponent's rating pool (chess.com) is not the training pool (Lichess). Rating offsets between sites are not established here.

**Effort:** L. It needs Maia inference, which no other MVP analysis needs, plus matched controls. Runs in **insights**, with Maia possibly in the browser.

**Prior work:**
- **Lichess Insights** "Tactical awareness" ("How often you take advantage of your opponent mistakes"). It is computed as: after an opponent mistake or blunder, your next move is not itself a mistake ([InsightMetric.scala](https://github.com/lichess-org/lila/blob/master/modules/insight/src/main/InsightMetric.scala), [PovToEntry.scala](https://github.com/lichess-org/lila/blob/master/modules/insight/src/main/PovToEntry.scala)). It covers bad surprises only, with no notion of *unexpectedness* and no time component.
- chess.com Game Review "Miss" labels single failures to punish an opponent mistake ([classification help](https://support.chess.com/article/2965-how-are-moves-classified-what-is-a-blunder-or-brilliant-and-etc)).
- Research: the Einstellung effect. A familiar idea blocks a better one, even in experts ([Bilalić, McLeod & Gobet 2008, *Cognition* 108:652–661](https://doi.org/10.1016/j.cognition.2008.05.005)). This is a plausible mechanism for "you keep playing your plan after the opponent changed the position". Maia's authors frame human-move prediction as a way to find positions where humans err ([McIlroy-Young et al. 2020](https://arxiv.org/abs/2006.01855)).
- No tool or paper was found that measures a player's response to *unexpected* opponent moves across their games.

**Why it's not engine review:** The engine judges your reply against the best reply. It cannot say that your replies are worse **because** the previous move was unexpected, which needs a human model and a matched baseline across many games. This is the vision's own example of a cause ("Your mistakes cluster after your opponent's unexpected moves").

**Training link:**
- A weakness after good surprises (you are shocked by strong moves) suggests "candidate moves for the opponent" drills: before each move in a drill, list the opponent's three most dangerous replies, then check them.
- A weakness after bad surprises (you miss the gift) suggests "punish the mistake" puzzles built from the player's own games, in their positions.
- Improvement: `excess_WPL` and `chance_taken` on new games against the pre-training value, with the same matching.

**Verdict:** **Later.** It is novel and fits the vision exactly, but it depends on Maia inference and on the taxonomy and criticality pipelines existing first. Revisit after the course, together with the gaze work, since gaze could show whether the player looked at the opponent's move at all.
