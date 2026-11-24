# Sprint 2 (19–24 Nov 2026)

**Product Owner:** Laura · **Scrum Master:** Nika · **Developers:** Christoph, Javi, Zaid, Xander ·
see [team.md](team.md)

**Sprint Goal:** Chess Habits runs on Azure, deployed by the pipeline, with a monitoring
dashboard, security scans and browser tests in CI, and the team is ready for the Sprint Review.

Status as of 22 Nov. Live: https://polite-mud-0c720f303.6.azurestaticapps.net

Selected items are the issues with the `sprint-2` label. Each one has an owner and acceptance
criteria in its issue. Board: [Chess Habits backlog](https://github.com/users/javocruz/projects/1)
(To do → In progress → In review → Done, with a Sprint field).

| Item | Issue | Owner | PR | Status |
|---|---|---|---|---|
| Pipeline signs in to Azure through OIDC; first deployment by the pipeline | | Christoph | #23, #31 | Done: live since 22 Nov; #31 fixed the smoke test, deploys on `main` green again |
| Monitoring dashboard: KQL queries + Azure Workbook | #17 | Nika | #22 | Merged, deployed; screenshot to add |
| End-to-end browser tests with Playwright | #18 | Laura | #24 → #32 | In review (#24 continued in #32) |
| Security scans in CI: CodeQL + Bandit | #19 | Zaid | #25 | In review |
| Release tags + CHANGELOG, README screenshots | #20 | Xander | #30 | Merged (`v0.1.0`); README screenshots to add |
| Backlog board, sprint notes, retrospectives, Sprint Review demo script | #21 | Javi | #26, #27 | Board done, demo script merged (#27); sprint notes in review (#26) |
| Methods page: every definition and threshold in the UI | #28 | Javi | #29 | Merged |
| Tag `submission` on `main` before 24 Nov 23:59 | | Laura | | To do |

## Sprint Review (25–26 Nov)

10 minutes of demo plus 5 minutes of questions; every member presents the part they built. The
demo story, who presents what and the fallback plan go in `demo.md` (#21).

## Retrospective

_Draft of 23 Nov, written from the PRs and pipeline runs. The team confirms or changes it before
the `submission` tag._

**What went well**

- The work was split: six members opened a PR for their own backlog item this sprint, as agreed
  in the Sprint 1 retrospective.
- Chess Habits is live on Azure since 22 Nov, deployed by the pipeline, which signs in through
  OIDC with the group's managed identity, so no Azure secret is stored anywhere.
- The monitoring dashboard is deployed from Bicep together with the rest of the infrastructure,
  and the first release is tagged (`v0.1.0`) with a changelog.

**What did not go well**

- `AI_USAGE.md` conflicted on almost every PR, because every row is added at the end of the same
  table. Each fix meant merging `main` in again, which also dismissed the approvals.
- The live smoke test still looked for the old `tilt` analysis, so three deploys on 22 Nov were
  red although the system was fine. #31 fixed it.
- The first deploy came on 22 Nov, two days before the deadline: Azure access arrived on 18 Nov,
  and the OIDC sign-in needed trial and error because GitHub puts the owner and repository IDs in
  the token's subject, which our guide did not say (now documented in #31).
- Two items stalled in review: the Playwright PR (#24) came from a fork without the test files,
  so CI never ran on it (continued in #32), and CodeQL in #25 cannot upload results on a private
  repository.

**Agreements for the next sprint**

- Open a PR early, from a branch in this repository (not a fork), so CI runs from the first push.
- Smoke tests check things that do not change with the product, such as `/health` and that
  `/analyses` is not empty, instead of one analysis by name.
- Try a new tool or cloud setting in a small spike first (as CodeQL and OIDC showed), before
  building a whole item on it.
