# Security scans

Every pull request runs these checks in CI. A pull request cannot be merged into `main` unless
all of them pass (branch protection).

| What | Tool | Where | Fails the build on |
|---|---|---|---|
| Our Python code | [Bandit](https://bandit.readthedocs.io/) | `ci.yml`, job `service` (games and insights) | any medium or high severity finding |
| Our Python code (during lint) | Ruff `S` rules (Bandit's rules inside Ruff) | `ci.yml`, step `Lint` | any finding |
| Our Python and TypeScript code | [CodeQL](https://codeql.github.com/), `security-extended` queries | `codeql.yml` (also on `main` and weekly) | results are shown in the repository's **Security** tab |
| Python dependencies | `pip-audit` | `ci.yml`, step `Dependency audit` | any known vulnerability |
| UI dependencies | `npm audit` | `ci.yml`, job `ui` | high or critical vulnerabilities |

## Why both Ruff and Bandit

Ruff already runs Bandit's rules during lint, so Bandit currently finds nothing new (0 issues in
both services when it was added). We keep Bandit as a separate, clearly labelled security step
with its own report and Bandit's full rule set, so a security problem fails the build as a
security problem and not as a style warning.

## Why CodeQL as well

Bandit looks at one line at a time. CodeQL follows how data moves through the code, for example
from a request parameter into a database query, so it catches problems Bandit cannot. It is the
only scanner that also checks the TypeScript UI. It runs weekly too, because GitHub adds new
rules over time and unchanged code is checked against them.

## Run the scans locally

```bash
pip install -r services/games/requirements-dev.txt
bandit -r services/games/app -ll
bandit -r services/insights/app -ll
```

## When a scan finds something

1. Fix it if it is a real problem.
2. If it is a false positive, add `# nosec <rule id>` on that line with a short comment explaining
   why it is safe (for example `# nosec B608: column names come from a fixed list`). Never
   disable a rule for the whole project.


## Review of the deep-analysis upload (#43)

`PUT /players/{player_id}/game-analyses` (insights service) stores the results of the Stockfish
pass that runs in the player's browser. Reviewed on 25 Nov 2026.

**What protects it**

- Every field is checked by the schema (`GameAnalysisBatch` in `schemas.py`): at most 200 games
  per upload and 300 moves per game, evaluations between -10000 and 10000, position keys of
  exactly 8 hex characters, FENs of at most 100 characters. Anything else gets a 422.
- The database is accessed through SQLAlchemy, so values that are uploaded never end up inside
  SQL text.
- CORS only allows the UI's own address; PUT and PATCH were added for this endpoint.
- Request logs contain the method, path, status and duration, never the uploaded data.

**Fixed**

- The same `game_id` twice in one upload created two rows, broke the unique constraint on
  (player_id, game_id) and returned a 500. The second copy now updates the first row.
  Regression test: `test_upload_with_the_same_game_twice_keeps_one_row`.

**Known risks (accepted for this course)**

- No login: anyone with the API address can overwrite a player's results. Login is out of
  scope for this assignment. CORS only blocks other websites, not someone calling the API
  directly.
- The endpoint doesn't check whether the player or the games actually exist, so the database
  could contain junk rows. They don't affect the results, because the analysis only uses
  the player's own games. To fix it, the endpoint could ask the games service which games
  belong to the player before saving.
