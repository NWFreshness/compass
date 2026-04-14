import uuid
from sqlalchemy import CheckConstraint, Float, ForeignKey, Integer, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    scores: Mapped[list["Score"]] = relationship("Score", back_populates="subject")
    benchmarks: Mapped[list["Benchmark"]] = relationship("Benchmark", back_populates="subject")


class Benchmark(Base):
    __tablename__ = "benchmarks"
    __table_args__ = (
        UniqueConstraint("grade_level", "subject_id", name="uq_benchmarks_grade_level_subject_id"),
        CheckConstraint("tier1_min >= tier2_min", name="ck_benchmarks_tier1_min_gte_tier2_min"),
        CheckConstraint("tier1_min >= 0 AND tier1_min <= 100", name="ck_benchmarks_tier1_min_range"),
        CheckConstraint("tier2_min >= 0 AND tier2_min <= 100", name="ck_benchmarks_tier2_min_range"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    grade_level: Mapped[int] = mapped_column(Integer, nullable=False)
    subject_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("subjects.id"), nullable=False)
    tier1_min: Mapped[float] = mapped_column(Float, default=80.0, nullable=False)
    tier2_min: Mapped[float] = mapped_column(Float, default=70.0, nullable=False)

    subject: Mapped["Subject"] = relationship("Subject", back_populates="benchmarks")
