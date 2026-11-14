"""ORM models. The schema itself is owned by the migrations in migrations/versions."""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Unicode,
    UnicodeText,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Player(Base):
    """A chess account tracked by Chess Habits (the CRUD entity)."""

    __tablename__ = "players"
    __table_args__ = (UniqueConstraint("platform", "username", name="uq_players_platform_user"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    platform: Mapped[str] = mapped_column(String(16))
    username: Mapped[str] = mapped_column(String(64))
    # "player": an account you track; "reference": a grandmaster to compare with.
    kind: Mapped[str] = mapped_column(String(16), default="player")
    display_name: Mapped[str | None] = mapped_column(Unicode(100))
    notes: Mapped[str | None] = mapped_column(Unicode(500))
    created_at: Mapped[datetime] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime)
    last_imported_at: Mapped[datetime | None] = mapped_column(DateTime)

    games: Mapped[list["Game"]] = relationship(
        back_populates="player", cascade="all, delete-orphan", passive_deletes=True
    )
    imported_months: Mapped[list["ImportedMonth"]] = relationship(
        cascade="all, delete-orphan", passive_deletes=True
    )


class ImportedMonth(Base):
    """One monthly chess.com archive that has been imported for a player."""

    __tablename__ = "imported_months"
    __table_args__ = (UniqueConstraint("player_id", "month", name="uq_imported_months"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"))
    month: Mapped[str] = mapped_column(String(7))  # "YYYY-MM"
    game_count: Mapped[int] = mapped_column(Integer)
    # A past month never changes on chess.com, so it is never fetched again.
    complete: Mapped[bool] = mapped_column(Boolean)
    imported_at: Mapped[datetime] = mapped_column(DateTime)


class Game(Base):
    """One game, always stored from the tracked player's point of view."""

    __tablename__ = "games"
    __table_args__ = (UniqueConstraint("player_id", "platform_game_id", name="uq_games_platform"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), index=True)
    platform_game_id: Mapped[str] = mapped_column(String(64))
    url: Mapped[str | None] = mapped_column(String(255))
    time_class: Mapped[str] = mapped_column(String(16), index=True)
    time_control: Mapped[str] = mapped_column(String(32))
    base_seconds: Mapped[int | None] = mapped_column(Integer)
    increment_seconds: Mapped[int | None] = mapped_column(Integer)
    rated: Mapped[bool] = mapped_column(Boolean)
    ended_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    player_color: Mapped[str] = mapped_column(String(5))
    player_rating: Mapped[int | None] = mapped_column(Integer)
    opponent_username: Mapped[str] = mapped_column(String(64))
    opponent_rating: Mapped[int | None] = mapped_column(Integer)
    result: Mapped[str] = mapped_column(String(4))  # win / loss / draw
    result_detail: Mapped[str] = mapped_column(String(32))  # e.g. resigned, timeout
    eco: Mapped[str | None] = mapped_column(String(8))
    opening: Mapped[str | None] = mapped_column(Unicode(255))
    ply_count: Mapped[int] = mapped_column(Integer)
    # Remaining clock after each ply in tenths of a second, comma-separated.
    clocks: Mapped[str | None] = mapped_column(UnicodeText)
    # PGN [Termination], e.g. "opponent1 won on time".
    termination: Mapped[str | None] = mapped_column(Unicode(100))
    # Material (P=1, N=B=3, R=5, Q=9) of the player minus the opponent in the final position.
    final_material: Mapped[int | None] = mapped_column(Integer)
    pgn: Mapped[str] = mapped_column(UnicodeText)

    player: Mapped[Player] = relationship(back_populates="games")
