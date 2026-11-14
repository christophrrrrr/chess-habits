# insights service

Runs Kiebitz's analyses over a player's games (fetched from the games service over HTTP) and
stores the findings in its own database (`analysis_runs`, `findings`).

## How findings are measured

All definitions live in [docs/definitions.md](../../docs/definitions.md). In short:

- Results are residuals: actual score minus the score expected from the player's smoothed
  strength (`R_skill`) and the opponent's pre-game rating. chess.com reports post-game ratings,
  so pre-game ratings are reconstructed first.
- Every comparison has a 95% cluster-bootstrap interval (sessions or games), a minimum
  detectable effect, and a label after Benjamini-Hochberg correction over the whole run:
  **finding** (q ≤ 0.05), **exploratory** (q ≤ 0.10), **no clear effect** (nothing larger than
  the MDE) or **not enough data** (below 100 games for results, 30 for behaviour rates).
- Every analysis runs per time control (bullet, blitz, rapid, classical).

## Analyses

Chosen by the research sweep ([docs/research/shortlist.md](../../docs/research/shortlist.md)):

| Card | Key | What it shows |
|---|---|---|
| Clock profile | `clock_profile` | Time-trouble rate, onset move, self-inflicted share, main cause (opening / long thinks / drain), pace in wins vs losses, games decided on time by final material |
| Time-trouble cost | `time_trouble_score` | Result in games with vs without time trouble (an association; held up against position controls in research E3) |
| Requeue after a loss | `after_loss_requeue` | How often the next game starts within 60 s after a loss vs a win |
| Result after a loss | `after_loss_result` | Residual right after a loss vs right after a win, in Elo |
| Stop-loss rules | `stop_loss_rules` | Whether "stop after 2/3 losses" would have skipped games played below the player's level |

## API

| Method | Path | What it does |
|---|---|---|
| GET | `/health` | Liveness check |
| GET | `/analyses` | Available analyses |
| POST | `/players/{id}/runs` | Fetch the player's games from the games service, run all analyses, store findings |
| GET | `/players/{id}/runs` | Past runs |
| GET | `/players/{id}/findings` | Latest run with findings |
| GET | `/runs/{id}` | One run with findings |
| DELETE | `/runs/{id}` | Delete a run |

If the games service is down, `POST /players/{id}/runs` answers `503` with a clear message after
a 60 s timeout (enough for the games service to wake from scale-to-zero); earlier findings stay readable.

## Run and test locally

```bash
cd services/insights
uvicorn app.main:app --reload --port 8002   # needs the games service on GAMES_SERVICE_URL
pytest --cov
ruff check . && ruff format --check .
```

| Variable | Default |
|---|---|
| `DATABASE_URL` | `sqlite:///./insights.db` (`mssql+pymssql://...` in compose / Azure) |
| `GAMES_SERVICE_URL` | `http://localhost:8001` |
| `CORS_ORIGINS` | `http://localhost:5173` |
