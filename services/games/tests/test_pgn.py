from conftest import PGN, chesscom_game

from app.importer import game_from_chesscom
from app.models import Player
from app.pgn import (
    material_balance,
    opening_from_url,
    parse_moves,
    parse_time_control,
    result_from_code,
    started_at_from_pgn,
)


def test_parse_time_control():
    assert parse_time_control("180+2") == (180, 2)
    assert parse_time_control("600") == (600, 0)
    assert parse_time_control("1/86400") == (None, None)
    assert parse_time_control("") == (None, None)
    assert parse_time_control("abc") == (None, None)


def test_result_from_code():
    assert result_from_code("win") == "win"
    assert result_from_code("repetition") == "draw"
    assert result_from_code("timevsinsufficient") == "draw"
    assert result_from_code("timeout") == "loss"
    assert result_from_code("resigned") == "loss"


def test_opening_from_url():
    assert opening_from_url("https://www.chess.com/openings/Sicilian-Defense-Najdorf") == (
        "Sicilian Defense Najdorf"
    )
    assert opening_from_url(None) is None
    assert opening_from_url("https://example.com/") is None


def test_parse_moves_with_and_without_clocks():
    parsed = parse_moves(PGN)
    assert parsed.ply_count == 5
    assert parsed.clocks.split(",")[0] == "1819"
    no_clock = parse_moves('[Event "x"]\n\n1. e4 e5 2. Nf3 *')
    assert no_clock.ply_count == 3
    assert no_clock.clocks is None
    assert parse_moves("").ply_count == 0


def test_game_from_chesscom_as_black_and_unrelated():
    player = Player(username="opponent1")
    game = game_from_chesscom(player, chesscom_game("x1"))
    assert game.player_color == "black"
    assert game.result == "loss"
    assert game.opponent_username == "ChrisAxm"

    stranger = Player(username="someoneelse")
    assert game_from_chesscom(stranger, chesscom_game("x2")) is None
    assert game_from_chesscom(player, chesscom_game("x3", pgn="")) is None


def test_game_id_falls_back_to_url():
    player = Player(username="chrisaxm")
    data = chesscom_game("x4")
    del data["uuid"]
    data["url"] = "https://www.chess.com/game/live/123456"
    assert game_from_chesscom(player, data).platform_game_id == "123456"


def test_material_balance():
    start = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    assert material_balance(start, "white") == 0
    assert material_balance("4k3/8/8/8/8/8/8/R3K3 b - - 0 40", "white") == 5
    assert material_balance("4k3/8/8/8/8/8/8/R3K3 b - - 0 40", "black") == -5
    assert material_balance(None, "white") is None


def test_started_at_from_pgn():
    assert started_at_from_pgn(PGN).isoformat() == "2026-10-01T18:00:05"
    assert started_at_from_pgn('[Event "x"]') is None
    assert started_at_from_pgn('[UTCDate "bad"] [UTCTime "x"]') is None
