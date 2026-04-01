from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class ScoreRecord(Base):
    __tablename__ = "score_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    role: Mapped[str] = mapped_column(String, nullable=False)
    industry: Mapped[str] = mapped_column(String, nullable=False)
    seniority: Mapped[str] = mapped_column(String, nullable=False)
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    task_scores: Mapped[list] = mapped_column(JSON, nullable=False)
    model_used: Mapped[str] = mapped_column(String, nullable=False)
    scored_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
