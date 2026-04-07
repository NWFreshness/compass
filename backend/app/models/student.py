import uuid
from typing import Optional
from sqlalchemy import ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class Student(Base):
    __tablename__ = "students"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    student_id_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    grade_level: Mapped[int] = mapped_column(Integer, nullable=False)
    school_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("schools.id"), nullable=False)
    class_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("classes.id"), nullable=True)

    school: Mapped["School"] = relationship("School", back_populates="students")
    class_: Mapped[Optional["Class"]] = relationship("Class", back_populates="students")
    scores: Mapped[list["Score"]] = relationship("Score", back_populates="student")
    interventions: Mapped[list["Intervention"]] = relationship("Intervention", back_populates="student")
    ai_recs: Mapped[list["AIRec"]] = relationship("AIRec", back_populates="student")
