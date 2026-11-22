# Roadmap

How Chess Habits gets from today's open PRs to the best possible submission on 24 Nov 2026, and
what comes after the course. Priorities follow the grading weights in
[assignment.md](assignment.md): a working, tested, self-deploying and monitored product beats
more features. Product ideas come from the research shortlist
(`docs/research/shortlist.md`, PR #8).

## Where we are (12 Nov)

| Grading area (weight) | State |
|---|---|
| Product, architecture, code (25%) | MVP complete in PRs #1–#10 (#12 renames the project): games service (players CRUD, chess.com import), insights service (clock profile, after-loss, stop-loss, rules with adherence), UI. Not merged yet. |
| Cloud infrastructure (15%) | Bicep for everything; access to IE's subscription granted (18 Nov), waiting for the pipeline's managed identity. |
| DevOps pipeline (20%) | CI (lint, format, tests with coverage gate, pip-audit, image builds, compose smoke test) and deploy workflow written; deploy never run. |
| Testing (10%) | 51 insights + 27 games + 29 UI tests, 96–98% coverage. No browser E2E yet. |
| Monitoring and reliability (10%) | JSON request logs, KQL queries and SLO written; no dashboard yet; partial failure handled and tested. |
| Scrum process (10%) | Definition of Done, sprint 0/1 notes. **Missing**: GitHub Projects backlog, branch protection, team roles. |
| Docs and review (10%) | README, 6 decision records, data model, definitions, AI usage log. |

## Until the deadline

### Now: needs no credentials (12–15 Nov)

1. ~~**Rule adoption with adherence**~~ (MVP item 4): done in #10.
2. **Dashboard as code**: an Azure Workbook in Bicep with request count, error rate, p95
   latency and the SLO, per service. The assignment allows a Workbook for the dashboard.
3. **Zero-downtime deploys**: Container Apps multiple-revision mode. The new revision gets 0%
   traffic, its `/health` is checked on the revision URL, then traffic switches over; an
   unhealthy revision is deactivated. A credited extra.
4. **Release scheme**: version tags on `main` (`v0.x.y`), images tagged with SHA and version,
   GitHub Releases with notes, and the `submission` tag. A credited extra.
5. **Browser E2E test**: Playwright against `docker compose` in CI with a seeded games
   database, so CI never depends on chess.com: add player → analyse → adopt a rule.
6. **Security scans**: CodeQL, `npm audit`, Bandit (recommended in the brief).
7. **Methods page** in the UI: every definition and threshold, linked from each card (D10).

### When the Azure credentials arrive

8. First deployment **by the pipeline** (the PR stack is reviewed and merged before, in order), check `/health`, logs
   in Log Analytics, run the SLO query and fix the KQL against real data.
9. Show partial failure in the cloud: stop the games app, insights findings stay readable.
10. Branch protection on `main` with one required approval.
11. Product Backlog in GitHub Projects from this roadmap (user stories with acceptance
    criteria). Needs `gh auth refresh -s project` once.

### Sprint 2 (19–24 Nov)

12. **Grandmaster comparison** (done 14 Nov, pulled forward into Sprint 1): pick a grandmaster, import their
    public chess.com games through the same import, and show their clock profile and after-loss
    habits next to yours, e.g. how Hikaru uses his clock compared with you. No new service or
    database: a grandmaster is just another tracked player. Time of day (D6) and opening
    autopilot cost move to after the course.
13. Docs: live URL and screenshots in the README, `sprint-2.md`, retrospectives, decision
    records for blue-green deploys and the release scheme, `AI_USAGE.md`.
14. Sprint Review prep: the demo story (import → clock card → adopt rule → rule card), a small
    PR ready to merge live, warm the services 5 minutes before (scale to zero), dashboard
    screenshots as a fallback, every member rehearses their part.
15. Tag `submission` on `main` before 24 Nov 23:59.

## Risks

| Risk | Mitigation |
|---|---|
| Azure credentials arrive late | Pipeline, Bicep and docs are ready; access to IE's subscription arrived 18 Nov; the managed identity for the pipeline is being created by the professor. Everything else is done first. |
| Few team members for PR approvals and role rotation | Clarify with the professor; record roles per sprint. |
| Cold start during the live demo | Warm-up request before the review; the UI explains slow first requests. |
| chess.com API down during the demo | Import before the review; findings are stored, so the demo does not need chess.com. |

## After the course

From the research shortlist, section 6:

- **Dec 2026 – Jan 2027: engine slice.** Stockfish in the browser (Web Workers, no new
  containers); critical moments and only-move find rate; resignation quality; drills.
- **Feb – Apr 2027: human baseline.** Maia-3 in the browser once its weight licence is
  confirmed; "surprising mistake" rate against players of your level; Lichess import.
- **From May 2027: gaze.** Webcam eye tracking in Chess Habits' own training sessions (never
  during chess.com play), opt-in and processed in the browser.
