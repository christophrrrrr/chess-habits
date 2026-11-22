# Assignment Requirements (checklist)

Summary of the group assignment *"Plan, Build, Ship and Operate a Product as a Scrum Team on Azure"*. The official PDF is the source of truth; this is a working checklist.

- **Deadline:** 2026-11-24 23:59 (code and docs). Graded version = commit tagged `submission` on `main`.
- **Sprint Reviews:** 25–26 Nov 2026, in class.
- **Weight:** 15% of the course grade.

> Minimum means minimum, viable means working. A small product that works, is tested, deploys itself and can be monitored scores higher than an ambitious one that does not run. Keep `main` deployable at all times.

## Timeline

| Sprint | Dates | Goal |
|---|---|---|
| 0 | 4–10 Nov | Team, roles, idea, Product Backlog, repo, Definition of Done, local skeleton (`docker compose up` returns a page or `/health`) |
| 1 | 11–18 Nov | Skeleton deployed to Azure **by the pipeline**, then the first core feature end to end |
| 2 | 19–24 Nov | MVP complete, monitoring, documentation |
| Review | 25–26 Nov | Live demo and Sprint Review |

## Scrum

- [ ] Product Owner and Scrum Master rotate each sprint; record who held which role.
- [ ] Backlog in **GitHub Projects**: user stories with acceptance criteria.
- [ ] `docs/scrum/sprint-N.md` per sprint: Sprint Goal, items selected, done / not done, retrospective agreements.
- [ ] `docs/scrum/definition-of-done.md`: at least merged via reviewed PR, CI green, deployed.
- [ ] Every change through a PR approved by another member. Branch protection on `main`.

## Product

- [ ] Web app with a static UI on **Azure Static Web Apps**.
- [ ] At least **one persisted entity with full CRUD**.
- [ ] At least **one feature beyond CRUD**.
- [ ] Backend: Python (Flask/FastAPI) or Node.js (Express). Frontend: static files (plain HTML/JS or React/Vue built to static).
- [ ] **Exactly two services**, each in its own container with its **own database**, talking over HTTP. The UI calls them from the browser; CORS restricted to the UI's origin.
- [ ] One Dockerfile per container: no `COPY . .`, no secrets in the image, pinned dependencies, non-root user.
- [ ] `docker-compose.yml` brings the whole system up from a clean clone (SQL Server in compose locally).
- [ ] Schema via **versioned migration files applied on startup**.
- [ ] `GET /health` on every service; one log line per request to stdout (method, path, status, duration).
- [ ] **No secrets in the repo.** A leaked credential that was never revoked caps the grade at 40/100.
- [ ] Paid APIs (if any): key as a GitHub secret, cost kept low (cache, rate limit).

**Out of scope:** always-on compute, Kubernetes, message brokers, other databases, a third container, auth beyond a simple mechanism (optional API key or hard-coded demo user), payments.

## Azure

- [ ] Use the group's existing resource group `rg-sdd-<class>-g<N>`. Never create resource groups.
- [ ] At most **2 Container Apps** (Consumption plan, scale to zero, max 1 replica), **2 serverless Azure SQL databases** (auto-pause), **1 Static Web App** (`<prefix>-ui`).
- [ ] Resource names start with `sdd-<class>-g<N>` (e.g. `sdd-3a-g3-api`, `sdd-3a-g3-api-db`).
- [ ] Images in **GitHub Container Registry**.
- [ ] Pipeline signs in as the **group's managed identity** `sdd-<class>-g<N>-github` (OIDC; created by the professor).
- [ ] Config only through environment variables and secrets; nothing changed manually after setup.
- [ ] Initial setup scripted (Azure CLI) or IaC (Bicep/Terraform; IaC earns credit).
- [ ] CI never touches the Azure database.
- [ ] No other Azure services, no other cloud, no Render/Vercel/Railway/Heroku.

## CI/CD (GitHub Actions)

- [ ] **On every PR and push:** lint, format check, tests with coverage (**fail below 70%** on core logic of each service), image build. Recommended: `pip-audit` / `npm audit` / Bandit / CodeQL.
- [ ] **On merge to `main`:** push images tagged with commit SHA, deploy services and UI only if CI passed, apply migrations, check `/health` after deploy and fail if not 200 in time.
- [ ] Credited extras: IaC, release/tagging scheme, zero-downtime (blue-green or canary with Container Apps revisions), smoke/E2E test against the deployed URL.

## Monitoring and reliability

- [ ] Request logs queryable in the Container Apps environment's **Log Analytics** workspace (INFO level, no request bodies).
- [ ] Dashboard: request count, error rate, response time (saved queries, Workbook or portal dashboard).
- [ ] One **SLO** with the query that measures it.
- [ ] **Partial failure:** with one service (or an external API) down, the other keeps working; the affected flow fails with a timeout and a clear message.

## Documentation

- [ ] `README.md`: what it does, live URL, architecture diagram (matching the deployment), run locally, run tests, reproduce Azure setup, team with GitHub usernames.
- [ ] `docs/decisions.md`: 4–6 decision records (context, decision, alternatives, consequences): architecture, storage, deployment/pipeline, monitoring, and more.
- [ ] `docs/data-model.md`: entities and relationships (diagram), matching the migrations.
- [ ] `docs/scrum/`: Definition of Done and one file per sprint.
- [ ] `AI_USAGE.md`: one row per significant AI-assisted piece of work (including workflows, Dockerfiles, IaC).

## Sprint Review (10 min + 5 min questions)

1. Product live from its public URL: Sprint Goal and completed items.
2. A change merged just before or during the review, going through the pipeline to production.
3. Monitoring dashboard and SLO.
4. Next sprint plan and main retrospective agreement.

Every member presents a part and must be able to explain what they built.

## Individual contribution statement

Each member submits individually on Blackboard: what they built (with PR links), roles per sprint, contribution % for every member (adds to 100%) with one line of justification each.

## Grading

| Category | Weight |
|---|---|
| Product, Architecture & Code Quality | 25% |
| Cloud Infrastructure | 15% |
| DevOps Pipeline | 20% |
| Testing | 10% |
| Monitoring & Reliability | 10% |
| Scrum Process | 10% |
| Documentation & Sprint Review | 10% |
