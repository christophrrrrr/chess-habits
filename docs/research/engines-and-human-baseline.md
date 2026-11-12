# Engines, human baseline and data pipeline

**Question:** Where do Chess Habits' engine evaluations and "human of rating R" probabilities come from, and how do we compute them inside the assignment's constraints (two scale-to-zero containers, Azure SQL serverless, static UI)?

**Status:** feasibility study, 2026-11-12. Measurements in this note were made on 2026-11-12 (see "How the benchmarks were run"). Companion note: [maia-human-baseline.md](maia-human-baseline.md).

**Short answer:** compute in the **browser**. Stockfish 19 (stockfish.js "lite single", 1.8 MB WASM) evaluates every position, and Maia-3 (5M parameters, ONNX via onnxruntime-web) gives human move probabilities. The browser uploads compact per-move results to the **insights** service. The containers run no engine. Lichess cloud eval is not worth it. The Lichess open database is used offline, once, to build population baseline tables. Maia-2 and Maia-1 are not usable for 1800+ players.

---

## Options

### (a) Stockfish WASM in the browser

| Package | Engine | Builds | Notes |
|---|---|---|---|
| [`stockfish` (nmrugg/stockfish.js)](https://github.com/nmrugg/stockfish.js) 19.0.1 (npm, published 2026-10-10) | Stockfish 19 (released [2026-09-05](https://stockfishchess.org/blog/2026/stockfish-19/)) | full multi-threaded and full single (~99 MB WASM each), **lite multi-threaded (1.7 MB)**, **lite single (1.8 MB)**, asm.js (3 MB, slow) | Multi-threaded builds need `SharedArrayBuffer`, so the page must send `Cross-Origin-Opener-Policy: same-origin` and `Cross-Origin-Embedder-Policy: require-corp`. Single-threaded builds need neither ([README](https://unpkg.com/stockfish@19.0.1/README.md)). Speaks UCI over `postMessage` in a Web Worker. This is the build chess.com contributes to. |
| [`@lichess-org/stockfish-web`](https://github.com/lichess-org/stockfish-web) 0.5.0 (2026-09-05) | `sf_19`, `sf_19_smallnet`, Fairy-Stockfish 14 | pthread builds; NNUE nets loaded separately | Made for lichess.org; its own README says it "is not straight-forward to load and use" and points to stockfish.js for simple use ([README](https://cdn.jsdelivr.net/npm/@lichess-org/stockfish-web@0.5.0/README.md)). |

- **MultiPV** is a standard UCI option and works in both (measured below: MultiPV 3 costs ~5x MultiPV 1 at the same depth).
- **Azure Static Web Apps** can serve the needed headers through `globalHeaders` and custom MIME types in `staticwebapp.config.json` ([docs](https://learn.microsoft.com/en-us/azure/static-web-apps/configuration)), so multi-threaded builds are possible. The single-threaded build avoids the issue: run several single-threaded engines in parallel Web Workers instead.
- **Static hosting limits (Free plan):** 250 MB per environment, 100 GB bandwidth per month, no overage on Free ([quotas](https://learn.microsoft.com/en-us/azure/static-web-apps/quotas)). The 99 MB full build would use 40% of the storage and ~100 MB of bandwidth per new visitor. The lite build (1.8 MB) does not have this problem.
- **Strength trade-off (primary data from the Maia platform):** in headless Chromium, single thread, 16 MB hash, 200 game positions, Stockfish 17 WASM at depth 12 took 0.07 s, agreed with depth 22 on the best move 71.5% of the time and was 2.2 win-% points off on average. At depth 18: 0.86 s, 86.5% agreement, 1.0 point off ([maia-platform-frontend LOADING.md](https://github.com/CSSLab/maia-platform-frontend/blob/main/LOADING.md), measured 2026-10/11).

### (b) Low-depth Stockfish inside a scale-to-zero Azure Container App

- **CPU/memory:** Consumption plan combinations go from 0.25 vCPU/0.5 GiB to 4 vCPU/8 GiB, but apps in a *Consumption-only* environment are limited to **2 vCPU / 4 GiB** ([docs](https://learn.microsoft.com/en-us/azure/container-apps/containers)). The assignment also caps each app at **max 1 replica**.
- **Request timeout:** HTTP ingress request timeout is **240 seconds** ([ingress docs](https://learn.microsoft.com/en-us/azure/container-apps/ingress-overview)). There is no queue and no third container, so a long analysis must be cut into client-driven chunks of under ~200 s each.
- **Cold start:** Microsoft gives no number ([cold-start guide](https://learn.microsoft.com/azure/container-apps/cold-start)); third-party measurements report 2-10 s for the first request ([lab write-up](https://yeongseon.github.io/azure-paas-troubleshooting-labs/container-apps/scale-to-zero-502/overview/)). The official Stockfish 19 Linux binary adds ~80 MB to the image (the Windows universal zip is 81 MB).
- **Price (West Europe, from the Azure Retail Prices API, queried 2026-11-12):** active vCPU $0.000034/s, memory $0.000004/GiB-s, requests $0.56 per million. Free grant per subscription and month: 180,000 vCPU-s, 360,000 GiB-s, 2 million requests ([billing docs](https://learn.microsoft.com/en-us/azure/container-apps/billing)). Scaled to zero costs nothing.
- **Practical problem:** a CPU-bound engine inside the insights service competes with its own `/health` and API requests on one replica. That conflicts with the assignment's monitoring and partial-failure requirements. It also serialises all users behind one engine.

### (c) Lichess cloud eval and Lichess exports

- **`GET /api/cloud-eval?fen=&multiPv=`** returns a cached evaluation or 404. The spec says "about 320 million positions", "Opening positions have more chances of being available" and "Use this endpoint to fetch a few positions here and there" ([OpenAPI spec](https://raw.githubusercontent.com/lichess-org/api/master/doc/specs/tags/analysis/api-cloud-eval.yaml)). The downloadable eval dump has 417,862,375 positions, updated 2026-11-11 ([database.lichess.org](https://database.lichess.org/)).
- **Rate limits:** not published per endpoint. "Only make one request at a time"; after a 429, "wait a full minute" ([API tips](https://lichess.org/page/api-tips)).
- **Measured coverage on real games (2026-11-12):** 12 of the owner's recent chess.com rapid/blitz games, every 2nd position up to ply 40, one request per second:

  | Plies | Found |
  |---|---|
  | 1-10 | 60/60 |
  | 11-20 | 36/60 |
  | 21-30 | 2/60 |
  | 31-40 | 0/59 |

  The last position found per game was ply 12-24 (median 16). A 77-ply rapid game is therefore ~15-20% covered, all of it in the opening. At one request per second, fetching the opening positions of 1,000 games takes hours, while computing them locally takes seconds. **Not worth it.**
- **Lichess game export** (`GET /api/games/user/{username}`, later phase): `evals=true`, `clocks=true`, `accuracy=true`, `perfType`, `since`, `max`; throttled to 20 games/s anonymous, 30 games/s with OAuth, 60 games/s for your own games ([spec](https://raw.githubusercontent.com/lichess-org/api/master/doc/specs/tags/games/api-games-user-username.yaml)). Evals exist only for games someone asked Lichess to analyse. Use them when present and compute the rest.
- **Lichess open database (population baselines):** CC0. October 2026: 95,395,628 standard rated games, 31 GB `.pgn.zst` (~7.1x larger uncompressed). "About 6% of the games include Stockfish analysis evaluations"; `%clk` clocks since April 2017; ratings are Glicko-2 ([database.lichess.org](https://database.lichess.org/)). Zstd files can be partly downloaded and still decompressed, so a slice of one month is enough. About 6% of 95M is ~5.7M evaluated games per month, which is ample for 100-point rating bands from 1800 to 2600.

### (d) Maia (human move model)

| Model | Licence | Ratings | Runs as | Fit for 1800+ |
|---|---|---|---|---|
| Maia-1 ([CSSLab/maia-chess](https://github.com/CSSLab/maia-chess)) | GPL-3.0 | 9 separate lc0 nets, 1100-1900 | lc0 weights | **No**: stops at 1900 |
| Maia-2 ([CSSLab/maia2](https://github.com/CSSLab/maia2), [paper](https://arxiv.org/abs/2409.20553)) | MIT | 11 bins: `<1100`, 100-point bins to 1999, `>=2000` ([utils.py](https://github.com/CSSLab/maia2/blob/main/maia2/utils.py)) | PyTorch (`pip install maia2`), weights from Google Drive; rapid and blitz models; 23.3M params; 53.25% top-1 | **No**: everyone above Lichess 2000 is in one bin |
| Maia-3 ([CSSLab/maia3](https://github.com/CSSLab/maia3), [paper](https://arxiv.org/abs/2605.19091), [announcement](https://lichess.org/@/ashtonanderson/blog/introducing-maia-3-free-and-open-source/vCPPRtX3), 2026-05-24) | **Code AGPL-3.0**; Hugging Face weights carry no licence tag ([Maia3-23M](https://huggingface.co/UofTCSSLab/Maia3-23M)) | **600-2600 Lichess blitz**, continuous (rating embeddings interpolated between anchors at 0 and 5000); conditions on own *and* opponent rating | PyTorch UCI engine; community ONNX exports ([bqrio/maia3-onnx](https://huggingface.co/bqrio/maia3-onnx)): 5M fp16 10.8 MB, 23M fp16 45.8 MB, 79M fp16 156 MB | **Yes**, the only option |

- **Maia-3 accuracy:** top-1 move match 55.4% (5M), 56.6% (23M), 57.1% (79M), against 52.0% for Maia-2 on the same test set ([paper](https://arxiv.org/html/2605.19091)).
- **Maia-3 training data:** Lichess **blitz** games, January 2023 to July 2025. Positions with under 30 s on the clock were dropped ([paper](https://arxiv.org/html/2605.19091)). It therefore does not model time-trouble play, and it models blitz rather than rapid or classical play.
- **ONNX interface** (the export matches the Maia platform's own analysis export): inputs `tokens` [batch, 64, 12] (piece one-hot, board mirrored when Black is to move), `elo_self` [batch], `elo_oppo` [batch] as raw ratings; outputs `logits_move` [batch, 4352] and `logits_value` [batch, 3] (loss/draw/win for the side to move) ([model card](https://huggingface.co/bqrio/maia3-onnx)). The tokens hold no castling or en-passant information.
- **Browser:** the official Maia platform already runs Maia-3 client-side with onnxruntime-web 1.23 (WASM, 4 threads). Its 23M fp16 model (45.7 MB) evaluates a batch of 10 ratings for one position in 0.63 s, and an 8-bit-weights copy (24.2 MB) in 0.59 s with 99.3% the same top move ([LOADING.md](https://github.com/CSSLab/maia-platform-frontend/blob/main/LOADING.md)). The platform frontend itself is GPL-3.0, so we must not copy its code.
- **Other clock-aware human models:** Otter (Aug 2026) conditions on clock and history, but uses the same 11 brackets topping out at ">=2000" ([arXiv 2608.05206](https://arxiv.org/abs/2608.05206)), so it has the same problem as Maia-2 for our users.
- **Rating scales differ.** Maia-3 uses Lichess blitz ratings. ChessGoals (updated July 2026, N = 1,935 players with Lichess blitz) maps chess.com blitz 1800/2000/2200/2400 to Lichess blitz 1950/2080/2210/2340 ([ChessGoals](https://chessgoals.com/rating-comparison/)). chess.com rapid 2215 is about chess.com blitz 2400 in the same table. The owner (chess.com blitz 2389) is about Lichess blitz 2330. His rapid 2380 is above the table's range.

### Game source: chess.com published-data API

- **Endpoints:** `/pub/player/{user}/games/archives` (list of months), `/pub/player/{user}/games/{YYYY}/{MM}` (JSON), `/pub/player/{user}/games/{YYYY}/{MM}/pgn` ([docs](https://www.chess.com/news/view/published-data-api)).
- **Rate limits:** "Serial access is unlimited. Parallel requests may trigger rate limiting" (429). Send a User-Agent with contact details. Commercial use is allowed if you do not "copy its features or IP" and state that you are not affiliated with chess.com ([support article](https://support.chess.com/en/articles/9650547-what-is-the-pubapi-and-how-do-i-use-it)). Responses carry `ETag`/`Last-Modified` for conditional requests (304), and gzip is supported. Endpoints officially refresh every 12-24 h, but on 2026-11-12 the current month came back with `cache-control: max-age=5` and a `Last-Modified` two minutes old (observation only). `Access-Control-Allow-Origin: *` was present, so browsers can call it directly.
- **Game JSON fields:** `url, pgn, time_control, end_time, rated, accuracies, tcn, uuid, initial_setup, fen, time_class, rules, white, black, eco`. There are **no engine evaluations**. `accuracies` appears only if someone already ran Game Review: 1,446 of the owner's 2,670 games.
- **Clock format:** every move carries `{[%clk 0:09:58.8]}`, the clock *after* the move, in 0.1 s steps. `TimeControl` is `"600"`, `"180+2"` or `"1/86400"` (daily). Time spent on a move = previous clock of the same side - this clock + increment. There is no lag-compensation data, so very short times in bullet are noisy.
- **Archive sizes (owner `chrisaxm`, measured 2026-11-12):** 41 monthly archives, 2,670 games (1,310 rapid, 846 bullet, 461 blitz, 53 daily), 9.5 MB JSON (3.6 KB per game), 2.1 MB gzip transfer, fetched serially in 8.1 s. Mean plies: rapid 76.9 (median 71), blitz 68.3, bullet 69.4, daily 34.5. Clocks were present in 100% of live games and 46/53 daily games. One busy month (Oct 2026) held 500 games and 1.7 MB.

---

## Benchmarks/estimates

### How the benchmarks were run

- Desktop Intel i7-9700F (8 cores, no SMT), Windows 11, Node 24.22.1, python-chess 1.11.2, onnxruntime 1.23.2 (Python, CPU).
- Positions were taken from the owner's latest chess.com rapid games, one engine per run, `ucinewgame` not sent between positions, 16 MB hash.
- **Caveat:** other processes held the CPU at 100% load during the runs. Treat absolute times as **pessimistic**; ratios between configurations are more trustworthy. A laptop without that load should be similar or faster per core.
- Scripts are not in the repo (they were scratch tools). The method can be repeated with python-chess `SimpleEngine.popen_uci(["node", "stockfish-19-lite-single.js"])`.

### Stockfish 19, per position, 1 thread

| Engine / build | Limit | Mean | p50 | p95 | kN/s | Positions |
|---|---|---|---|---|---|---|
| WASM lite single (1.8 MB) | depth 12 | **35-40 ms** | 19-23 ms | 109-114 ms | 475-550 | 232 / 366 |
| WASM lite single | depth 16 | **304 ms** | 254 ms | 715 ms | 508 | 366 |
| WASM lite single | depth 18 | 1,249 ms | 859 ms | 3,382 ms | 303 (heavier load) | 366 |
| WASM lite single | 100k nodes (reaches depth 16.2 on average) | **184 ms** | 193 ms | 272 ms | 543 | 232 |
| WASM lite single | depth 12, MultiPV 3 | 190 ms | 150 ms | 505 ms | 451 | 232 |
| WASM full single (99 MB) | depth 12 | 96 ms | 45 ms | 333 ms | 151 | 232 |
| WASM full single | 100k nodes | 549 ms | 501 ms | 1,078 ms | 182 | 232 |
| Native SF19 (official Windows build) | depth 12 | 27 ms | 16 ms | 82 ms | 540 | 232 |
| Native SF19 | depth 16 | 209 ms | 166 ms | 569 ms | 605 | 232 |
| Native SF19 | 100k nodes | 166 ms | 173 ms | 244 ms | 604 | 232 |
| Native SF19 | depth 12, MultiPV 3 | 125 ms | 113 ms | 279 ms | 618 | 232 |

Reading: with the same big net, WASM searches ~3.3x fewer nodes per second than native (182 vs 604 kN/s). The lite build closes that gap by using a small, weaker net: lite WASM searched about as many nodes per second as native big-net Stockfish (543 vs 604 kN/s). Per position, browser depth 12 costs about the same as native depth 12 on a server core.

### Maia-3 ONNX, per (position, rating) evaluation, CPU

| Model | 1 thread, batch 1 | 1 thread, batch 32 | 4 threads, batch 1 | 4 threads, batch 32 |
|---|---|---|---|---|
| 5M fp32 (21 MB) | 17.8 ms | 14.6 ms | 12.8 ms | **9.5 ms** |
| 23M fp32 (91 MB) | 58.7 ms | 46.3 ms | 35.2 ms | 21.1 ms |

The browser (onnxruntime-web WASM) is slower than native ONNX Runtime. The Maia platform's 23M fp16 needs ~63 ms per item with 4 threads (batch of 10 in 0.63 s, [LOADING.md](https://github.com/CSSLab/maia-platform-frontend/blob/main/LOADING.md)). By FLOPs, 5M should be ~3-4x faster in the browser, about 15-25 ms per item (**estimate**, not measured in a browser).

**Sanity check on real games (Maia-3 5M):** 600 positions where the owner was to move, both ratings set to R:

| R (Lichess) | mean P(played move) | top-1 match | mean -log2 P(played) |
|---|---|---|---|
| 1500 | 0.367 | 47.7% | 2.19 bits |
| 2000 | 0.413 | 51.0% | 2.01 bits |
| 2400 | 0.436 | 53.5% | 1.95 bits |
| 2600 | 0.438 | 54.2% | 1.95 bits |

The model explains the owner's moves better as R rises, then flattens between 2400 and 2600. Two consequences follow. The pipeline works end to end with real chess.com data. And Maia-3 resolves rating differences poorly near its top: "your moves look like an R-rated player" is weak at 2400+.

### Compute for 1,000 rapid games (~77 plies, i.e. ~77,000 positions; ~38,500 with the user to move)

Single-thread times are the measured means multiplied out. "4 workers" assumes 4 free cores and linear scaling (**estimate**).

| Option | What | Single thread | 4 browser workers | Azure cost |
|---|---|---|---|---|
| **A1** Browser, SF lite depth 12 | eval of every position | 77k x 37 ms = 48 min | **~12 min** | $0 |
| **A2** Browser, SF lite 100k nodes | better evals (~depth 16) | 77k x 184 ms = 3.9 h | ~1 h | $0 |
| **A3** Browser, MultiPV 2 at depth 12 on user's positions | "only move" / criticality gap | 38.5k x ~110 ms (between MPV1 and MPV3; estimate) = 1.2 h | ~18 min | $0 |
| **A4** Browser, Maia-3 5M, one evaluation per position | P(move \| own rating, opponent rating), human W/D/L | 77k x 15-25 ms = 19-32 min | runs alongside (ORT uses its own threads) | $0 |
| **A5** Browser, human difficulty (SF depth 10 on the top-3 Maia moves of user positions) | expected loss of a peer | 38.5k x 3 x ~25 ms (estimate) = 48 min | ~12 min | $0 |
| **B** ACA native SF, 100k nodes, 2 vCPU / 4 GiB | same as A2 server-side | 77k x 0.17 s = 13,000 vCPU-s | ~1.8 h wall on 2 vCPU | $0.44 vCPU + $0.10 memory = **~$0.55** (or free: the grant covers ~13 such batches a month) |
| **B'** ACA native SF depth 12 | same as A1 | 77k x 27 ms = 2,100 vCPU-s | ~17 min on 2 vCPU | ~$0.09 |
| **C** Lichess cloud eval | opening positions only | ~16 plies x 1,000 games, serial at ~1 req/s ≈ 4.4 h; 0% beyond ply ~25 | n/a | $0 |

Assumption for B: an Azure vCPU is about as fast as one loaded desktop core here (**speculation**; Azure vCPUs are usually hyperthreads).

**Incremental use is small.** A strong player adds roughly 50-500 games a month (the owner's busiest month had 500, mostly bullet). With A1 + A4, 50 new rapid games take about 40 s of engine time plus about 1-2 min of Maia time in the background.

**Database volume:** one row per ply at ~100-150 bytes is about 8-12 MB per 1,000 games. The Azure SQL free tier gives each database 100,000 vCore-seconds and 32 GB per month and auto-pauses after 15 minutes idle ([free tier docs](https://learn.microsoft.com/en-us/azure/azure-sql/database/free-offer)).

---

## Licences

| Component | Licence | What it means for Chess Habits |
|---|---|---|
| Stockfish / stockfish.js WASM | GPL-3.0 ([repo](https://github.com/nmrugg/stockfish.js); npm `Copying.txt`; the package's non-engine glue code is MIT) | Serving the `.wasm` to browsers is *conveying* object code. Ship the licence text and give the Corresponding Source next to it (GPLv3 §6(d): "equivalent access" from the same place, e.g. a link to the exact tag `v19.0.1` and the Stockfish `sf_19` source). Our UI talks to the engine only through UCI text messages in a separate Web Worker, which the [GPL FAQ](https://www.gnu.org/licenses/gpl-faq.en.html#MereAggregation) treats like pipes and sockets ("communication mechanisms normally used between two separate programs"). On that reading, Chess Habits' own code need not be GPL. Not legal advice. |
| Stockfish native in a container | GPL-3.0 | Running it on a server without distributing it creates no source obligation. Publishing the Docker image to GHCR (public) is distribution, so add the source link there too. |
| `@lichess-org/stockfish-web` | GPL-3.0 (repo licence) | Same as stockfish.js. |
| Maia-1 | GPL-3.0 | Not used. |
| Maia-2 | MIT | Unproblematic, but unusable for our rating range. |
| Maia-3 code | **AGPL-3.0** | §13: anyone interacting with a *modified* version over a network must be offered its source. If we use only the ONNX weights with our own preprocessing, Maia-3's code is not part of Chess Habits. |
| Maia-3 weights | **unclear**: no licence tag on Hugging Face; the announcement says the models are "completely free for you to download and use" | Ask CSSLab to confirm in writing before building a product on them. The ONNX conversion (`bqrio`) states AGPLv3 "inherited from the upstream". |
| maia-platform-frontend | GPL-3.0 | Read it for facts, do not copy code into Chess Habits. |
| Lichess open database | CC0 | Free for any use. |
| chess.com published data | API terms: commercial use allowed; do not copy chess.com features/IP; state non-affiliation | Shapes the product too: Chess Habits must not rebuild Game Review. |

**Simplest safe option (decision for the owner):** release Chess Habits under AGPL-3.0. GPLv3 §13 allows combining with AGPL code, so that covers Stockfish and Maia-3 whatever the weights turn out to be. Note: the repo is private as of 2026-11-12; if the UI serves Stockfish WASM, the GPL source offer applies to everyone who gets the page.

---

## Recommendation

### Architecture

```
chess.com PubAPI ──(serial, ETag)──> [games service]  ── Azure SQL #1: accounts, games, plies (SAN, clock, time spent)
                                          │ HTTP
Browser (static React on SWA)  ───────────┘
  ├─ Worker pool: N x stockfish-19-lite-single (N = min(4, cores-1)), 1.8 MB, no COOP/COEP needed
  ├─ Worker: Maia-3 5M (fp16 10.8 MB, or int8) via onnxruntime-web, model self-hosted on SWA
  └─ uploads per-ply results in batches ─────> [insights service] ── Azure SQL #2: evals, maia probs, findings,
                                                   (no engine)          population baselines (seeded by migration)
Offline, on a dev machine: Lichess open DB slice ──> baseline tables ──> migration file
```

1. **games service:** imports chess.com archives serially with `If-None-Match` and only re-fetches the current month. It stores PGN and per-ply clock / time spent. Nothing CPU-heavy.
2. **Browser analysis:** load a game list from games, then for each position:
   1. Ask insights for evals it already has, by FEN hash. This acts as an opening cache shared across the user's games and replaces Lichess cloud eval.
   2. Evaluate the rest with Stockfish lite at a fixed setting.
   3. Run Maia-3 with both players' ratings, converted to the Lichess blitz scale.
   4. POST compact rows to insights. Each row holds `fen_hash, eval_cp | mate (White POV), best_move, depth, nodes, engine_id`, plus `p_played, p_best_engine_move, entropy, top3 moves+probs, human_wdl, maia_id`.
3. **insights service:** stores the rows and computes findings in SQL/Python. It never searches positions, so it stays responsive and `/health` stays fast. Max 1 replica and the 240 s timeout do not matter.
4. **Version everything:** `engine_id` (e.g. `sf19-lite-d12`) and `maia_id`. Never mix settings inside one finding. Re-analysis is a browser job.
5. **Win% from centipawns:** use the Lichess formula `Win% = 50 + 50 * (2 / (1 + exp(-0.00368208 * cp)) - 1)` ([lichess accuracy page](https://lichess.org/page/accuracy)). Classify losses in win% rather than centipawns, so a 2-pawn swing in a won position counts less than in a balanced one.

### MVP slice (deadline 2026-11-24, one developer)

- Stockfish lite single at **depth 12, MultiPV 1** in 2-4 workers. The latest 50-100 rapid games take roughly 1-3 minutes. Store evals and expose one simple per-ply table. This is enough for any MVP finding that needs "was this move a mistake (win% drop ≥ X)".
- **Do not** put Maia, MultiPV or the population baselines into the MVP. Each is a separate later step.
- Do not put Stockfish in a container. It adds image size, CPU contention and the 240 s chunking problem for no gain.

### After the MVP

1. Raise quality to 100k nodes for positions the user is to move, or for flagged positions only (≈ 4x cost).
2. Add Maia-3 5M (see [maia-human-baseline.md](maia-human-baseline.md)) to compute P(move | R), human difficulty and peer-expected loss.
3. Add MultiPV 2 on the user's positions for the "only move" gap that criticality analyses need.
4. Build population baseline tables offline from the Lichess open database for 100-point bands from 1800 to 2600, by time control: error rate by phase, by clock bucket, and by Maia-difficulty bucket. Seed them through a migration.
5. Lichess import: use `[%eval]` when the game has it and compute the rest.

### Candidate analyses / pipeline options evaluated here

| Candidate | Exists elsewhere? | Novelty | Value 1800+ | Reliability | Effort | Verdict |
|---|---|---|---|---|---|---|
| Browser Stockfish pipeline (lite, depth 12) | Every review tool has engine evals; the value is in using them, not showing them | 1 | 5 (prerequisite) | 4 | S | **MVP** |
| Server-side Stockfish in insights container | n/a | 1 | 3 | 3 | M | drop (later only for users without a capable browser) |
| Lichess cloud eval as eval source | Lichess analysis board | 1 | 1 | 2 (opening only) | S | drop |
| Lichess `[%eval]` reuse on Lichess import | Lichess Insights uses it | 1 | 3 | 4 | S | later |
| Maia-2 / Maia-1 as human baseline | maiachess.com (older) | 2 | 1 (single top bin ≥2000) | 1 | M | drop |
| Maia-3 human baseline (P(move \| R)) | maiachess.com per position/game, not across games | 4 | 5 | 3 | M | later |
| Peer-expected loss vs actual loss across hundreds of games | maiachess.com shows per-game "natural vs surprising" mistakes only | 4 | 5 | 3 | L | later |
| Maia-implied rating per context (phase, clock, opening) | chess.com Game Review "game rating" per game | 3 | 2 (flat likelihood at 2400+) | 2 | M | later (low priority) |
| Population baseline tables from Lichess open DB | Lichess Insights (own games only), research papers | 3 | 4 | 4 | M | later |

---

## Open questions

- Maia-3 **weight licence**: AGPL like the code, or something else? Ask CSSLab before shipping.
- Maia-3 rating calibration for **chess.com rapid** players above ~2200: ChessGoals tables stop there, and the model's likelihood is flat from 2400 to 2600. A per-user calibration is needed (see the Maia note).
- Maia-3 ignores **time-trouble positions** (<30 s, dropped in training) and was trained on blitz. How wrong is it for bullet, rapid and classical? This needs a check on held-out games per time control.
- Browser timings for onnxruntime-web with the 5M model were estimated from FLOPs, not measured. Measure in Chrome and Firefox on a typical laptop.
- The benchmarks ran on a loaded machine. Re-run on an idle laptop before quoting numbers in the report.
- Azure price list shows a new "Environment Management Hour" meter ($0.10/h, effective 2026-11-01). The billing docs tie management charges to private endpoints, planned maintenance and Dedicated profiles. Confirm it does not apply to the group's Consumption-only environment.
- Client-computed evals can be faked. That only harms the user's own account, but it matters if Chess Habits ever shows cross-user comparisons.

---

## Sources

- Stockfish 19 release: https://stockfishchess.org/blog/2026/stockfish-19/
- stockfish.js 19.0.1 README: https://unpkg.com/stockfish@19.0.1/README.md ; repo https://github.com/nmrugg/stockfish.js
- lichess stockfish-web README (0.5.0): https://cdn.jsdelivr.net/npm/@lichess-org/stockfish-web@0.5.0/README.md ; repo https://github.com/lichess-org/stockfish-web
- Maia platform performance notes (Stockfish/Maia in browser, 2026-10/11): https://github.com/CSSLab/maia-platform-frontend/blob/main/LOADING.md
- Maia-3 code: https://github.com/CSSLab/maia3 ; paper (Chessformer, ICLR 2026): https://arxiv.org/abs/2605.19091 , https://arxiv.org/html/2605.19091 ; announcement: https://lichess.org/@/ashtonanderson/blog/introducing-maia-3-free-and-open-source/vCPPRtX3 ; weights: https://huggingface.co/collections/MaiaChess/maia3 , https://huggingface.co/UofTCSSLab/Maia3-5M ; ONNX export: https://huggingface.co/bqrio/maia3-onnx
- Maia-2: https://github.com/CSSLab/maia2 ; https://arxiv.org/abs/2409.20553 ; rating bins: https://github.com/CSSLab/maia2/blob/main/maia2/utils.py
- Maia-1: https://github.com/CSSLab/maia-chess
- Otter: https://arxiv.org/abs/2608.05206
- Lichess API: cloud eval spec https://raw.githubusercontent.com/lichess-org/api/master/doc/specs/tags/analysis/api-cloud-eval.yaml ; user games export spec https://raw.githubusercontent.com/lichess-org/api/master/doc/specs/tags/games/api-games-user-username.yaml ; API tips https://lichess.org/page/api-tips
- Lichess open database: https://database.lichess.org/
- Lichess accuracy / win% formula: https://lichess.org/page/accuracy
- chess.com published-data API: https://www.chess.com/news/view/published-data-api ; support article: https://support.chess.com/en/articles/9650547-what-is-the-pubapi-and-how-do-i-use-it
- ChessGoals rating comparison: https://chessgoals.com/rating-comparison/
- Azure Container Apps: containers https://learn.microsoft.com/en-us/azure/container-apps/containers ; billing https://learn.microsoft.com/en-us/azure/container-apps/billing ; ingress https://learn.microsoft.com/en-us/azure/container-apps/ingress-overview ; cold start https://learn.microsoft.com/azure/container-apps/cold-start ; prices: Azure Retail Prices API https://prices.azure.com/api/retail/prices (serviceName 'Azure Container Apps', westeurope) ; pricing page https://azure.microsoft.com/en-us/pricing/details/container-apps/
- Third-party cold-start measurement: https://yeongseon.github.io/azure-paas-troubleshooting-labs/container-apps/scale-to-zero-502/overview/
- Azure Static Web Apps: configuration https://learn.microsoft.com/en-us/azure/static-web-apps/configuration ; quotas https://learn.microsoft.com/en-us/azure/static-web-apps/quotas
- Azure SQL free tier: https://learn.microsoft.com/en-us/azure/azure-sql/database/free-offer
- GPL FAQ (aggregation): https://www.gnu.org/licenses/gpl-faq.en.html#MereAggregation ; AGPL-3.0: https://www.gnu.org/licenses/agpl-3.0.html
- Own measurements: chess.com archives of `chrisaxm`, Lichess cloud-eval coverage, Stockfish and Maia-3 benchmarks, all on 2026-11-12 (method above).
