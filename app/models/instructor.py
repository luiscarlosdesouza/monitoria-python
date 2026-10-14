from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

instructor_school_class = Table(
    "instructor_school_class",
    Base.metadata,
    Column("instructor_id", Integer, ForeignKey("instructors.id", ondelete="CASCADE"), primary_key=True),
    Column("school_class_id", Integer, ForeignKey("school_classes.id", ondelete="CASCADE"), primary_key=True),
)

class Instructor(Base):
    __tablename__ = "instructors"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="CASCADE"), nullable=False)
    codpes = Column(String(20), index=True, nullable=False)  # Número USP
    nompes = Column(String(255), nullable=False)
    codema = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    department = relationship("Department", back_populates="instructors")
    school_classes = relationship("SchoolClass", secondary=instructor_school_class, back_populates="instructors")
    requisitions = relationship("Requisition", back_populates="instructor", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Instructor {self.codpes} - {self.nompes}>"
