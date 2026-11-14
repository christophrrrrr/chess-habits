# insights service

Runs Kiebitz's analyses over a player's games (fetched from the games service over HTTP) and
stores the findings in its own database (`analysis_runs`, `findings`).

## How findings are measured

Every game is scored against what the ratings predict (Elo expected score), so a finding never
just reflects stronger or weaker opponents. Two chess.com quirks are corrected first:

- chess.com reports **post-game** ratings; pre-game ratings are reconstructed from the previous
  game in the same time class (and the opponent's by adding back the rating change).
- A single rating is noisy, so the player's strength is the median pre-game rating of the 25
  games before and after.

Each finding compares a group of games (e.g. "right after a loss") with the rest and reports
the difference in score points with a 95% confidence interval and a confidence label. Below 30
games in either group the label is `insufficient` and no claim is made. Every analysis runs per
time control (bullet, blitz, rapid, classical).

Current analyses (see `app/analysis/analyses.py`): tilt after a loss, long sessions, time trouble.
New analyses come from the research notes in `docs/research/`.

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
a 10 s timeout; earlier findings stay readable.

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
