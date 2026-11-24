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
    players ||..o{ rules : "player_id (other database)"
    rules ||..o{ findings : "details.rule_id (rule_check cards)"
    players ||..o{ game_analyses : "player_id (other database)"
    games ||..o| game_analyses : "game_id (other database)"

    players {
        int id PK
        string platform "chesscom"
        string username "lower case, unique with platform"
        string kind "player or reference (a grandmaster to compare with)"
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
        datetime started_at "PGN UTCDate/UTCTime"
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
        string termination "PGN Termination"
        int final_material "player minus opponent, final position"
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
        string analysis_key "clock_profile, time_trouble_score, after_loss_*, stop_loss_rules, warm_up, time_of_day, opening_time, premoves, form, critical_moments, endings, opening_autopilot, rule_check"
        string time_class
        string kind "contrast or profile"
        string metric "score, share or profile"
        string label "finding, exploratory, no_effect, not_enough_data, profile"
        string title
        string summary
        float effect "group A minus group B (contrasts only)"
        float ci_low
        float ci_high
        float mde "minimum detectable effect"
        float p_value
        int sample_size
        text details "JSON"
    }
    rules {
        int id PK
        int player_id "games.players.id"
        string time_class "bullet, blitz, rapid, classical"
        string kind "clock_checkpoint or stop_loss"
        int move "clock checkpoint: own move number"
        float min_share "clock checkpoint: share of T_est"
        string stop_rule "stop loss: two_in_a_row, three_in_a_row, three_in_session"
        string note
        datetime adopted_at
        datetime retired_at "null while active"
        datetime created_at
    }
    game_analyses {
        int id PK
        int player_id "games.players.id"
        int game_id "games.games.id, unique with player_id"
        string engine "e.g. sf19-lite-100k; null: positions only"
        int final_cp "final position, centipawns from the player's side"
        text position_keys "8-hex hashes before own moves 1-20, comma-separated"
        text moves "JSON: Stockfish rows for own moves"
        datetime updated_at
    }
```

Deleting a player deletes their games and imported months (`ON DELETE CASCADE`). Deleting a run
deletes its findings. A rule is never deleted by a run: retiring it (`retired_at`) keeps its
history, and each run writes one `rule_check` finding per active rule.

`game_analyses` (migration 0004) holds the deep analysis that the player's browser computes and
uploads (positions, Stockfish rows, final evaluation; see decision 9). The insights service never
computes it itself; each analysis run reads it next to the games from the games service.
