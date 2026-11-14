# Data model

Two databases, one per service. There are no foreign keys across services: `analysis_runs.player_id`
refers to `players.id` in the games database by value only.

Schema source of truth: the migrations in
[services/games/migrations/versions](../services/games/migrations/versions) and
[services/insights/migrations/versions](../services/insights/migrations/versions).

```mermaid
erDiagram
    players ||--o{ games : "has"
    players ||--o{ imported_months : "has"
    analysis_runs ||--o{ findings : "has"
    players ||..o{ analysis_runs : "player_id (other database)"

    players {
        int id PK
        string platform "chesscom"
        string username "lower case, unique with platform"
        string display_name
        string notes
        datetime created_at
        datetime updated_at
        datetime last_imported_at
    }
    imported_months {
        int id PK
        int player_id FK
        string month "YYYY-MM, unique per player"
        int game_count
        bool complete "past month: never fetched again"
        datetime imported_at
    }
    games {
        int id PK
        int player_id FK
        string platform_game_id "unique per player"
        string url
        string time_class "bullet, blitz, rapid, daily"
        string time_control "e.g. 180+2"
        int base_seconds
        int increment_seconds
        bool rated
        datetime ended_at
        string player_color
        int player_rating "post-game, as chess.com reports it"
        string opponent_username
        int opponent_rating
        string result "win, loss, draw"
        string result_detail "e.g. resigned, timeout"
        string eco
        string opening
        int ply_count
        text clocks "remaining clock per ply, tenths of a second"
        text pgn
    }
    analysis_runs {
        int id PK
        int player_id "games.players.id"
        string status
        int games_analyzed
        datetime created_at
        datetime finished_at
        string error
    }
    findings {
        int id PK
        int run_id FK
        string analysis_key "tilt, session_fatigue, time_trouble"
        string time_class
        string title
        string summary
        float effect "score points vs. comparison group"
        float ci_low
        float ci_high
        int sample_size
        string confidence "high, medium, low, insufficient"
        text details "JSON"
    }
```

Deleting a player deletes their games and imported months (`ON DELETE CASCADE`). Deleting a run
deletes its findings.
