# Research experiments

Reproducible scripts behind [docs/research/experiments/](../docs/research/experiments/). They test the three
experiments chosen in [docs/research/shortlist.md](../docs/research/shortlist.md) (section 8) on real chess.com data.
This is research code, not product code: nothing here is imported by the services.

| Folder | What it does | Write-up |
|---|---|---|
| `common/kexp/` | chess.com client (serial, cached), PGN/clock parsing, Stockfish pool with an sqlite eval cache, context table (`R_skill`, sessions), cluster bootstrap, BH | - |
| `fetch_data/` | Picks the comparison players and downloads every archive | - |
| `e1_time_vs_criticality/` | E1: relative move time vs ΔU and C_gap; critical-and-fast error excess | [e1](../docs/research/experiments/e1-time-vs-criticality.md) |
| `e2_after_loss/` | E2: after-loss contrasts for results, behaviour and move quality; shuffled-label false-positive check | [e2](../docs/research/experiments/e2-after-loss.md) |
| `e3_clock_confounds/` | E3: material proxy vs engine for flag games; time-trouble coefficient with position controls; premove detector | [e3](../docs/research/experiments/e3-clock-confounds.md) |

## Data stays out of the repo

All downloads, the Stockfish binary, eval caches and outputs live under the folder named by the
environment variable `CHESS_HABITS_EXP_DATA` (default `experiments/data/`, gitignored, see `.gitignore`).
Downloaded files are treated as untrusted data: nothing in that folder is executed, and every script is
run with `python -I` (isolated mode) from the repo root.

## Rerun everything

Windows, Python 3.12, 8 cores. Engine wall time on an i7-9700F (8 cores, 7 Stockfish processes) was about 1 h 50 min in total
(E1 owner about 35 min, E1 others 36 min, E2 21 min, E3 20 min); reruns read the eval cache and take minutes
(E2's 1,000 label shuffles per player take about 5 min).

```bash
pip install -r experiments/requirements.txt
export CHESS_HABITS_EXP_DATA=/path/outside/the/repo/research-data      # optional

# 1. Stockfish 19, official build (https://github.com/official-stockfish/Stockfish/releases/tag/sf_19)
mkdir -p "$CHESS_HABITS_EXP_DATA/stockfish" && cd "$CHESS_HABITS_EXP_DATA/stockfish"
curl -LO https://github.com/official-stockfish/Stockfish/releases/download/sf_19/stockfish-windows-x86-64-universal.zip
unzip stockfish-windows-x86-64-universal.zip && cd -
# (or set CHESS_HABITS_STOCKFISH=/path/to/stockfish)

# 2. Players and games (serial requests with a contact User-Agent; cached)
python -I experiments/fetch_data/select_players.py 5      # writes $CHESS_HABITS_EXP_DATA/chesscom/players.json
python -I experiments/fetch_data/fetch_archives.py

# 3. Experiments (each prints progress and writes $CHESS_HABITS_EXP_DATA/out/*_summary.json)
python -I experiments/e1_time_vs_criticality/run.py --players chrisaxm --rapid 300 --blitz 150 --tag _owner
python -I experiments/e1_time_vs_criticality/run.py --players <P1>,<P3>,<P5> --rapid 150 --blitz 0 --tag _others
python -I experiments/e2_after_loss/run.py
python -I experiments/e2_after_loss/chart.py               # chart from e2_summary.json
python -I experiments/e3_clock_confounds/run.py
python -I experiments/e1_time_vs_criticality/compare.py    # cross-player comparison + chart (cache only)
```

Notes:
- `select_players.py` samples the public FM/CM/NM lists with a fixed seed, but the lists and ratings change
  over time, so a rerun on a later date can pick other players. The chosen names are stored only in the data
  folder; the write-ups call them P1-P5.
- The chess.com archive for the current month changes; a rerun on a later date sees more games.
- Engine results depend on the Stockfish build and node budget. Every summary JSON records both.
- `--workers` sets the number of Stockfish processes (one thread each, 64 MB hash).
- Long runs: a run that is interrupted resumes from the sqlite eval cache (written every 200 positions).
- Maia was not used: none of E1-E3 needs it, and the Maia-3 weight licence is still open (shortlist D3).
