# Premove patterns in bullet

**Question:** How often do you premove, in which situations, what do your premoves cost you, and where do you lose time by *not* premoving obvious moves?

**What to measure:** chess.com live bullet (1+0, 2+1) and 3+0 blitz scrambles. Chess.com charges a premove exactly 0.1 s ([chess.com help](https://support.chess.com/en/articles/8562432-what-are-pre-moves-and-how-do-they-work)), so in a no-increment game:

- **Premove candidate** = own move with `t_k = 0.1 s` exactly (computed as in [clock-and-time.md](clock-and-time.md)); with increment, `t_k = 0.1` after adding the increment back. Lichess premoves are free (0 s), so this detector is chess.com-specific; a Lichess version would use `t_k ≤ 0.02 s` with its 0.01 s precision under 10 s (to verify).
- Detector check on real data: in the owner's October 2026 1+0 games, 2,734 of 26,626 own and opponent move times are exactly 0.1 s vs. 736 at 0.2 s and 696 at 0.3 s. The spike is the premove signal. A rough **premove share** estimate is `(n_0.1 - n_0.2) / N` ≈ 7-8%; the raw 0.1 s share (10.1% of the owner's own 2026 1+0 moves) is an upper bound because a few fast manual moves also land on 0.1 s.

Metrics:

1. **Premove share** by clock band (`c` ≥ 25%, 10-25%, < 10%) and by phase. Healthy pattern (hypothesis): low early, high in the scramble.
2. **Premove cost**: share of premoves after which the player is down ≥ 2 points of material two plies later and does not regain it within the next 2 plies (engine-free proxy); with engine, premoves with `ΔW ≥ 20`. Compare with the player's non-premove moves *at the same clock band*: premoves are expected to be worse, the question is by how much.
3. **Missed premoves**: forced moves and simple recaptures (see easy-move classes in [clock-long-thinks.md](clock-long-thinks.md)) played with `t_k ≥ 0.5 s` while `c < 10%`. Seconds lost per game this way.
4. **Scramble throughput**: own moves per second while the clock is under 10 s, and the premove share within that, in flag wins vs. flag losses (links to [clock-flag-losses.md](clock-flag-losses.md)).

Per time control: **bullet** main; **blitz** only in scrambles (`c < 10%`); not useful in rapid/classical (owner: only 3.6% of 10+0 move times are exactly 0.1 s) or Daily.

**Data needed:** chess.com `[%clk]` (0.1 s resolution), moves, a move-replay library for material and legal-move checks. Optional engine.

**Reliability:**
- The detector is indirect (no premove flag in the PGN); lag can make a premove cost more than 0.1 s (forum reports, not official), which hides some premoves.
- Very large samples in bullet (owner: ~24,000 own 1+0 moves in 2026), so rates are stable after ~100 games. Premove-cost events are rarer; ~300+ games for a useful CI.
- The material proxy misses premoves that lose by allowing mate or a decisive attack; the engine version fixes that.

**Effort:** S (clock + material rules). Belongs in the insights service; parsing already done for the MVP.

**Prior work:**
- Chessiro (2026) shows premove counts per game ([Chessiro](https://chessiro.com/blog/inside-chessiro-game-review)).
- Chess.com, Lichess Insights and Aimchess show nothing about premoves (Lichess Insights' smallest move-time bucket is "0 to 1 second", [InsightRange.scala](https://github.com/lichess-org/lila/blob/master/modules/insight/src/main/InsightRange.scala)).
- No tool found that measures premove cost or missed premoves across games.

**Why it's not engine review:** Game Review does not know which moves were premoves. This is pure behaviour (how you handle the scramble) and works without an engine.

**Training link:**
- High premove cost early in the game: restrict premoves to forced recaptures and moves that are safe against every reply.
- Many missed premoves in scrambles: drill premoving in won/lost endgames vs. a bot at 15 s, or specific recapture patterns.
- Measure: premove cost per 100 premoves and seconds lost to missed premoves per game, over the next 200 bullet games.

**Verdict:** **Later** (small, cheap add-on once clock parsing exists; first after the MVP if the player is a bullet-volume player like the owner, 70% of whose 2026 games were bullet).
