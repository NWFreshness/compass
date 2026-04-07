import uuid
from typing import Optional
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Uuid
from app.models.base import Base


class School(Base):
    __tablename__ = "schools"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    users: Mapped[list["User"]] = relationship("User", back_populates="school")
    classes: Mapped[list["Class"]] = relationship("Class", back_populates="school")
    students: Mapped[list["Student"]] = relationship("Student", back_populates="school")
