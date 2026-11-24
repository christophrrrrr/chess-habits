# Sprint Review demo (25–26 Nov 2026)

10 minutes of demo plus 5 minutes of questions. Every member presents the part they built and
must be able to explain it. **This is a proposal: the team confirms the split and the timings in
the rehearsal.**

The review has to show four things ([assignment.md](../assignment.md)): the product live from its
public URL with the Sprint Goal and completed items; a change merged just before or during the
review going through the pipeline to production; the monitoring dashboard and SLO; the next
sprint plan and the main retrospective agreement.

## Running order

| Time | Part | Presenter | What to show |
|---|---|---|---|
| 0:00 | Sprint Goal and the live PR | Laura (PO) | Sprint Goal from [sprint-2.md](sprint-2.md), what got done. Merge the live PR (below) now, so the deploy finishes during the demo. |
| 1:00 | The product, live | Christoph | The demo story (below) on the public URL. |
| 4:00 | The pipeline | Zaid | The live PR's run: lint, tests with coverage, security scans, image build, compose smoke test, deploy, health check. |
| 6:00 | Tests | Laura | The Playwright test clicking through the main story in CI. |
| 6:30 | Monitoring and reliability | Nika | The Workbook (request count, error rate, latency), the SLO query, and partial failure: stop the games app, findings stay readable. |
| 8:30 | Releases | Xander | Release tags, the changelog and the GitHub Release for the sprint. |
| 9:00 | Scrum | Javi | The board, the roles per sprint, the main retrospective agreement and the plan after the course. |
| 9:45 | The live PR is in production | Laura | Reload the site and show the change. |

## The demo story

1. **Home page**: the tracked accounts as tiles.
2. **Import**: open an account that was imported the day before and press *Import from
   chess.com*; only the current month is fetched, so it finishes in seconds.
3. **Habit tile**: open the clock profile tile; the page shows the finding, its interval and the
   label (Finding / No clear effect / Not enough data).
4. **Adopt a rule**: adopt the suggested clock checkpoint on that page.
5. **Rule card**: back on the overview, the new rule tile shows whether it is being kept.
6. **Grandmaster comparison**: *Compare with a grandmaster*, pick the one imported before the
   review (e.g. Hikaru), and show the differences marked "clearly different".

## The live PR

A small, visible, low-risk change that is reviewed and approved the day before and only merged
during the review, for example a line of text on the home page. It must not touch migrations or
infrastructure. A deploy takes a few minutes, so it is merged at the start and shown at the end.

## Before the review

- [ ] Rehearsal with the whole team; every presenter can explain their part without notes.
- [ ] The day before: import the demo account and the grandmaster on the live site, so the demo
      does not depend on chess.com.
- [ ] The live PR is open, approved and CI green.
- [ ] 5 minutes before: open the site and run an analysis to wake up both services (scale to zero
      means the first request takes 30–90 s).
- [ ] Tabs open: live site, the GitHub Actions run list, the Workbook, the board.
- [ ] Fallback screenshots of every step in `docs/scrum/demo/` (taken after the first deployment).

## If something breaks

| Problem | Fallback |
|---|---|
| A service is still starting | Say so (the UI shows the "waking up" banner), carry on with the next part and come back. |
| chess.com is down | Skip the import step; all data shown is already stored. |
| The deploy of the live PR is slow or fails | Show the run as it is and the last successful deploy; explain the health-check gate. |
| Azure is down | Fallback screenshots, then the same story on `docker compose up` locally. |
