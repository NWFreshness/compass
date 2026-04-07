import uuid
from typing import Optional
from sqlalchemy import ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class Class(Base):
    __tablename__ = "classes"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    grade_level: Mapped[int] = mapped_column(Integer, nullable=False)
    school_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("schools.id"), nullable=False)
    teacher_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    school: Mapped["School"] = relationship("School", back_populates="classes")
    teacher: Mapped[Optional["User"]] = relationship("User", back_populates="taught_classes")
    students: Mapped[list["Student"]] = relationship("Student", back_populates="class_")
    ai_recs: Mapped[list["AIRec"]] = relationship("AIRec", back_populates="class_")
