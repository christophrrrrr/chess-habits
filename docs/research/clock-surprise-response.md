# Response to the opponent's unexpected move

**Question:** When your opponent plays a move you (or players of your level) would not expect, do you notice it, spend time on it, and answer it well, or do your mistakes cluster right after surprises?

**What to measure:** Per time control, for each opponent move followed by an own move with `c ≥ 10%` (see [clock-and-time.md](clock-and-time.md)).

1. **Surprise** of the opponent's move `m_opp` in position `P`:
   - Target (later): `S = -log2 p_human(m_opp | P, rating)` where `p_human` is a human-move model's probability for a player of the **opponent's** rating (Maia-2, MIT, [CSSLab/maia2](https://github.com/CSSLab/maia2); or Maia-3, [CSSLab/maia3](https://github.com/CSSLab/maia3), AGPL-3.0 code). High `S` = a move a typical player at that level rarely plays.
   - Engine proxy (no human model): `m_opp` is outside Stockfish's top 3 at shallow depth, **or** it changed the evaluation by ≥ 10 Win% in either direction (a blunder by the opponent is also a surprise).
   - Personal proxy (no engine): the opponent left the player's own repertoire with this move (`opponent-exit`, see [clock-opening-speed.md](clock-opening-speed.md)); only covers the opening.
2. **Reaction time** = `r_k` of the player's next move, binned by surprise (low / mid / high tertiles of `S`).
3. **Reaction quality** = error rate (`ΔW ≥ 10`) on the next own move, by surprise bin, **within the same criticality band** of the position after `m_opp` (surprises tend to create critical positions; without the control the finding is trivial).
4. Named findings:
   - **Under-reaction**: high surprise, `r < 1` (no slowdown), error. "After unexpected moves you keep your normal pace and err 2x as often."
   - **Missed gift**: the opponent blundered (`ΔW_opp ≥ 20`), the player did not punish it (own move loses most of the gain). Lichess Insights' "Tactical awareness" covers punishing mistakes in general ([InsightMetric.scala](https://github.com/lichess-org/lila/blob/master/modules/insight/src/main/InsightMetric.scala)); the new part is the timing: did the player even slow down?
   - **Over-reaction** (speculative): high surprise of a harmless move, long think, later time trouble.

Per time control: **blitz, rapid, classical**. Bullet only for the missed-gift count. Not for Daily.

**Data needed:** PGN moves and `[%clk]`; Stockfish evals (browser) of the position before and after each opponent move; later a human-move model in the browser (Maia via ONNX Runtime Web: third-party browser ONNX exports of Maia-3 exist on Hugging Face, e.g. [bqrio/maia3-onnx](https://huggingface.co/bqrio/maia3-onnx); no Maia-2 browser export found; licences of weights to check).

**Reliability:**
- High-surprise moves are by definition a minority (top tertile = 1/3 of opponent moves, but meaningful surprises, e.g. `p_human < 5%`, are rarer). Expect ~150-300 blitz/rapid games before the under-reaction error rate has a useful CI.
- Surprise depends on the model: Maia predicts ~55-57% of human moves top-1 ([Maia-3 paper](https://arxiv.org/abs/2605.19091), [Otter](https://arxiv.org/abs/2608.05206)), so "surprise" is noisy for any single move; aggregate only.
- Main confound: surprising moves change the position's criticality. Always compare within criticality bands.
- Human models are trained mostly on Lichess games; chess.com ratings must be mapped (rough offsets; to research).

**Effort:** L. Needs the engine pipeline plus a human-move model running client-side (model choice, licence check, ONNX conversion, size).

**Prior work:**
- The vision document lists "your mistakes cluster after your opponent's unexpected moves" as an example finding ([vision.md](../vision.md)).
- Allie 2.1 predicts both moves and human think time, so it could define "expected reaction time" ([chess-v2](https://github.com/y0mingzhang/chess-v2)), but at 9.2B parameters it does not fit our constraints.
- No product found that measures time and quality after the opponent's surprising moves. Lichess Insights "Tactical awareness" and "Luck" measure punishing mistakes without timing ([InsightMetric.scala](https://github.com/lichess-org/lila/blob/master/modules/insight/src/main/InsightMetric.scala)).

**Why it's not engine review:** It explains a cause ("you don't slow down when surprised"), not a symptom ("move 23 was a mistake"), and it needs a model of what *humans* expect, which engine review does not have.

**Training link:**
- A "surprise check" habit: after any unexpected move, ask what it threatens before replying; drills built from the player's own under-reaction positions, shown right after the surprising move.
- Measure: error rate on replies to high-surprise moves and the median `r` after surprises, per quarter.

**Verdict:** **Later.** High novelty and directly from the vision, but needs both engine and human-model pipelines and large samples.
