from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
from app.models.instructor import instructor_school_class
from app.models.class_schedule import class_schedule_school_class

class SchoolClass(Base):
    __tablename__ = "school_classes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    school_term_id = Column(Integer, ForeignKey("school_terms.id", ondelete="CASCADE"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="CASCADE"), nullable=False)
    codtur = Column(String(50), nullable=False)      # Código da turma
    tiptur = Column(String(50), nullable=True)       # Tipo da turma (Teórica, Prática)
    nomdis = Column(String(255), nullable=True)      # Nome da disciplina
    coddis = Column(String(50), nullable=False)      # Código da disciplina (ex: MAC0110)
    dtainitur = Column(DateTime, nullable=True)      # Início das aulas da turma
    dtafimtur = Column(DateTime, nullable=True)      # Fim das aulas da turma
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("codtur", "coddis", "school_term_id", name="uq_school_class_term"),
    )

    school_term = relationship("SchoolTerm", back_populates="school_classes")
    department = relationship("Department", back_populates="school_classes")
    instructors = relationship("Instructor", secondary=instructor_school_class, back_populates="school_classes")
    class_schedules = relationship("ClassSchedule", secondary=class_schedule_school_class, back_populates="school_classes")
    requisitions = relationship("Requisition", back_populates="school_class", cascade="all, delete-orphan")
    enrollments = relationship("Enrollment", back_populates="school_class", cascade="all, delete-orphan")
    selections = relationship("Selection", back_populates="school_class", cascade="all, delete-orphan")
    frequencies = relationship("Frequency", back_populates="school_class", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<SchoolClass {self.coddis} Turma {self.codtur}>"
