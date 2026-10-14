from sqlalchemy import Column, Integer, String, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    codpes = Column(String(20), index=True, nullable=False)   # Número USP
    nompes = Column(String(255), nullable=False)             # Nome completo do aluno
    codema = Column(String(255), nullable=True)              # E-mail institucional ou preferencial
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("codpes", "nompes", name="uq_student_codpes_nompes"),
    )

    school_records = relationship("SchoolRecord", back_populates="student", cascade="all, delete-orphan")
    enrollments = relationship("Enrollment", back_populates="student", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="student", cascade="all, delete-orphan")
    selections = relationship("Selection", back_populates="student", cascade="all, delete-orphan")
    frequencies = relationship("Frequency", back_populates="student", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Student {self.codpes} - {self.nompes}>"
