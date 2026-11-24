# Decision records

Each record: context, decision, alternatives considered, consequences.

## 1. Split into a `games` and an `insights` service

**Context.** The assignment requires exactly two backend services, each with its own database,
talking over HTTP. Chess Habits has two very different kinds of work: getting and storing games
(stable, append-only, depends on chess.com), and analysing them (changes constantly as research
adds analyses, recomputable from the games).

**Decision.** `games` owns tracked accounts (the CRUD entity) and imported games. `insights`
owns analysis runs and findings, and reads games from `games` over HTTP.

**Alternatives.** *Players + analysis* (analysis service also imports): mixes the external
dependency with the fast-changing part. *Split by platform* (chess.com / Lichess): duplicates
logic, no real independence.

**Consequences.** Analyses can be added, rerun or thrown away without touching imported data.
Partial failure is natural: without `insights`, import and browsing still work; without
`games`, stored findings still show. Cost: `insights` pulls all games over HTTP per run
(paged, 500 per page), which is fine for thousands of games but will need incremental runs later.

## 2. Azure SQL serverless with SQLAlchemy, Alembic and pymssql

**Context.** Required: Azure SQL serverless per service (auto-pause), SQL Server in compose
locally, schema through versioned migrations applied on startup.

**Decision.** SQLAlchemy 2 ORM with Alembic migrations, run by each service at startup
(`alembic upgrade head`) after a retry loop that waits up to 2 minutes for the database to
resume from auto-pause. Driver: `pymssql` (self-contained wheels; no ODBC driver in the image).
Tests run the same migrations against SQLite.

**Alternatives.** `pyodbc` + Microsoft ODBC driver: official, but needs apt repositories and a
bigger image. Raw SQL migration files: simpler but no dialect portability for tests.

**Consequences.** Small images, migrations tested on every CI run. SQLite and SQL Server
differ in edge cases, so the compose smoke test in CI also runs everything against real SQL
Server. Max 1 replica means no concurrent migration runs.

## 3. Import month by month, driven by the UI

**Context.** A strong player has thousands of games across dozens of monthly chess.com
archives. No background workers, queues or always-on compute are allowed, and Container Apps
cut long HTTP requests.

**Decision.** `POST /players/{id}/imports {month}` imports one archive. The UI loops over
the months and shows progress. Fully imported past months are never fetched again (they never
change on chess.com); the current month can be re-imported without duplicates.

**Alternatives.** One long request for the whole history (timeouts); a background job (not
allowed, no always-on compute).

**Consequences.** Every request stays short (about 1–4 s per month) and chess.com is called
serially, as it asks. Closing the tab stops the import; the next import resumes where it ended.

## 4. Deployment: GHCR images tagged by SHA, health-gated, Bicep

**Context.** Merges to `main` must deploy automatically only after CI, with migrations and a
health check; config only through environment variables and secrets.

**Decision.** `deploy.yml` reuses `ci.yml`, pushes `ghcr.io/<owner>/chess-habits-<service>:<sha>`,
updates both Container Apps, and waits until the latest revision is ready and `/health` is 200
(fails after 5 minutes); then builds the UI with the live URLs and uploads it to Static Web
Apps, followed by a live smoke test. Infrastructure is Bicep (`infra/main.bicep`), deployed by
a manual workflow. Azure steps are gated by the `AZURE_ENABLED` variable.

**Alternatives.** Azure CLI setup script (less reproducible); Terraform (state storage would be
an extra resource).

**Consequences.** Every running image maps to one commit; rollback = redeploy an older SHA.
`main` stays green before the Azure credentials exist.

## 5. Monitoring through structured stdout logs

**Context.** Request logs must be queryable in Log Analytics, with a dashboard and an SLO; no
extra Azure services.

**Decision.** Each service writes exactly one JSON line per request to stdout
(`service, method, path, status, duration_ms`; never bodies). Container Apps ships stdout to the
environment's Log Analytics workspace, where saved KQL queries build the dashboard and the SLO
([monitoring.md](monitoring.md)).

**Alternatives.** Application Insights / OpenTelemetry exporter: an extra Azure resource.

**Consequences.** No SDK, no extra cost; queries parse the JSON with `parse_json`.

## 6. Findings measured against expectation, with uncertainty

**Context.** Vision principle: *only show what you can back up*. Raw win rates mislead (they
depend on opponents), and small samples produce confident-looking noise.

**Decision.** Every game gets a residual: actual score minus the Elo-expected score. A finding
compares a group of games (e.g. right after a loss) with another and reports the difference
with a 95% cluster-bootstrap interval (sessions or games), the minimum detectable effect, and
a label after Benjamini-Hochberg correction over the whole page; below 100 games (results) or
30 events (behaviour) it makes no claim. Definitions: [definitions.md](definitions.md). chess.com reports **post-game** ratings (verified on real data), so pre-game
ratings are reconstructed, and the player's strength is smoothed (median of ±25 games) to avoid
regression-to-the-mean artifacts.

