import enum
import uuid
from datetime import date
from typing import Optional
from sqlalchemy import CheckConstraint, Date, Enum, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class InterventionStatus(str, enum.Enum):
    active = "active"
    resolved = "resolved"


class Intervention(Base):
    __tablename__ = "interventions"
    __table_args__ = (
        CheckConstraint(
            "(student_id IS NOT NULL AND class_id IS NULL) OR (student_id IS NULL AND class_id IS NOT NULL)",
            name="ck_intervention_one_target",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    student_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("students.id"), nullable=True)
    class_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("classes.id"), nullable=True)
    teacher_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"), nullable=False)
    strategy: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    outcome_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[InterventionStatus] = mapped_column(Enum(InterventionStatus), default=InterventionStatus.active, nullable=False)

    student: Mapped[Optional["Student"]] = relationship("Student", back_populates="interventions")
    class_: Mapped[Optional["Class"]] = relationship("Class", back_populates="interventions")
