# Changelog

All notable changes to Chess Habits are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html): one minor version per sprint while
the project is below 1.0. How releases are cut: [docs/deployment.md](docs/deployment.md#releases).

## [Unreleased]

### Added

- `CHANGELOG.md`, the `v0.1.0` release, the release scheme in the deployment guide and README
  screenshots of the main pages (#20).

### Changed

- The Deploy and Infrastructure workflows sign in to Azure through OpenID Connect as the
  group's managed identity instead of a service principal secret; the deployment guide
  describes IE's subscription and the one-time setup (#23).
- CI audits npm dependencies in two steps: shipped code fails on high-severity advisories,
  build and test tools only on critical ones (#23).

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

[Unreleased]: https://github.com/christophrrrrr/chess-habits/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/christophrrrrr/chess-habits/releases/tag/v0.1.0
