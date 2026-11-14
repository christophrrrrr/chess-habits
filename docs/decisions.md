# Decision records

Each record: context, decision, alternatives considered, consequences.

## 1. Split into a `games` and an `insights` service

**Context.** The assignment requires exactly two backend services, each with its own database,
talking over HTTP. Kiebitz has two very different kinds of work: getting and storing games
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

**Decision.** `deploy.yml` reuses `ci.yml`, pushes `ghcr.io/<owner>/kiebitz-<service>:<sha>`,
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
compares the mean residual of a group of games (e.g. right after a loss) with the rest and
reports the difference with a 95% confidence interval and a label; below 30 games per group it
makes no claim. chess.com reports **post-game** ratings (verified on real data), so pre-game
ratings are reconstructed, and the player's strength is smoothed (median of ±25 games) to avoid
regression-to-the-mean artifacts.

**Alternatives.** Win rates per bucket (biased by opponent strength); Bayesian models (better,
but harder to explain and test in this sprint).

**Consequences.** Findings are comparable across time controls and honest about noise. With
many analyses × time controls some "medium" findings will be chance (multiple comparisons);
the research notes propose stricter thresholds for later sprints.
