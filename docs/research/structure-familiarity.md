# Structure familiarity (the specialization effect)

**Question:** Do you score and play worse in pawn structures you rarely reach, and which unfamiliar structures cost you the most?

**What to measure:**

The analysis tests, for each player, the expertise finding that skill is partly bound to familiar patterns. Experts play about one standard deviation of skill better in positions from their own specialty ([Bilalić, McLeod, Gobet 2009](https://pubmed.ncbi.nlm.nih.gov/21585497/)), and chunks encode specific spatial patterns ([Gobet & Simon 1996](https://www.Gwern.net/doc/psychology/chess/1996-gobet.pdf)). It complements [clock-opening-speed.md](clock-opening-speed.md), which handles *exact* repertoire positions and the time spent after leaving them. This note is about the **middlegame structure**, which can be familiar even after the moves are new, and unfamiliar even inside a known opening.

All familiarity is computed from the player's **own strictly earlier games, same colour**. Live time controls are pooled for familiarity, because a structure is the same whatever the clock.

1. **Structure key** at the "structure ply" `p*`: the first ply ≥ 24 at which no pawn was captured on the last 2 plies, capped at ply 40. If the game ends earlier, it has no key.
   - `key_core` = the squares of all white and black pawns on files c, d, e, f. This defines the central structure (Carlsbad, IQP, Maroczy, French chain, open centre, and so on).
   - `key_full` = the squares of all pawns, used for the similarity measure.
2. **Familiarity count** for game g: `fam(g)` = the number of earlier own games (same colour) with an identical `key_core`, **or** with a Jaccard similarity of 0.75 or more between `key_full` sets. Buckets: 0, 1–4, 5–19, 20+.
3. **Results metric (no engine needed):** Elo residual per game, `res = score − 1/(1 + 10^((R_opp − R_you)/400))`. Report the mean residual per familiarity bucket, per time-control group, with bootstrap 95% CIs. Also fit a logistic model per player: `win/draw/loss ~ rating diff + log(1 + fam)`, with the opening family (first 3 ECO characters) as a fixed effect when n allows. The fixed effect keeps "unfamiliar structure" separate from "bad opening".
4. **Worst unfamiliar structures:** group games by `key_core` and rank by n × (−mean res), restricted to keys reached 5 or more times overall but with low familiarity when first met. Show a sample position and the openings that led there.
5. **Quality metric (engine, later):** mean win% loss on own moves at plies `p*` to `p*+30`, by familiarity bucket, in the same |eval| band. This is better done as excess loss compared with Maia peers (see [expertise-literature.md](expertise-literature.md)), which removes the "harder structures are just harder" confound.
6. **Clock side-metric (cheap):** median relative think time on moves `p*`..`p*+10` by bucket, using `[%clk]` and the same own-baseline normalisation as the clock notes. If unfamiliar structures cost both time and score, the finding is stronger.

Output example (illustrative): "In rapid, in structures you have reached fewer than 5 times before, you score 7 points below expectation (n=210, CI −12 to −2). In familiar ones you score +2. The biggest losses come from IQP positions with the isolated pawn on *your* side, which you reached 23 times, mostly from the Caro-Kann Panov."

**Data needed:** Games only: chess.com PGN (moves, ratings, `[%clk]`, `ECOUrl`), sorted by date. python-chess in the insights service builds the pawn sets. An engine is only needed for metric 5. The owner already has 2,670 chess.com games since 2023-07 (rapid 1,310, bullet 846, blitz 461) per [prior-work-gap-map.md](prior-work-gap-map.md).

**Reliability:**

- **Results noise:** a game score has SD ≈ 0.45 to 0.5. With 150 games per bucket, the SE of a difference between two buckets is about 0.05, enough to detect about 0.1 score (about 70 Elo) at 95% confidence. Show a finding only when each compared bucket has 100 or more games and the CI of the difference excludes 0. Otherwise show "not enough games yet". With about 1,300 rapid games, the owner can reach this in rapid; blitz probably cannot.
- **Expected effect size:** unknown for real games. The lab effect (about 1 SD) comes from positions picked to be in or out of a specialty. In real games, unfamiliar structures are rarer and partly shared with opponents, so expect a much smaller effect (speculation). The validation step below decides whether this ships.
- **Confounders:** (a) Opening choice: handled by the opening-family fixed effect. (b) The opponent's preparation: opponents who steer into rare structures may be stronger than their rating. Rating handles part of this, not all. (c) History length: require 200 or more earlier games before a game counts. (d) Structure key quality: exact `key_core` may be too fine or too coarse, so check that buckets are not dominated by one key. (e) Daily games allow books and databases: analyse them separately. (f) Bullet: familiarity effects probably show up on the clock, not in results.
- **Validation before shipping:** on a public Lichess sample of 1,000 players with 1,000+ games each, check whether `log(1 + fam)` has a positive coefficient on results after controlling for rating difference and opening family. If the population effect is about zero, drop the feature.

**Effort:** S for metrics 1 to 4 and 6 (insights service: one ordered pass per player storing `p*`, `key_core`, `key_full` and `fam` per game, then SQL aggregation with bootstrap CIs, plus one table and one chart in the UI). M to add metric 5 once engine evals exist.

**Prior work:**

- **chess.com Insights:** results for your top 10 openings and "book moves before leaving theory" ([support](https://support.chess.com/en/articles/8708925-what-is-insights-on-chess-com)). **Advanced Stats** gives a "pawn structure" *skill* rating ([help](https://support.chess.com/en/articles/15451190-how-do-i-use-advanced-stats)), which is about handling structures in general, not about how familiar each structure is to you.
- **Aimchess:** "Opening performance" (advantage after the opening) ([aimchess.com](https://aimchess.com)). **Lichess Insights:** dimensions include opening family and material imbalance, not pawn structure familiarity (see [prior-work-gap-map.md](prior-work-gap-map.md)).
- **Research:** specialization effect ([Bilalić et al. 2009](https://pubmed.ncbi.nlm.nih.gov/21585497/)); chunk and template theory ([Gobet & Simon 1996](https://www.Gwern.net/doc/psychology/chess/1996-gobet.pdf)); players narrow their opening repertoire over time and misjudge their best openings ([Chowdhary et al. 2023](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9902564/)).
- I found no tool that relates a player's results or move quality to how often *they* have reached a structure before.

**Why it's not engine review:** No single game can show this. It needs the player's history to define "familiar". It needs no engine, and it explains a cause ("you lose in structures you don't know, not in openings you don't know") rather than grading moves.

**Training link:**

- For the 3 worst unfamiliar structures: a short structure plan (typical pawn breaks, piece placement), 5 model games in that structure, and a drill set of the player's own positions from those games (shared with the training-loop note). Alternatively, change the repertoire to avoid the structure, and say which opening move leads into it.
- **Measuring improvement:** for each trained structure, track the residual and (later) the excess loss in new games reaching it, against the pre-training baseline, as a rolling window. Familiarity rises by itself as games are played, so the success criterion is the *gap* closing faster than for comparable untrained structures (a rough control).

**Verdict:** Build for MVP (results-only metrics 1 to 4 and 6), behind the validation check; add the engine metric later. It is cheap, works with data we already import, rests on one of the most robust findings in expertise research, and no existing tool offers it.
