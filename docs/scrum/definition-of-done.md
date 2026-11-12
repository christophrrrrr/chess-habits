# Definition of Done

A backlog item is done when all of this is true:

1. **Merged via a reviewed pull request**: approved by another team member; no direct pushes to `main`.
2. **CI green**: lint, format check, tests (coverage of each service's core logic at least 70%),
   dependency audit, image build and the `docker compose` smoke test all pass.
3. **Deployed**: the pipeline deployed the change to Azure and the health check and live smoke test passed.
4. **Acceptance criteria met** on the live URL (checked by the Product Owner).
5. **Tested**: new logic has unit or API tests; bugs get a regression test.
6. **Documented**: README / `docs/` updated if behaviour, setup or architecture changed; a decision
   record added for significant choices; data model updated with migrations.
7. **No secrets** in code, config, logs or history.
8. **AI use logged** in `AI_USAGE.md` if AI tools did a significant part of the work.
