# AI usage log

Required by the assignment: one row per significant piece of AI-assisted work. Every AI-generated
change is reviewed by a team member in its pull request before merging.

| Date | Who | Tool | What | How it was checked |
|---|---|---|---|---|
| 2026-11-12 | Christoph Rintz | Claude Code (Claude Opus) | Games service: chess.com import, players CRUD, migrations, Dockerfile, tests, CI workflow | Unit/API tests (97% coverage), real import of 801 games from chess.com, lint, `pip-audit`; reviewed in PR |
| 2026-11-12 | Christoph Rintz | Claude Code (Claude Opus) | Insights service: analysis framework (Elo-expected baseline, pre-game rating reconstruction, confidence intervals), tilt / session / time-trouble analyses, tests | Unit/API tests (97% coverage); run on 2,642 real games; checked rating semantics against chess.com data; reviewed in PR |
| 2026-11-12 | Christoph Rintz | Claude Code (Claude Opus) | UI (React + Vite): accounts CRUD, month-by-month import with progress, findings per time control with confidence-interval bars, tests, CI job | 16 component/page tests (95% coverage), lint, build; reviewed in PR |
| 2026-11-12 | Christoph Rintz | Claude Code (Claude Opus) | docker-compose, CI compose smoke test, Bicep infrastructure, deploy and infra workflows, deployment guide | Compose smoke test in CI, `bicep build`/`lint`, `actionlint`; Azure deploy not yet run (credentials pending); reviewed in PR |
| 2026-11-12 | Christoph Rintz | Claude Code (Claude Opus) | README architecture, decision records, data model, monitoring/SLO queries, Definition of Done, sprint notes | Checked against the code and migrations; KQL to be verified once Log Analytics has data; reviewed in PR |
| 2026-11-12 | Christoph Rintz | Claude Code (Claude Opus), multi-agent research workflow | Research sweep (37 notes, gap map, shortlist, 3 experiments on real chess.com data) and the MVP analysis slice built from it: clock profile, after-loss cards, statistics layer (cluster bootstrap, MDE, Benjamini-Hochberg), definitions file, UI cards | Sources cited in each note; experiments reproducible from `experiments/`; 30 insights tests (98% coverage), 20 UI tests; results cross-checked against the experiments on 2,642 real games; reviewed in PR |
| 2026-11-12 | Christoph Rintz | Claude Code (Claude Opus) | Rule adoption with adherence tracking (MVP item 4): `rules` entity with CRUD API and migration, rule checks in every analysis run, suggested clock checkpoint, adopt buttons and rule cards in the UI | 51 insights tests (98% coverage), 29 UI tests; checked on 2,642 real games with backdated rules; reviewed in PR |
| 2026-11-12 | Christoph Rintz | Claude Code (Claude Opus) | Rename the project from Kiebitz to Chess Habits (code, images, compose, CI/CD, infra, docs) | All tests, lint and format checks re-run; reviewed in PR |
