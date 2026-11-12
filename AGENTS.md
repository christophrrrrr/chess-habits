# Guide for AI agents

Read these before doing anything:

1. [docs/vision.md](docs/vision.md): what Chess Habits is, the design principles, open research questions.
2. [docs/assignment.md](docs/assignment.md): hard constraints from the university assignment. They override any idea in the vision.

## Rules

- **Constraints first.** Exactly two backend services, each with its own Azure SQL database; a static UI; no third container, message brokers, other databases, other clouds or extra Azure services. If an idea needs any of these, say so instead of building it.
- **MVP first.** `main` must stay deployable. Prefer a small working feature over a large unfinished one.
- **Vision test.** Every analysis must pass: *"Could chess.com's Game Review already tell you this?"* If yes, it is not a Chess Habits feature.
- **No secrets** in the repo, ever: no keys, connection strings or tokens, not even in examples. Use environment variables and `.env` files (gitignored) locally.
- **Research goes in `docs/research/`**, one file per topic, using the template in [docs/research/README.md](docs/research/README.md). Cite sources.
- **Every change via pull request** reviewed by a teammate; never push directly to `main` once branch protection is on.
- **Log AI-assisted work** as a row in `AI_USAGE.md` (required by the assignment).
