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
| Idea approval and Azure access requested from the professor (12 Nov) | | Done (18 Nov): resource group `rg-sdd-3a-g3` and managed identity `sdd-3a-g3-github` |
| Product Backlog with acceptance criteria (GitHub issues, board in Projects) | | Partly done: issues #17–#21 with acceptance criteria and the `sprint-2` label; the [board](https://github.com/users/javocruz/projects/1) followed on 20 Nov (#21) |
| Branch protection on `main` (1 approval, CI green, also for admins) | | Done (14 Nov) |
| Roles per sprint and who owns what ([team.md](team.md)) | #15 | Done (merged 14 Nov) |
| Grandmaster comparison (pulled forward from Sprint 2) | #16 | Done (merged 14 Nov) |
| First deployment to Azure | | Not done → Sprint 2: access arrived on 18 Nov; pipeline sign-in through OIDC in #23 |

**Sprint Goal: partly met.** A player can import their chess.com games and see findings end to
end (locally with `docker compose`, checked by the CI smoke test), but nothing is deployed to
Azure yet: access to the group's resource group arrived on the last day of the sprint.

## Retrospective

**What went well**

- The whole MVP is merged: 16 PRs, CI green on `main` after every merge, branch protection on.
- The analyses come from research and experiments on real games, not guesses.
- The stacked PRs were merged in order without conflicts, waiting for CI on `main` between merges.

**What did not go well**

- Almost all of the code came from one person before the team had split the work.
- Some PRs were very large (up to ~5,600 lines), too big to review properly.
- Azure access arrived on 18 Nov, so the deploy half of the Sprint Goal was missed.
- The Product Backlog board was not set up.

**Agreements for Sprint 2**

- Every member owns at least one backlog item ([team.md](team.md)) and opens their own PR for it.
- One issue per PR, kept small enough to review, approved by another member before merging.
- The first deployment by the pipeline comes first; everything else builds on it.
