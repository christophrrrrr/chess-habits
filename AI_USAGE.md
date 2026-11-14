# AI usage log

Required by the assignment: one row per significant piece of AI-assisted work. Every AI-generated
change is reviewed by a team member in its pull request before merging.

| Date | Who | Tool | What | How it was checked |
|---|---|---|---|---|
| 2026-11-12 | Christoph Rintz | Claude Code (Claude Opus) | Games service: chess.com import, players CRUD, migrations, Dockerfile, tests, CI workflow | Unit/API tests (97% coverage), real import of 801 games from chess.com, lint, `pip-audit`; reviewed in PR |
