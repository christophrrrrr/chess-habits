# Sprint 1 (11–18 Nov 2026)

**Product Owner:** Christoph · **Scrum Master:** Javi · see [team.md](team.md)

**Sprint Goal:** The skeleton is deployed to Azure by the pipeline, and a player can import their
chess.com games and see a first set of findings end to end.

| Item | PR | Status |
|---|---|---|
| Games service: track accounts (CRUD), import chess.com games month by month | #1 | Done (merged 14 Nov) |
| Insights service: analysis runs, first findings (tilt, sessions, time trouble) with confidence intervals | #2 | Done (merged 14 Nov) |
| UI: accounts, import with progress, findings per time control | #3 | Done (merged 14 Nov) |
| `docker compose` for the whole system + CI smoke test | #4 | Done (merged 14 Nov) |
| Azure infrastructure (Bicep) and deploy pipeline | #5 | Done (merged 14 Nov) |
| Decision records, data model, monitoring/SLO queries, Scrum docs | #6 | Done (merged 14 Nov) |
| Research sweep: what can Chess Habits analyse that no tool does yet | #8 | Done (merged 14 Nov) |
| Handle scale-to-zero cold starts | #7 | Done (merged 14 Nov) |
| MVP analyses from the research: clock profile, after-loss cards, statistics layer, definitions | #9 | Done (merged 14 Nov) |
| Rule adoption with adherence tracking (clock checkpoint, stop-loss rule) | #10 | Done (merged 14 Nov) |
| Roadmap until the deadline and after the course | #11 | Done (merged 14 Nov) |
| Rename the project from Kiebitz to Chess Habits | #12 | Done (merged 14 Nov) |
| Sharper vision: the habits strong players have but cannot explain; audience club players and up | #13 | Done (merged 14 Nov) |
| Tile UI: one big tile per finding, a page per finding, account tiles | #14 | Done (merged 14 Nov) |
| Idea approval and Azure access requested from the professor (12 Nov) | | Waiting for an answer |
| Product Backlog with acceptance criteria (GitHub issues, board in Projects) | | In progress (Javi) |
| Branch protection on `main` (1 approval, CI green, also for admins) | | Done (14 Nov) |
| Roles per sprint and who owns what ([team.md](team.md)) | | In review |
| Grandmaster comparison (pulled forward from Sprint 2) | | In progress |
| First deployment to Azure | | Blocked: no access to the group's resource group and no service principal yet |

## Retrospective

_To fill in at the end of the sprint._
