# Expertise literature: what separates 1800 from 2400+, and what predicts lost points

Research sweep, 2026-11-12. Scope: academic work on chess expertise and decision quality that Chess Habits can turn into analyses for strong players (1800+). Every claim has a link. Where I could not check a number in the primary source, I say so.

## Summary

1. **Position difficulty explains errors better than rating or clock.** On solved (tablebase) positions, a model using only position difficulty predicted blunders with 73% accuracy, against 55% for rating and 53% for time left ([Anderson et al. 2017](https://ar5iv.labs.arxiv.org/html/1606.04956)). So raw accuracy averaged over games mostly measures how hard a player's positions were, not how well they played. **Every Chess Habits metric should be difficulty-adjusted**, meaning it compares the player against what peers would do in the same positions.
2. **We now have a usable model of "what peers would do".** Maia-2 (NeurIPS 2024, MIT licence) and Maia-3 (ICLR 2026, AGPL-3.0, released May 2026) give move probabilities conditioned on the ratings of both players. Maia-3 covers ratings 600 to 2600 (Lichess blitz) and matches 57.1% of human moves ([Monroe et al. 2026](https://arxiv.org/abs/2605.19091), [CSSLab/maia3](https://github.com/CSSLab/maia3)). For 2400 players this matters: Maia-1 stopped at 1900, and Maia-2 puts everyone above 2000 into one bucket ([Maia-2](https://arxiv.org/html/2409.20553v2)).
3. **Single-game "is this mistake typical for my level" already exists.** Maia-3 on maiachess.com tells you which mistakes are "natural" and which are "surprising" for your level, and shows a "position danger" measure, for Lichess games ([Maia-3 launch post](https://hn.jakechampion.name/reader/https://lichess.org/@/ashtonanderson/blog/introducing-maia-3-free-and-open-source/vCPPRtX3)). So per-game blind-spot labels fail the vision test. Chess Habits' gap is **aggregation across hundreds of games, chess.com support, and causes**.
4. **At 1800 vs 2400, the differences are small per move but steady.** In Regan and Haworth's fits, the engine-match rate climbs from 46.9% (2000) to 52.3% (2400) and 56.2% (2700). The average scaled error falls from 0.110 to 0.072 pawns ([Regan & Haworth 2011](https://www.cse.buffalo.edu//~regan/papers/pdf/ReHa11c.pdf)). Strong players also put their thinking time where thinking pays off ([Russek et al. 2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC12553403)), stop allocating time badly when the clock is low ([Howard 2021](https://mpra.ub.uni-muenchen.de/108243/)), and judge positions more accurately at a glance ([Chassy et al. 2023](https://pmc.ncbi.nlm.nih.gov/articles/PMC10497664/)).
5. **Familiarity is a large, measurable effect.** Experts play about one standard deviation of skill better in positions from their own opening specialty ([Bilalić et al. 2009](https://pubmed.ncbi.nlm.nih.gov/21585497/)). Chunks encode specific spatial patterns ([Gobet & Simon 1996](https://www.Gwern.net/doc/psychology/chess/1996-gobet.pdf)). This supports a new analysis: how a player scores and plays in pawn structures they rarely reach, compared with the structures they know (see [structure-familiarity.md](structure-familiarity.md)). The exact-position version (leaving your own repertoire, and the time spent after it) is in [clock-opening-speed.md](clock-opening-speed.md).
6. **Strong humans win by setting problems, not only by avoiding errors.** In positions that the engine rates equal, results still lean towards one side, and the effect replicates across separate groups of accounts. The side that does worse also spends more time thinking ([Park 2026](https://arxiv.org/abs/2607.25655)). Humans also steer towards positions with fewer reasonable options ([Regan et al. 2014](https://researchconnect.buffalo.edu/en/publications/human-and-computer-preferences-at-chess/)). This supports measuring how much difficulty a player creates for the opponent and how much they face (see [practical-pressure.md](practical-pressure.md)).
7. **Evidence on tilt is mixed and comes mostly from elite over-the-board play.** Within a game, small inaccuracies are followed by worse play, while blunders are followed by more careful play ([Adhikari et al. 2023](https://pages.nes.ru/sanatoly/Papers/TiltChess.htm)). Between games, titled men play less accurately after a loss and choose riskier openings ([Engel, working paper](https://sites.google.com/view/julia-f-engel/job-market-paper)). Treat tilt as a hypothesis to test for each player, not as a known fact.
8. **Deliberate practice matters but explains only about a third of skill.** Serious solo study predicts rating better than tournament play or lessons ([Charness et al. 2005](https://zendy.io/title/10.1002/acp.1106)), and deliberate practice explains about 34% of variance in chess skill ([Hambrick et al. 2014](https://www.bps.org.uk/research-digest/exploding-10000-hours-myth-its-no-guarantee-greatness)). Chess Habits' training suggestions should be specific, solo, and tied to feedback. "Play more games" is not training.

## Papers

Each entry gives the finding, the dataset, the effect size, and what Chess Habits can do with it.

### Maia: Aligning superhuman AI with human behavior (McIlroy-Young, Sen, Kleinberg, Anderson, KDD 2020)

- **Finding:** A Leela-style network trained on human games at one rating predicts what players at that rating actually play much better than Stockfish or Leela do. A separate network predicts whether a human will blunder in a given position.
- **Dataset:** Lichess games with no bullet games and no moves made with under 30 s left. Nine 100-point rating bins from 1100 to 1900, about 12M games per bin. Blunder task: 182M blunders and 272M non-blunders from games with Lichess evaluations ([paper](https://ar5iv.labs.arxiv.org/html/2006.01855)).
- **Effect size:** Move matching: Maia 50.8% to 52.9% at its own bin, Stockfish 33% to 41%, Leela at most 46%. Blunder (a loss of at least 10 win-probability points) prediction, board only / board plus metadata: residual CNN 67.7% / 71.7%. On frequently seen positions ("will more than 10% of players blunder here?"): 76.9%.
- **For Chess Habits:** The basis for "peer baseline" metrics. Its weakness for us is that it stops at 1900, which is too low for our target users, so use Maia-2 or Maia-3 instead.

### Maia-2: A unified model for human-AI alignment in chess (Tang, Jiao, McIlroy-Young, Kleinberg, Sen, Anderson, NeurIPS 2024)

- **Finding:** One model, conditioned on the skill of both players through skill-aware attention, replaces the separate Maia models. It is also "coherent": in 27% of positions the probability of the correct move rises steadily with skill, against about 1% for Maia-1.
- **Dataset:** Lichess rapid games from 2013 to 2023, about 169M games and 9.1B positions. Skill buckets run from below 1000 up to "above 2000" ([paper](https://arxiv.org/html/2409.20553v2), [proceedings](https://proceedings.neurips.cc/paper_files/paper/2024/hash/250190819ff1dda47cd23cecc0c5a69b-Abstract.html)).
- **Effect size:** Top-1 accuracy 53.25% on average (Skilled 51.7%, Advanced 54.2%, Master 53.9%), against 51.4% for Maia 1500. Perplexity 4.07 bits against 4.67 bits.
- **Output:** `inference_each(model, prepared, fen, elo_self, elo_oppo)` returns move probabilities and a White expected score. The README warns that this score is "not a calibrated win probability". MIT licence, `pip install maia2`, rapid and blitz checkpoints ([repo](https://github.com/CSSLab/maia2)).
- **For Chess Habits:** Usable today in Python inside the insights service. Its main limitation is the single bucket above 2000, so it cannot tell 2000 from 2400 apart.

### Maia-3 / Chessformer (Monroe, Eilender, Chalmers, Tang, Anderson, ICLR 2026)

- **Finding:** An encoder-only transformer that treats board squares as tokens. Maia-3 predicts human moves conditioned on both ratings and the last 8 positions.
- **Dataset:** Lichess blitz games from January 2023 to July 2025. Ratings 600 to 2600 ([paper](https://arxiv.org/abs/2605.19091), [launch post](https://hn.jakechampion.name/reader/https://lichess.org/@/ashtonanderson/blog/introducing-maia-3-free-and-open-source/vCPPRtX3)).
- **Effect size:** 57.1% move matching for the 79M-parameter model, 55.4% for 5M and 56.6% for 23M, against 52.0% for Maia-2 on the same (Allie) test set.
- **Licence and outputs:** The code is under **AGPL-3.0**. It runs as a UCI engine (`maia3-5m`) with `SelfElo`/`OppoElo` options and outputs MultiPV likely human moves plus win/draw/loss from a value head. It has no clock input ([repo](https://github.com/CSSLab/maia3)). The weights are on Hugging Face ([UofTCSSLab/Maia3-5M](https://huggingface.co/UofTCSSLab/Maia3-5M)).
- **Product overlap:** maiachess.com uses it to label single-game mistakes as "natural" or "surprising" for your level and to show "position danger", for Lichess games only. It does not aggregate across a player's games (launch post, above).
- **For Chess Habits:** This is the best peer model for 2000 to 2600 players. AGPL obligations apply if we serve it from our backend. That is fine if Chess Habits is open source; otherwise it needs a decision (see open questions). We need to check rating calibration from chess.com to Lichess blitz.

### Learning models of individual behavior in chess (McIlroy-Young, Wang, Sen, Kleinberg, Anderson, KDD 2022)

- **Finding:** Fine-tuning Maia on one player's games predicts that player's moves better than any rating-level model.
- **Dataset:** 400 Lichess players, mostly rated 1100 to 1900 (median about 1740), most with more than 20,000 games ([paper v3](https://arxiv.org/html/2008.10086v3)).
- **Effect size:** +4.19 percentage points on average (SE 0.10) over the best-matching Maia. Fine-tuning is *worse* than the base model with 1,000 games and only helps from about 5,000 games (Table 2).
- **For Chess Habits:** Not practical at this data requirement. The authors also did not release individual models, because stylometry would de-anonymise players ([repo](https://github.com/CSSLab/maia-individual)).

### Maia4All: Learning to imitate with less (Tang, Jiao, McIlroy-Young, Kleinberg, Sen, Anderson, TMLR 2026)

- **Finding:** Individual embeddings started from rating-level "prototypes" can model a player from **20 games** instead of 5,000.
- **Effect size:** Accuracy rises from 51.4% to 53.2% in the 20-game setting ([preprint](https://www.cs.toronto.edu/~ashton/pubs/maia4all-preprint2025.pdf), [arXiv](https://arxiv.org/abs/2507.21488), [TMLR listing](https://mlanthology.org/tmlr/2026/tang2026tmlr-learning)).
- **For Chess Habits:** A "your personal model" becomes realistic. We could find positions where *your* model expects you to go wrong while the rating model does not, which are personal habits. It is not MVP work, and I could not confirm that code was released.

### Behavioral stylometry (McIlroy-Young, Wang, Sen, Kleinberg, Anderson, NeurIPS 2021) and player-specific style (Sogliuzzo et al. 2026)

- **Finding:** A transformer embedding identifies a player among thousands from 100 games with 98% accuracy. It was trained on Lichess blitz players rated 1100 to 2000 and also works on grandmaster games ([paper](https://papers.nips.cc/paper_files/paper/2021/file/ccf8111910291ba472b385e9c5f59099-Paper.pdf)). In the KDD 2022 paper, stylometry from moves after ply 30 alone reaches 55% with 100 games, so style is visible well beyond opening choice ([v3](https://arxiv.org/html/2008.10086v3)). Sogliuzzo, Rautureau and Piette (May 2026) adapt Maia-2 with player embeddings for 16 world champions and compare styles with Jensen-Shannon divergence ([arXiv](https://arxiv.org/abs/2605.11893)).
- **For Chess Habits:** Proves that style is stable and measurable. A "style fingerprint" alone is not actionable, so I recommend dropping it as a feature. It is useful as a privacy warning: stored move data identifies people.

### Allie: Human-aligned chess with a bit of search (Zhang, Jacob, Lai, Fried, Ippolito, ICLR 2025)

- **Finding:** A model trained on human games including non-move behaviour (time spent, resignations) "ponders" in critical positions. Time-adaptive MCTS, with search effort set by predicted human thinking time, gives human-like strength.
- **Effect size:** Against players rated 1000 to 2600, the average skill gap was 49 Elo ([paper](https://arxiv.org/pdf/2410.03893), [code](https://github.com/ippolito-cmu/allie)).
- **For Chess Habits:** A possible source for "how long would a peer think here?", which would give a peer baseline for time use. This is for the clock researcher. Not MVP.

### Assessing human error against a benchmark of perfection (Anderson, Kleinberg, Mullainathan, KDD 2016 / TKDD 2017)

- **Finding:** Position difficulty is the strongest predictor of error. Difficulty is measured as blunder potential β = (number of moves that lose game-theoretic value) / (number of legal moves). There are also "skill-anomalous" positions where stronger players blunder more often.
- **Dataset:** About 200M FICS games and 1M grandmaster games, restricted to 6-piece tablebase positions ([paper](https://ar5iv.labs.arxiv.org/html/1606.04956)).
- **Effect size:** Balanced blunder prediction: β alone 0.73, rating alone 0.55, time alone 0.53, all features 0.75. In FICS, a +0.2 change in β raises the blunder rate more than 600 rating points lower it. The blunder rate jumps when less than about 10 s remain and is flat above that. Extra time helps higher-rated players more.
- **For Chess Habits:** The strongest argument for difficulty-adjusted metrics, and for comparing a player with peers in the *same* positions. "Your accuracy is 88%" without adjustment is mostly noise about which positions you got.

### Intrinsic chess ratings (Regan & Haworth, AAAI 2011) and human vs computer preferences (Regan, Biswas, Zhou, 2014)

- **Finding (2011):** A player's move choices are modelled with two parameters. Sensitivity *s* is the ability to tell apart moves that are only slightly worse. Consistency *c* is how reliably large errors are avoided. The model is p_i ∝ exp(−(δ_i/s)^c), where δ_i is the scaled eval gap to the best move. The fitted parameters map onto Elo, which gives an "intrinsic performance rating" from move quality instead of results ([paper](https://www.cse.buffalo.edu//~regan/papers/pdf/ReHa11c.pdf)).
- **Effect size (2011, 2006 to 2009 data, games with both players within 10 points of each 100-point Elo level, Rybka 3 depth 13):**

  | Elo | s | c | engine-match % | avg scaled error (pawns) |
  |---|---|---|---|---|
  | 2000 | .139 | .454 | 46.9 | .110 |
  | 2200 | .123 | .490 | 49.4 | .089 |
  | 2400 | .098 | .483 | 52.3 | .072 |
  | 2700 | .078 | .503 | 56.2 | .056 |

  The gain from 2000 to 2400 shows up mainly as sensitivity: *s* falls from .139 to .098, while *c* barely changes.
- **Error scaling:** Human error grows with the size of the advantage on either side. The authors flatten this by scaling eval differences with the differential 1/(1+|x|), which integrates to ln(1+|x|). The side that is worse makes larger raw errors.
- **Finding (2014):** At any eval, the human to move scores 2% to 3% worse than when the opponent is to move. Engines show no such effect. Humans also steer towards positions with fewer reasonable options. Data: 726,120 analysed moves from 10,317 games ([abstract](https://researchconnect.buffalo.edu/en/publications/human-and-computer-preferences-at-chess/), [PDF](https://cdn.aaai.org/ocs/ws/ws1274/8859-38007-1-PB.pdf)).
- **For Chess Habits:** (a) Use win-probability loss or eval-scaled loss, never raw centipawn loss, or "you blunder when winning" becomes an artefact. (b) The s/c split is a real two-number profile: "you miss small edges" vs "you make occasional big errors". This can be computed by context (phase, clock, eval state).

### Computer analysis of world champions and position complexity (Guid & Bratko, ICGA 2006; ICGA 2011)

- **Finding:** Average error compared with an engine (MeanLoss = Σ|eval(best) − eval(played)| / moves) ranks players, but only fairly once you account for how complex their positions were. The complexity measure is based on how much the engine's best move and evaluation change across search depths 2 to 12. Error rates rose with complexity ([ChessBase summary](https://en.chessbase.com/post/computers-choose-who-was-the-strongest-player-), [ICGA abstract](https://content.iospress.com/articles/icga-journal/icg29203), [follow-up](https://en.chessbase.com/post/using-che-engines-to-estimate-human-skill)). *I could not retrieve the exact complexity formula from the primary source. Verify it before implementing.*
- **For Chess Habits:** A cheap, engine-only difficulty proxy (best-move instability across depths) for use when Maia is not available. Later work found that difficulty for *humans* is better predicted with human models; see the next entry.

### Predicting chess puzzle difficulty (IEEE BigData Cup 2024; FedCSIS 2025 Challenge)

- **Finding:** Competitions predicting the Glicko-2 rating of Lichess puzzles from the position alone. Top entries combine Maia/Maia-2 success probabilities with Leela and Stockfish features. The 2025 edition supplied 22 precomputed Maia success probabilities per puzzle ([overview and team papers, FedCSIS 2025](https://annals-csis.org/Volume_43/drp/pdf/6771.pdf), [another entry](https://annals-csis.org/Volume_43/drp/pdf/7603.pdf)).
- **Dataset:** About 4.55M Lichess puzzles.
- **Effect size:** I did not retrieve the winning RMSE. *Check the overview paper.*
- **For Chess Habits:** Confirms that "the probability that a player at rating r finds the best move" (P_maia(best | pos, r)) is the state-of-the-art feature for human difficulty. It is also the key ingredient of the pressure analysis.

### Engine-equal, human-unequal (Park, arXiv, July 2026)

- **Finding:** Among 1,661 opening positions that Stockfish 18 rates within 10 cp of equal, human results differ from what ratings predict, and the difference repeats position by position across separate groups of accounts. The side that does worse thinks longer.
- **Dataset:** Lichess, October 2025, 16.1M occurrences, with an out-of-sample month eight months later ([arXiv](https://arxiv.org/abs/2607.25655)).
- **Effect size:** Typical skew is small: median |δ| ≈ 0.018 (about 2 percentage points of score). Replication slope 0.69 (95% CI 0.65 to 0.74), and 0.94 for the best-measured positions. Single-author preprint, not peer reviewed.
- **For Chess Habits:** "Equal" is not equal for humans. This supports measuring the practical difficulty a player's choices create.

### Response time distributions in rapid chess (Sigman, Etchemendy, Slezak, Cecchi, Frontiers in Neuroscience 2010)

- **Finding:** Thinking times are long-tailed and correlated from move to move. Stronger players move faster in the opening and endgame and spend more time on the middlegame. In time trouble, seconds become worth material.
- **Dataset:** FICS 3+0 games, more than 2.8M games and 200M moves. Players below 1400 compared with players above 1900. Crafty at 16 ply ([paper](https://www.frontiersin.org/articles/10.3389/fnins.2010.00060/full)).
- **Effect size:** By move 40, stronger players had used 77.9% of their clock and weaker players 74.7% (p < 10⁻⁸). Weaker players made their first blunder (score drop greater than 2) before move 17 on average, stronger players around move 40. Under time trouble, about 8 s is worth roughly a minor piece (the paper is inconsistent: the caption says a rook).
- **For Chess Habits:** A time-allocation profile by phase. Lichess Insights already shows move time by phase, so this is an input, not a feature on its own. Clock researcher.

### Time spent thinking reflects the value of computation (Russek, Acosta-Kane, van Opheusden, Mattar, Griffiths, Cognitive Science 2025)

- **Finding:** Players spend more time where thinking is worth more. Value of thinking: ΔU_C = U(best move at depth 16) − U(depth-1 Stockfish move), with U = depth-15 win probability. The expected version E[ΔU_C] fits better. The link gets stronger with Elo and with longer time controls.
- **Dataset:** Lichess 2019, 12.49M games, 519M moves, plies 15 to 75, 11 time controls ([paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC12553403)).
- **Effect size:** The slope of move time on ΔU_C ranges from 1.76 to 38.7 s per unit across time controls. Move time is concave in ΔU_C (√ΔU_C fits better). The expertise interaction is "modest" but robust (all p < 1e-50). Companion paper: [Kuperwajs & Russek, CogSci 2025](https://escholarship.org/uc/item/75b4m9c2).
- **For Chess Habits:** An exact, published formula for "time vs how critical the position was" (vision candidate). For each player, regress move time on √E[ΔU_C] and compare the slope with peers at the same rating and time control. Clock researcher's area.

### A check for rational inattention (Howard, MPRA working paper 2021)

- **Finding:** Strong players balance the marginal benefit of thinking (better moves) against its marginal cost (less time later) across time controls. Weak players under-adjust when short of time. Lichess's low-time beep pushes players to move faster and improves their time allocation, even though it slightly increases mistake size.
- **Dataset:** Millions of Lichess moves with Stockfish evals, using the time control as an instrument ([paper](https://mpra.ub.uni-muenchen.de/108243/)).
- **Effect size:** One extra second on a move is worth about 0.03 pawns (IV, 3+0 vs 5+0). In 15-second chess, the lowest-rated fifth of players use 0.55 s per move against 0.38 s for the top fifth (+44%). In 5-minute chess the gap is 11.2 s against 10.0 s (+12%).
- **For Chess Habits:** "Overthinking under low time" is a skill gap even at higher ratings. This gives a clock-researcher metric: compare the marginal value of the player's time with peers'.

### Speed, quality and the optimal timing of complex decisions (Sunde, Zegners, Strittmatter, 2022)

- **Finding:** Among professionals, faster moves go with better moves, which fits a drift-diffusion account: hard decisions take longer *and* go wrong more often ([arXiv](https://arxiv.org/abs/2201.10808)).
- **For Chess Habits:** A warning against naive "you think too long" claims. Long thinks mark hard positions, so time effects must be estimated *within* difficulty bands.

### Time pressure and strategic risk-taking (Carow & Witzig, JEBO 2025; working paper 2024)

- **Finding:** Under time pressure, professionals choose lower-risk moves. After a mistake, or when worse, they take more risk (correlational "strategic loss aversion"). Move risk is the variance, over the opponent's 5 best engine replies (within 300 cp), of a CNN-predicted human difficulty (the expected cp loss a proficient human would make in that position). The CNN was trained on 2M games.
- **Dataset:** FIDE World Cups 2013 to 2023, using the tiebreak structure as a source of outside variation in thinking time ([paper](https://download.uni-mainz.de/RePEc/pdf/Discussion_Paper_2404.pdf), [listing](https://ideas.repec.org/p/jgu/wpaper/2404.html)).
- **Effect size:** Statistically robust but small. One minute less on the clock lowers the risk measure (the variance of difficulty) by 0.12%. With the alternative eval-based risk measure the drop is 0.23% to 0.29% (IV estimates). The average change per move is about 0.2% of a standard deviation in classical games.
- **For Chess Habits:** A move-level definition of "risk" and of "difficulty you hand the opponent", used in [practical-pressure.md](practical-pressure.md).

### Do mistakes provoke new mistakes? (Adhikari, Anatolyev, Dagaev, IEEE Transactions on Games 2023)

- **Finding:** Small inaccuracies are followed by less accurate play. The effect of larger mistakes is weaker, and serious blunders are followed by *more* careful play.
- **Dataset:** 885 Tata Steel games, 2011 to 2020, Stockfish evals, ordered probit ([author page](https://pages.nes.ru/sanatoly/Papers/TiltChess.htm)).
- **For Chess Habits:** A within-game "error cascade" metric: P(error on move t+1..t+5 | inaccuracy at t) minus the player's baseline. It may differ for amateurs and online play. Psychology researcher's area.

### How men and women respond to failure (Engel, job-market paper)

- **Finding:** After a loss in a weekly titled-player tournament series, men play less accurately, choose riskier openings, and quit more often. Women hold or improve their level ([paper page](https://sites.google.com/view/julia-f-engel/job-market-paper)).
- **Dataset:** 286,140 games, 3,523 titled players, with player, round and tournament fixed effects. Effect sizes are only in figures, and the paper is unpublished.
- **For Chess Habits:** Supports a post-loss check for each player (accuracy and opening risk in the game after a loss, against the same player's baseline). Psychology researcher's area.

### Quantifying human performance in chess (Chowdhary, Iacopini, Battiston, Scientific Reports 2023)

- **Finding:** Hot streaks and cold streaks exist after controlling for skill. Cold streaks are longer, and weaker players have longer hot streaks. Players narrow their opening repertoire over their career but often fail to identify their most successful openings.
- **Dataset:** Lichess, 123M games, 0.98M players ([paper](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9902564/)).
- **For Chess Habits:** "You don't know your best openings" is an existing finding. chess.com Insights already shows opening results, so the gap is narrow.

### Cognitive performance in remote work (Künn, Seel, Zegners, Economic Journal 2022)

- **Finding:** The same professionals made larger errors (engine-measured) online than over the board during COVID, and the gap shrank over time ([RePEc](https://econpapers.repec.org/RePEc:oup:econjl:v:132:y:2022:i:643:p:1218-1232.)).
- **For Chess Habits:** The setting affects quality. This supports context analyses (where and when you play), which belong to the psychology researcher.

### Speed and fast processes: Burns 2004; van Harreveld et al. 2007; Moxley et al. 2012; Chassy et al. 2023

- **Burns 2004 (Psychological Science):** Up to 81% of variance in rating is accounted for by blitz performance, that is, play with less than 5% of normal time. Pattern recognition carries much of skill ([APS](https://www.psychologicalscience.org/journals/psychological-science/j.0956-7976.2004.00699.x/)).
- **van Harreveld, Wagenmakers, van der Maas 2007:** Slow processes (search) matter at least as much for strong players as for weak ones ([Springer](https://link.springer.com/article/10.1007/s00426-006-0076-0)).
- **Moxley, Ericsson, Charness, Krampe 2012 (Cognition):** Extra deliberation improves move quality for experts and less skilled players alike. Skill explained 7.8% of variance in first-move quality and 15.2% in final-move quality ([record](https://vivo.weill.cornell.edu/display/pubid22541584), figures as cited by [Chassy et al. 2023](https://pmc.ncbi.nlm.nih.gov/articles/PMC10497664/)).
- **Chassy, Lahaye, Didierjean, Gobet 2023 (Psychological Research):** 63 players rated 2106 to 2691 evaluated positions after 5 s. Elo explained 44% of variance in evaluation error (η² = .425 for skill group). Complex positions were judged worse. Response time did not differ by skill ([paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC10497664/)).
- **For Chess Habits:** For 1800 to 2400 players, both quick judgement and calculation matter. An analysis that splits "quick-move quality" from "long-think quality" (compared with peers, at matched difficulty) can tell a player which one is weaker. That belongs to the clock researcher; this literature backs it.

### Chunking and templates (Chase & Simon 1973; Gobet & Simon 1996)

- **Finding:** Experts store tens of thousands of chunks, roughly 10,000 to 100,000 (the usual estimate is about 50,000). Chunks encode specific spatial patterns, which mirror-image experiments confirm. With random positions, the masters' recall advantage shrinks to a small effect ([Gobet & Simon 1996, Memory & Cognition](https://www.Gwern.net/doc/psychology/chess/1996-gobet.pdf), [Brunel repository](https://bura.brunel.ac.uk/bitstream/2438/815/1/FullText.pdf)). Master chunks can reach up to about 17 pieces ([Gobet papers via BURA](https://bura.brunel.ac.uk/bitstream/2438/822/4/1791.pdf)).
- **For Chess Habits:** Skill is partly bound to familiar patterns. This predicts lower decision quality in unfamiliar structures, which we can test for each player.

### Specialization effect and Einstellung (Bilalić, McLeod, Gobet 2008, 2009; Sheridan & Reingold 2013)

- **Specialization (Cognitive Science 2009):** Experts recall and solve better in positions from their own opening specialty, by about one standard deviation of skill. That is enough to outweigh general expertise. On familiar problems they search deeper and narrower, and outside their specialty broader and shallower ([PubMed](https://pubmed.ncbi.nlm.nih.gov/21585497/), [Oxford record](https://ora.ox.ac.uk/objects/uuid:9728b751-1b0c-4279-8fe6-45a48284a37d)).
- **Einstellung (Cognition 2008):** Once a familiar solution comes to mind, experts keep looking at features related to it while claiming to search for better ones. This reduces them to the level of much weaker players ([Bilalić et al. PDF](https://cognition.aau.at/download/Publikationen/Bilalic/Bilalic_etal_2008b.pdf)). Experts avoid the familiar move when it is a blunder, but not when it is merely suboptimal ([Sheridan & Reingold 2013](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3790829/)).
- **For Chess Habits:** (a) The [structure-familiarity](structure-familiarity.md) analysis. (b) A gaze hypothesis: "fixation stays on the first candidate's region" as an Einstellung signal, for the gaze researcher. (c) Pattern-matched "almost right" moves are a stronger player's typical error. Maia-3's "natural for your level" label partly captures this.

### Deliberate practice (Charness et al. 2005; Gobet & Campitelli 2007; Hambrick et al. 2014; Burgoyne et al. 2019)

- **Finding:** Hours of serious *solo* study predict current and peak rating better than tournament play or formal lessons ([Charness et al. 2005](https://zendy.io/title/10.1002/acp.1106)). In a reanalysis, serious chess activity, formal instruction and starting age explain 63% of variance in peak rating ([Burgoyne et al. 2019](https://englelab.gatech.edu/articles/2019/Burgoyne_et_al_2019_AJP.pdf)). Practice is necessary but not sufficient. An average of about 11,000 hours to reach 2200 is reported by the authors in a popular summary ([Gobet & Campitelli 2007](https://bura.brunel.ac.uk/handle/2438/611), [ChessBase](https://en.chessbase.com/post/handedne-practice-and-talent-in-che)). Deliberate practice explains about 34% of reliable variance in chess skill ([Hambrick et al. 2014, summary](https://www.bps.org.uk/research-digest/exploding-10000-hours-myth-its-no-guarantee-greatness)).
- **For Chess Habits:** Training suggestions should be targeted solo study with feedback (drills from the player's own critical positions, model games in unfamiliar structures), not more games. Training-loop researcher's area.

### Expertise increases planning depth (van Opheusden et al., Nature 2023)

- **Finding:** In four-in-a-row, a heuristic-search model fitted to choices, response times and eye movements shows that planning depth rises with expertise, in lab data and in large-scale mobile data ([paper](https://www.cns.nyu.edu/malab/static/files/publications/2023_Opheusden,Kuperwajs,Galbiati,BnayaLi,Ma.pdf)).
- **For Chess Habits:** Not chess, but it shows that planning depth can be inferred from behaviour. Speculation: a chess version could estimate the depth at which a player's move choices stop matching the engine. Research only.

## Analyses this enables

Vision test: "Could chess.com Game Review, chess.com Insights, Lichess Insights, Aimchess or maiachess.com already tell you this?" chess.com Insights covers accuracy by phase and move number, results by opponent rating, game-end types, opening results and "book moves before leaving book", found/missed forks, pins and mates, hanging pieces, piece accuracy, and calendar ([support article](https://support.chess.com/en/articles/8708925-what-is-insights-on-chess-com)). Aimchess scores tactics, endgame, advantage capitalization, resourcefulness, time management and openings ([aimchess.com](https://aimchess.com)).

| Analysis | Literature basis | Passes vision test? | Owner / note | Verdict |
|---|---|---|---|---|
| **Difficulty-adjusted excess loss**: your win% loss minus the expected loss of peers in the same position, E_r[loss] = Σ_m P_maia(m \| pos, r) · loss(m), aggregated by context | Anderson 2017; Maia-2/3; puzzle-difficulty challenges | Yes in aggregate. Per-game, maiachess.com already labels natural vs surprising mistakes | Core metric for most other analyses. Engines+Maia researcher | Later (needs Maia + engine). Make it the common currency |
| **Practical pressure balance**: difficulty you hand the opponent vs difficulty you face, in equal positions | Park 2026; Regan 2014; Carow & Witzig 2025; Maia | Yes. No tool measures it | [practical-pressure.md](practical-pressure.md) | Later |
| **Structure familiarity**: score and move quality in pawn structures by how often you have reached them before | Bilalić 2009; Gobet & Simon 1996; chunking | Yes. chess.com shows results per opening, not per own-structure familiarity | [structure-familiarity.md](structure-familiarity.md) | MVP (results-only version) |
| **Repertoire exit** (exact positions): time and quality after leaving your own known positions | Same | Yes | Clock researcher, [clock-opening-speed.md](clock-opening-speed.md) | (theirs) |
| **Sensitivity vs consistency profile** (Regan s, c) by context | Regan & Haworth 2011 | Mostly. Aimchess gives category scores, not this split | Could live inside excess loss (small-gap misses vs big errors) | Later |
| **Context-conditioned human-likelihood rating**: the rating r that maximises Π P_maia(played move \| pos, r) in a given situation | Regan IPR; Maia-2/3 | Partly. chess.com gives a per-game estimated rating, Aimchess gives category scores | Engines+Maia researcher | Later |
| **Time vs value of computation**: slope of move time on √E[ΔU_C], compared with peers | Russek 2025; Howard 2021; Sunde 2022 | Yes | Clock researcher | Later (engine-heavy) |
| **Quick-move vs long-think quality** at matched difficulty | Burns 2004; Moxley 2012; van Harreveld 2007 | Yes | Clock researcher | Later |
| **Error cascade** within a game | Adhikari 2023 | Yes | Psychology researcher | Later |
| **Post-loss quality and opening risk** | Engel; Chowdhary 2023 | Yes (Insights has calendar data, not this) | Psychology researcher | Later |
| **Personal model blind spots** (Maia4All embedding vs rating model) | KDD 2022; Maia4All 2026 | Yes | Research spike only | Later |
| **Style fingerprint** (stylometry) | NeurIPS 2021 | Yes, but not actionable | | Drop |
| **Skill-anomalous positions** | Anderson 2017 | Yes, but rare and not actionable for one player | | Drop |
| **Raw time-by-phase profile** | Sigman 2010 | No (Lichess Insights) | Input only | Drop as a feature |

Methodological rules that follow from the literature:

1. Measure error as **win-probability loss** (Lichess: Win% = 50 + 50·(2/(1+e^(−0.00368208·cp)) − 1), [lichess.org/page/accuracy](https://lichess.org/page/accuracy)) or eval-scaled loss (Regan's ln(1+|x|)), never raw centipawns.
2. **Adjust for difficulty** before comparing contexts, because difficulty dominates.
3. **Time effects only within difficulty bands** (Sunde 2022), and exclude moves made with very little time left when estimating skill (Maia used a 30 s cut-off).
4. **Peer baseline = same rating and same time control.** Maia-2/3 are trained on Lichess rapid/blitz and have no bullet or clock input. chess.com ratings must be mapped to Lichess ratings first.
5. **Opponents in the same games are a free control group.** They are near the player's rating and play the same positions.

## Open questions

- How should chess.com ratings (rapid 2380, blitz 2389, bullet 1900) be mapped to Lichess-blitz Elo for Maia-3 conditioning? Is the error from a wrong mapping large for players near 2400?
- Maia-3 is AGPL-3.0. Will the Chess Habits repo be open source, which makes serving it fine, or do we use Maia-2 (MIT) and accept the single bucket above 2000?
- Does Maia-3 (5M) run in the browser through ONNX/WASM fast enough for about 10k positions? This is not documented; it needs a spike.
- Guid & Bratko's exact complexity formula and the FedCSIS 2025 winning RMSE were not verified in primary sources.

## Sources

- Anderson, Kleinberg, Mullainathan. Assessing Human Error Against a Benchmark of Perfection. KDD 2016 / TKDD 2017. https://ar5iv.labs.arxiv.org/html/1606.04956
- McIlroy-Young et al. Aligning Superhuman AI with Human Behavior: Chess as a Model System. KDD 2020. https://arxiv.org/abs/2006.01855 , https://ar5iv.labs.arxiv.org/html/2006.01855
- Tang et al. Maia-2. NeurIPS 2024. https://arxiv.org/html/2409.20553v2 , https://proceedings.neurips.cc/paper_files/paper/2024/hash/250190819ff1dda47cd23cecc0c5a69b-Abstract.html , https://github.com/CSSLab/maia2
- Monroe et al. Chessformer: A Unified Architecture for Chess Modeling (Maia-3). ICLR 2026. https://arxiv.org/abs/2605.19091 , https://github.com/CSSLab/maia3 , https://huggingface.co/UofTCSSLab/Maia3-5M
- Anderson. Introducing Maia-3: free and open source (Lichess blog, May 2026). https://lichess.org/@/ashtonanderson/blog/introducing-maia-3-free-and-open-source/vCPPRtX3 (read via https://hn.jakechampion.name/reader/https://lichess.org/@/ashtonanderson/blog/introducing-maia-3-free-and-open-source/vCPPRtX3)
- MaiaChess platform v1 (Blunder Meter). https://www.maiachess.com/blog/platform-v1
- McIlroy-Young et al. Learning Models of Individual Behavior in Chess. KDD 2022. https://arxiv.org/html/2008.10086v3 , https://github.com/CSSLab/maia-individual
- Tang et al. Learning to Imitate with Less (Maia4All). TMLR 2026. https://arxiv.org/abs/2507.21488 , https://www.cs.toronto.edu/~ashton/pubs/maia4all-preprint2025.pdf , https://mlanthology.org/tmlr/2026/tang2026tmlr-learning
- McIlroy-Young et al. Detecting Individual Decision-Making Style: Exploring Behavioral Stylometry in Chess. NeurIPS 2021. https://papers.nips.cc/paper_files/paper/2021/file/ccf8111910291ba472b385e9c5f59099-Paper.pdf
- Sogliuzzo, Rautureau, Piette. Toward Modeling Player-Specific Chess Behaviors. arXiv 2026. https://arxiv.org/abs/2605.11893
- Zhang et al. Human-aligned Chess with a Bit of Search (Allie). ICLR 2025. https://arxiv.org/pdf/2410.03893 , https://github.com/ippolito-cmu/allie
- Regan, Haworth. Intrinsic Chess Ratings. AAAI 2011. https://www.cse.buffalo.edu//~regan/papers/pdf/ReHa11c.pdf , https://ojs.aaai.org/index.php/AAAI/article/view/7951
- Regan, Biswas, Zhou. Human and Computer Preferences at Chess. MPREF@AAAI 2014. https://cdn.aaai.org/ocs/ws/ws1274/8859-38007-1-PB.pdf , https://researchconnect.buffalo.edu/en/publications/human-and-computer-preferences-at-chess/
- Guid, Bratko. Computer Analysis of World Chess Champions. ICGA Journal 2006. https://content.iospress.com/articles/icga-journal/icg29203 , https://en.chessbase.com/post/computers-choose-who-was-the-strongest-player- , https://en.chessbase.com/post/using-che-engines-to-estimate-human-skill
- FedCSIS 2025 Challenge papers (puzzle difficulty). https://annals-csis.org/Volume_43/drp/pdf/6771.pdf , https://annals-csis.org/Volume_43/drp/pdf/7603.pdf , https://annals-csis.org/Volume_43/drp/4532.html
- Park. Engine-Equal, Human-Unequal. arXiv 2026. https://arxiv.org/abs/2607.25655
- Sigman, Etchemendy, Slezak, Cecchi. Response time distributions in rapid chess. Frontiers in Neuroscience 2010. https://www.frontiersin.org/articles/10.3389/fnins.2010.00060/full
- Russek et al. Time Spent Thinking in Online Chess Reflects the Value of Computation. Cognitive Science 2025. https://pmc.ncbi.nlm.nih.gov/articles/PMC12553403
- Kuperwajs, Russek. Exploring resource-rational planning under time pressure in online chess. CogSci 2025. https://escholarship.org/uc/item/75b4m9c2
- Howard. A Check for Rational Inattention. MPRA 108243, 2021. https://mpra.ub.uni-muenchen.de/108243/
- Sunde, Zegners, Strittmatter. Speed, Quality, and the Optimal Timing of Complex Decisions. 2022. https://arxiv.org/abs/2201.10808
- Carow, Witzig. Time Pressure and Strategic Risk-Taking in Professional Chess. JGU WP 2404 (2024); JEBO 2025. https://download.uni-mainz.de/RePEc/pdf/Discussion_Paper_2404.pdf , https://ideas.repec.org/p/jgu/wpaper/2404.html
- Adhikari, Anatolyev, Dagaev. Do Mistakes Provoke New Mistakes? Evidence from Chess. IEEE Transactions on Games 2023. https://pages.nes.ru/sanatoly/Papers/TiltChess.htm
- Engel. How Men and Women Respond to Failure: Evidence from Chess Tournaments. Working paper. https://sites.google.com/view/julia-f-engel/job-market-paper
- Chowdhary, Iacopini, Battiston. Quantifying human performance in chess. Scientific Reports 2023. https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9902564/
- Künn, Seel, Zegners. Cognitive Performance in Remote Work: Evidence from Professional Chess. Economic Journal 2022. https://econpapers.repec.org/RePEc:oup:econjl:v:132:y:2022:i:643:p:1218-1232.
- Burns. The effects of speed on skilled chess performance. Psychological Science 2004. https://www.psychologicalscience.org/journals/psychological-science/j.0956-7976.2004.00699.x/
- van Harreveld, Wagenmakers, van der Maas. The effects of time pressure on chess skill. Psychological Research 2007. https://link.springer.com/article/10.1007/s00426-006-0076-0
- Moxley, Ericsson, Charness, Krampe. The role of intuition and deliberative thinking in experts' superior tactical decision-making. Cognition 2012. https://vivo.weill.cornell.edu/display/pubid22541584
- Chassy, Lahaye, Didierjean, Gobet. Intuition in chess: a study with world-class players. Psychological Research 2023. https://pmc.ncbi.nlm.nih.gov/articles/PMC10497664/
- Gobet, Simon. Recall of random and distorted chess positions. Memory & Cognition 1996. https://www.Gwern.net/doc/psychology/chess/1996-gobet.pdf ; Templates in chess memory (Cognitive Psychology 1996) via https://bura.brunel.ac.uk/bitstream/2438/815/1/FullText.pdf
- Bilalić, McLeod, Gobet. Specialization effect and its influence on memory and problem solving in expert chess players. Cognitive Science 2009. https://pubmed.ncbi.nlm.nih.gov/21585497/ , https://ora.ox.ac.uk/objects/uuid:9728b751-1b0c-4279-8fe6-45a48284a37d
- Bilalić, McLeod, Gobet. Why good thoughts block better ones. Cognition 2008. https://cognition.aau.at/download/Publikationen/Bilalic/Bilalic_etal_2008b.pdf
- Sheridan, Reingold. The Mechanisms and Boundary Conditions of the Einstellung Effect in Chess. PLoS ONE 2013. https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3790829/
- Charness, Tuffiash, Krampe, Reingold, Vasyukova. The role of deliberate practice in chess expertise. Applied Cognitive Psychology 2005. https://zendy.io/title/10.1002/acp.1106
- Burgoyne et al. The impact of domain-specific experience on chess skill. American Journal of Psychology 2019. https://englelab.gatech.edu/articles/2019/Burgoyne_et_al_2019_AJP.pdf
- Gobet, Campitelli. The role of domain-specific practice, handedness, and starting age in chess. Developmental Psychology 2007. https://bura.brunel.ac.uk/handle/2438/611 , https://en.chessbase.com/post/handedne-practice-and-talent-in-che
- Hambrick et al. Deliberate practice: Is that all it takes to become an expert? Intelligence 2014 (summary). https://www.bps.org.uk/research-digest/exploding-10000-hours-myth-its-no-guarantee-greatness
- van Opheusden et al. Expertise increases planning depth in human gameplay. Nature 2023. https://www.cns.nyu.edu/malab/static/files/publications/2023_Opheusden,Kuperwajs,Galbiati,BnayaLi,Ma.pdf
- chess.com Insights (feature list). https://support.chess.com/en/articles/8708925-what-is-insights-on-chess-com
- Aimchess (feature list). https://aimchess.com
- Lichess accuracy formula. https://lichess.org/page/accuracy
