# Cause-grouped drills from your own critical positions

**Question:** Which of your own critical positions should you practise, grouped by *why* you went wrong (missed the opponent's threat, did not slow down at a critical moment, answered a surprise on autopilot), and is the gap knowledge ("I could not solve it even with time") or process ("I solve it calmly but did not look in the game")?

**What to measure:**

1. **Win%** from the side to move, Lichess formula: `W(cp) = 50 + 50·(2/(1 + e^(−0.00368208·cp)) − 1)` ([Lichess accuracy page](https://lichess.org/page/accuracy)). Browser Stockfish, MultiPV 5, fixed depth (e.g. 18) or fixed nodes; engine id and depth stored with the eval.
2. **Item eligibility** (starting thresholds, to tune on real data):
   - player to move, ply > 16 or out of the player's opening tree;
   - loss `ΔW = W(best) − W(played) ≥ 10`;
   - holding set `H = {m : W(best) − W(m) ≤ 3}` is non-empty and the played move is not in it;
   - the position was not decided either way: `W(best) ≥ 15` and `W(played) ≤ 90`;
   - **learnable for this player's level:** `Σ_{m∈H} P_maia(m | pos, R_player, R_opp) ≥ 0.5` with Maia-2 (MIT) ([expertise-literature.md](expertise-literature.md)). Positions that peers also miss are excluded: they are not a personal blind spot and are often engine-only moves (vision principle 2).
3. **Cause label** (first matching rule wins; heuristics, to validate by hand on ~100 of the owner's positions):
   - *Missed opponent threat:* not in check; null-move probe: give the opponent the move in the same position; their best reply `t` gains `T = W_player(best) − W_player(null, t) ≥ 15`; and after the played move the opponent's best reply is `t` or hits the same target square.
   - *Reply to surprise:* the opponent's previous move had `P_maia < 0.10` at the opponent's rating ([clock-surprise-response.md](clock-surprise-response.md)).
   - *Under-thought critical moment:* only one move holds (`|H| = 1` and the second-best move is ≥ 10 Win% worse) and the player spent less than their median move time for that phase ([clock-time-vs-criticality.md](clock-time-vs-criticality.md)).
   - *Time-trouble error:* clock < 10% of base or < 10 s.
   - *Failed conversion:* `W(best) ≥ 85` in this position and the game was not won.
   - *Missed own chance:* `W(best) ≥ 70` and `W(played) < 60`, none of the above.
4. **Drill formats per cause** (all show the position as it was, with the opponent's last move highlighted):
   - *Threat drill:* step 1 "What does your opponent threaten?": the player plays the opponent's move on the board (accept `t` and any opponent move within 5 Win% of `t` in the null-move probe). Step 2: find your own move (accept any move in `H`).
   - *Think-or-play drill:* the position is shown for 2 s with two buttons, **Think** / **Play**. Items are the player's critical positions (`|H| = 1`) mixed 1:1 with *foils* from the same games where many moves are fine (`|H| ≥ 4`), ideally ones where the player spent a long time. Score with signal detection: hit rate `h` (Think on critical), false-alarm rate `f` (Think on foil), sensitivity `d' = z(h) − z(f)`. After **Think**, the board stays locked for a minimum time (10 s rapid items, 3 s blitz items), then the player moves.
   - *Surprise drill:* the opponent's surprising move is animated, then the player replies.
   - *Missed own chance:* find a move in `H`.
   - *Conversion drill:* play on from the position against Maia at the opponent's rating with the clock the player had (later; Aimchess has a vs-computer version).
   - *Time-trouble drill:* same position with the clock the player actually had.
   - Drill clock from the source game's time control: bullet 3-5 s, blitz 10-15 s, rapid 30-60 s, classical and daily untimed with "type your candidate moves first" (starting values, speculation).
   - Optional: before the reveal, "How sure are you?" (1-3). High-confidence misses are reviewed first (hypercorrection effect: confident errors are corrected more often and the correction lasts; [Fazio](https://dukespace.lib.duke.edu/items/d6ab09ca-f55c-4efb-9d32-2788bc5838b2)).
5. **Knowledge vs process split.** The first time an item is shown it is solved **untimed**. Per cause: `process share = solved untimed / all items`. High process share (e.g. > 70%) means "you know it, you did not look": the plan leans on rules and think-or-play/threat drills. Low process share means a knowledge gap: themed study and model games. Reported with a Wilson CI.
6. **Scheduling.** FSRS ([py-fsrs](https://github.com/open-spaced-repetition/py-fsrs), MIT; default desired retention 0.9). Outcome → FSRS rating: wrong = Again; correct over the time limit = Hard; correct within the limit = Good; correct in under half the limit = Easy (Chess Tempo also uses solve time to set the next gap: [manual](https://www.gwern.net/docs/www/chesstempo.com/01756e1305cd97d8abb5e2a7380635f9ea40f4fd.html)). Interleave causes within a session ([Brunmair & Richter 2019](https://pubmed.ncbi.nlm.nih.gov/31556629/)). **Retire** an item after 3 consecutive Good/Easy with interval > 21 days; top the deck up with new positions of the same cause from newer games. Session size about 15 items, 10 minutes (speculation).
7. **Transfer probes.** When a cause's deck is built, a random half of its eligible positions is **held out**. About 1 in 5 items in each session is a held-out position seen for the first time. Two drill-level indicators: probe accuracy and probe median solve time, per cause, over time. Accuracy on reviewed items is shown as "memory", never as improvement. Because drilled and held-out positions are split at random, the difference "probe accuracy now vs probe accuracy at the start" is a small within-player experiment on transfer.
8. **In-game target metric** per cause, measured by the [improvement tracker](training-improvement-tracker.md): e.g. missed-threat rate = missed threats / positions with an opponent threat `T ≥ 15`; under-think rate = fast moves in `|H| = 1` positions / all `|H| = 1` positions.

**Data needed:** chess.com PGNs with `[%clk]` (games service). Browser Stockfish WASM for MultiPV evals and the null-move probe (results posted to the insights service). Maia-2 move probabilities for the learnable filter and surprise label (where Maia runs, browser or container, is an open question). Review logs (move, correct, ms, confidence) stored in the insights DB.

**Reliability:**

- Item counts decide everything. Speculation until measured: a 2300 player may produce 1-3 eligible positions per rapid game, so 100 games give 100-300 items over all causes and maybe 20-80 per cause. The owner's 1,310 rapid games are enough; blitz and daily decks will be thin.
- Cause labels are heuristic. The null-move probe is unreliable in zugzwang and when the side to move is in check (excluded). Hand-check 100 positions before showing the labels to users.
- Think-or-play: `d'` needs about 40 critical items and 40 foils for a usable estimate (speculation; standard SDT practice).
- Knowledge-vs-process split may be biased: the player has played the game and may remember the answer. Mitigation: only items from games older than 14 days.
- Probe accuracy: with 15 items per session and 3 probes, 30 sessions give about 90 probes, so a Wilson CI of about ±10 pp per cause pooled. Enough to see big transfer effects only.
- Drill accuracy is not in-game improvement. The tracker's in-game metric is the outcome.

**Effort:** **M** (later **L** with Maia). Insights service: tables `drill_item` (fen, side, cause, prompt_type, accepted_moves_json, source_game_id, ply, time_limit_s, is_probe, fsrs_state_json, due_at, retired_at) and `review`; FSRS step per answer (py-fsrs server-side, or a JS port in the browser posting the new state). Item generation runs in the browser right after the engine pass, so the containers stay small and scale to zero. UI: one drill board with three prompt types.

**Prior work:**

- Turning own mistakes into puzzles is common: Lichess "Learn from your mistakes" (one game, no scheduling) ([blog](https://lichess.org/@/lichess/blog/learn-from-your-mistakes/WFvLpiQA)); chess.com "Retry" (one game) ([help](https://support.chess.com/en/articles/8584089)); Aimchess Retry Mistakes, Blunder Preventer, Advantage Capitalization, Time Trainer ([aimchess.com](https://aimchess.com)); Chessable Puzzle Connect (10 or up to 1,000 puzzles from your chess.com mistakes) ([announcement](https://www.chess.com/news/view/announcing-chessable-3)); Chessiro Smart Shuffle ([blog](https://chessiro.com/blog/puzzles-from-your-own-games)); Chess Tempo spaced-repetition custom sets.
- Not found anywhere: grouping by cause, the threat-first two-step format, think-or-play recognition with foils, a human (Maia) learnability filter, the knowledge-vs-process split, held-out transfer probes.
- Learning science behind the design: spacing ([Cepeda et al. 2006](https://pubmed.ncbi.nlm.nih.gov/16719566/)), retrieval ([Rowland 2014](https://pubmed.ncbi.nlm.nih.gov/25150680/)), interleaving of similar categories ([Brunmair & Richter 2019](https://pubmed.ncbi.nlm.nih.gov/31556629/)), variability for generalisation ([Raviv et al. 2022](https://eprints.gla.ac.uk/272070)). See [training-loop.md](training-loop.md).

**Why it's not engine review:** Game Review offers "retry this move" for one game and grades against the engine's best. These drills are chosen by a cross-game *cause* finding, filtered by what players of your level find, accept any holding move, train noticing and time allocation rather than the answer, and report whether the failure is knowledge or process. None of that comes from a single-game review.

**Training link:** This is the practice step. Success is measured in games with the tracker: the cause's in-game rate against its split-sample baseline and against untrained causes. Drill-level probe accuracy is a leading indicator only.

**Verdict:** **Later** (first feature after the course). It needs the browser engine pass (and Maia for the full version), which is out of scope for the 2026-11-24 MVP. Build order: threat drill and missed-own-chance drill with FSRS and the knowledge-vs-process split first (engine only); then the Maia filter, think-or-play and surprise drills.
