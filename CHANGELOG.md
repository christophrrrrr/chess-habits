# Changelog

All notable changes to Chess Habits are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html): one minor version per sprint while
the project is below 1.0. How releases are cut: [docs/deployment.md](docs/deployment.md#releases).

## [Unreleased]

## [0.2.0] - 2026-11-28

Sprints 2 and 3, released together. Chess Habits is live on Azure, deployed by the pipeline
on every merge to `main`: https://polite-mud-0c720f303.6.azurestaticapps.net

### Added

- **Your plan**: a page that ranks every habit with clear evidence by its cost in Elo over an
  average game, with one concrete action each and rules that can be adopted there (#36).
- Charts on every card (plain SVG, with a table view under each chart) and five new clock-only
  habits: first game of a session, time of day, opening time, premoves and form (#36).
- **Deep analysis in the browser**: Stockfish 19 (WebAssembly) runs on the player's own
  computer and uploads compact results to the insights service (migration 0004), which adds
  three cards: **critical moments**, **how your games end** and **opening autopilot** (#47).
- **Where you look**: an opt-in eye-tracking prototype that runs entirely in the browser
  (MediaPipe Face Landmarker, own calibration), with heatmaps on puzzles and on the player's
  own missed positions (#37, #47).
- Methods page (`#/methods`) with every definition and threshold in plain words, linked from
  every card through "How is this measured?" (#29).
- Monitoring dashboard as an Azure Workbook deployed from Bicep: requests, 5xx error rate,
  p50/p95 latency and the SLO with its error budget (#22), a panel for deep-analysis uploads
  (#51), and screenshots of the deployed Workbook in `docs/monitoring.md` (#35).
- Security scans in CI: Bandit for both services and CodeQL for Python and TypeScript, with
  `docs/security.md` (#25), and a security review of the deep-analysis upload (#50).
- Browser tests with Playwright, run in CI against `docker compose`: the main story, a
  service-down message (#32) and the Your plan page with adopting a rule (#52).
- Bicep build and lint as a CI job on every pull request (#22).
- `CHANGELOG.md`, the `v0.1.0` release and the release scheme in the deployment guide (#20).
- Sprint 1 retrospective, Sprint 2 notes (#26) and the Sprint Review demo script (#27).
- README: the live URL (#33) and screenshots, including Your plan and the critical moments
  card (#20, #45).

### Changed

- The Deploy and Infrastructure workflows sign in to Azure through OpenID Connect as the
  group's managed identity instead of a service principal secret; the deployment guide
  describes IE's subscription and the one-time setup (#23), with the exact OIDC subject
  GitHub sends (#31).
- CI audits npm dependencies in two steps: shipped code fails on high-severity advisories,
  build and test tools only on critical ones (#23).
- The insights service accepts `PUT` and `PATCH` through CORS (#47).
- `AI_USAGE.md` is merged with `merge=union`, so rows added in parallel pull requests no longer
  conflict (#34).

### Fixed

- The deploy smoke test failed on a renamed analysis although the system was up; it now
  checks that `/analyses` returns a valid, non-empty list (#31, #34).
- Uploading the same game twice in one deep-analysis request returned a 500; the second copy
  now updates the first (#50).
- Generated files (`ui/dist/`, `ui/playwright-report/`) are no longer committed (#32).

## [0.1.0] - 2026-11-14

End of Sprint 1. The first complete version of the product, built and run locally and in CI;
not yet deployed to Azure.

### Added

- Games service: tracked chess.com accounts (CRUD) and a month-by-month import of their full
  game history, with its own database and migrations (#1).
- Insights service: analysis runs and findings with confidence intervals against an
  Elo-expected baseline, with its own database and migrations (#2).
- UI (React, Vite): accounts, import with progress and findings per time control (#3).
- `docker compose` for the whole system and a compose smoke test in CI (#4).
- Azure infrastructure in Bicep and the deploy pipeline: images in GitHub Container Registry,
  Container Apps, serverless Azure SQL, Static Web Apps and a live smoke test (#5).
- Architecture decision records, data model, monitoring and SLO queries, Definition of Done
  and sprint notes (#6).
- Research sweep: 37 notes on what Chess Habits can analyse that no other tool does, with a
  gap map, a shortlist and three experiments on real chess.com data (#8).
- Clock profile and after-loss cards, the statistics layer behind them (cluster bootstrap,
  minimum detectable effect, Benjamini-Hochberg correction) and `docs/definitions.md` (#9).
- Rules with adherence tracking: adopt a clock checkpoint or a stop-loss rule from a
  suggestion and see whether it is kept more often than before (#10).
- Roadmap to the deadline and after the course (#11).
- Tile-based UI: one tile per finding, a page per finding with hash routes, account tiles on
  the home page (#14).
- Team and roles per sprint, and who owns which backlog item (#15).
- Grandmaster comparison: import a grandmaster's last 12 months of games and compare habits
  per time control, with 95% intervals and a verdict for every difference (#16).

### Changed

- Project renamed from Kiebitz to Chess Habits across code, images, compose, CI/CD,
  infrastructure and docs (#12).
- Sharper vision: the habits strong players have but cannot explain, aimed at club players
  and up (#13).

### Fixed

- Scale-to-zero cold starts were reported as outages: the UI now waits up to 90 s and shows a
  "servers are waking up" banner after 4 s, and the insights service waits up to 60 s for the
  games service (configurable through `GAMES_SERVICE_TIMEOUT_SECONDS`) (#7).

[Unreleased]: https://github.com/christophrrrrr/chess-habits/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/christophrrrrr/chess-habits/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/christophrrrrr/chess-habits/releases/tag/v0.1.0
