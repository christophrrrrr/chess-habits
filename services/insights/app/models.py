"""ORM models. The schema itself is owned by the migrations in migrations/versions."""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Unicode, UnicodeText
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class AnalysisRun(Base):
    """One run of all analyses over a player's games."""

    __tablename__ = "analysis_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Id of the player in the games service (other service, so no foreign key).
    player_id: Mapped[int] = mapped_column(Integer, index=True)
    status: Mapped[str] = mapped_column(String(16))  # done / failed
    games_analyzed: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime)
    error: Mapped[str | None] = mapped_column(Unicode(500))

    findings: Mapped[list["Finding"]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Finding.id",
    )


class Finding(Base):
    """One measured pattern, always with its sample size and uncertainty."""

    __tablename__ = "findings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(
        ForeignKey("analysis_runs.id", ondelete="CASCADE"), index=True
    )
    analysis_key: Mapped[str] = mapped_column(String(64))
    time_class: Mapped[str] = mapped_column(String(16))
    title: Mapped[str] = mapped_column(Unicode(200))
    summary: Mapped[str] = mapped_column(Unicode(1000))
    # Effect in score points (0..1 scale): group performance minus comparison group.
    effect: Mapped[float] = mapped_column(Float)
    ci_low: Mapped[float] = mapped_column(Float)
    ci_high: Mapped[float] = mapped_column(Float)
    sample_size: Mapped[int] = mapped_column(Integer)
    confidence: Mapped[str] = mapped_column(String(16))  # high / medium / low / insufficient
    details: Mapped[str] = mapped_column(UnicodeText)  # JSON with analysis-specific numbers

    run: Mapped[AnalysisRun] = relationship(back_populates="findings")
