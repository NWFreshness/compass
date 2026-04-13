import enum
import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import DateTime, Enum, Float, ForeignKey, JSON, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class AITargetType(str, enum.Enum):
    student = "student"
    class_ = "class"


class AIRec(Base):
    __tablename__ = "ai_recs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    target_type: Mapped[AITargetType] = mapped_column(Enum(AITargetType), nullable=False)
    student_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("students.id"), nullable=True)
    class_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("classes.id"), nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"), nullable=False)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    temperature: Mapped[float] = mapped_column(Float, nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    response: Mapped[str] = mapped_column(Text, nullable=False)
    snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    parse_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    student: Mapped[Optional["Student"]] = relationship("Student", back_populates="ai_recs")
    creator: Mapped["User"] = relationship("User", foreign_keys=[created_by])
    class_: Mapped[Optional["Class"]] = relationship("Class", back_populates="ai_recs")
