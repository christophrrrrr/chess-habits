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
    """One card on the insights page. Contrasts (group A vs group B) always carry their
    interval, minimum detectable effect and a label after multiple-testing correction."""

    __tablename__ = "findings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(
        ForeignKey("analysis_runs.id", ondelete="CASCADE"), index=True
    )
    analysis_key: Mapped[str] = mapped_column(String(64))
    time_class: Mapped[str] = mapped_column(String(16))
    kind: Mapped[str] = mapped_column(String(16))  # contrast / profile
    metric: Mapped[str] = mapped_column(String(16))  # score / share / profile
    # finding / exploratory / no_effect / not_enough_data (contrasts), profile (profiles)
    label: Mapped[str] = mapped_column(String(24))
    title: Mapped[str] = mapped_column(Unicode(200))
    summary: Mapped[str] = mapped_column(Unicode(1000))
    effect: Mapped[float | None] = mapped_column(Float)
    ci_low: Mapped[float | None] = mapped_column(Float)
    ci_high: Mapped[float | None] = mapped_column(Float)
    mde: Mapped[float | None] = mapped_column(Float)
    p_value: Mapped[float | None] = mapped_column(Float)
    sample_size: Mapped[int] = mapped_column(Integer)
    details: Mapped[str] = mapped_column(UnicodeText)  # JSON with analysis-specific numbers

    run: Mapped[AnalysisRun] = relationship(back_populates="findings")