**Alternatives.** Win rates per bucket (biased by opponent strength); Bayesian models (better,
but harder to explain and test in this sprint).

**Consequences.** Findings are comparable across time controls and honest about noise; "no clear
effect" always comes with the size that could have been detected. Research E2 measured the
false-finding rate on shuffled data, which is why q = 0.05 (not 0.10) is the finding threshold.

## 7. A grandmaster is a tracked player with `kind = reference`

**Context.** Sprint 2 adds "put your habits next to a grandmaster's". The assignment allows
exactly two services and two databases.

**Decision.** A grandmaster is an ordinary row in `players` with `kind = reference` (migration
0003), imported through the same month-by-month import and analysed by the same analyses. The UI
imports only the last 12 months of a reference player (a top player has about 500 games a month;
a year gives thousands of games per time control). The insights service compares the two latest
runs (`GET /players/{id}/compare/{reference_id}`) from stored findings, with intervals and a
Benjamini-Hochberg pass over the comparison table. The cluster bootstrap now resamples in chunks,
so a run over thousands of games stays small in memory.

**Alternatives.** A separate grandmaster table or service (more code, breaks the two-service
limit); precomputed grandmaster profiles shipped with the app (stale, and not the player's choice).

**Consequences.** No new infrastructure; any chess.com account can be a reference. A reference
player shows up in its own section on the home page and has its own habit page.

## 8. Eye tracking prototype: MediaPipe in the browser, coarse regions only

**Context.** The vision's long-term goal is gaze habits (where you look while you think). The
course leaves no time for the research the gaze notes ask for, but a working prototype shows the
idea and tests the pipeline. Webcam tracking is only accurate to about 1-3 squares
(docs/research/gaze-tracking.md), and video of a player's face must not leave their device.

**Decision.** An opt-in page (`#/gaze`) runs MediaPipe Face Landmarker (Apache-2.0,
`@mediapipe/tasks-vision` pinned, loaded only on that page) in the browser. Our own code maps iris
position and head pose to the screen with a ridge regression from a 9-point calibration, checks
accuracy on 4 more points, and records gaze while the player solves three fixed positions. Results
are shown per 2x2 block of squares (opponent's half, king zones, first region looked at) and are
never stored or sent. The page is labelled a prototype and makes no claim about the player.

**Alternatives.** WebGazer.js (GPLv3, which would put the whole UI under the GPL); WebEyeTrack
(MIT, newer, no stable npm release we could pin); a gaze service in the backend (video would leave
the device, and a third service breaks the assignment's two-service limit).

**Consequences.** No backend change and no new Azure resource. The library's WASM and the face
model are fetched from jsDelivr and Google's model storage when the page opens. Linking gaze to
mistakes needs the research in docs/research/gaze-*.md first (after the course).

## 9. Stockfish runs in the player's browser; results are stored by insights

**Context.** Critical moments, resignation quality and the opening autopilot need the moves and an
engine. About 40 positions per game at 100,000 nodes (MultiPV 2) cost ~15 s per game; a few hundred
games is too much CPU for a scale-to-zero Container App with 0.5 vCPU, a long request would time
out, and the assignment allows no queue or third container.

**Decision.** The UI runs the deep analysis in the player's browser (`ui/src/deep/`): chess.js
(BSD-2) replays each PGN, and Stockfish 19 lite single-threaded (stockfish.js 19.0.1, GPL-3.0,
1.8 MB WASM, served from `ui/public/engine/` with its licence and a link to the exact source) runs
in a Web Worker, spoken to only through UCI text. Compact per-move rows are uploaded to the insights
service (`PUT /players/{id}/game-analyses`, table `game_analyses`, migration 0004) and used by the
normal analysis run. Uploads go game by game, so the run can stop and continue. Method and
thresholds follow docs/research/game-decision-points.md and engines-and-human-baseline.md.

**Alternatives.** Stockfish in the insights container (CPU cost on Azure credit, timeouts, the full
build is 99 MB); Lichess cloud evaluations (rate limits, few hits after the opening); python-chess on
the server for the positions (GPL-3.0 inside our published images).

**Consequences.** No new Azure service and no extra cloud cost; the analysis uses the player's CPU
and needs the tab open. Labels from a 100k-node search can flip near the thresholds (research: 47
of 50 critical labels held at 1M nodes), so cards show counts and intervals and never single-move
verdicts. Only the most recent N games get the engine pass; positions and final evaluations cover
all games.
