import enum
import uuid
from datetime import date
from typing import Optional
from sqlalchemy import Date, Enum, Float, ForeignKey, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class ScoreType(str, enum.Enum):
    homework = "homework"
    quiz = "quiz"
    test = "test"


class Score(Base):
    __tablename__ = "scores"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("students.id"), nullable=False)
    subject_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("subjects.id"), nullable=False)
    score_type: Mapped[ScoreType] = mapped_column(Enum(ScoreType), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    student: Mapped["Student"] = relationship("Student", back_populates="scores")
    subject: Mapped["Subject"] = relationship("Subject", back_populates="scores")
