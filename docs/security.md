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
   