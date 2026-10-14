from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Enrollment(Base):
    __tablename__ = "enrollments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    school_class_id = Column(Integer, ForeignKey("school_classes.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    voluntario = Column(Boolean, default=False, nullable=False)                    # Aceita ser voluntário
    disponibilidade_diurno = Column(Boolean, default=False, nullable=False)
    disponibilidade_noturno = Column(Boolean, default=False, nullable=False)
    preferencia_horario = Column(String(255), nullable=True)                      # Preferência de turno/horário
    observacoes = Column(Text, nullable=True)                                      # Observações do candidato
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("school_class_id", "student_id", name="uq_enrollment_class_student"),
    )

    school_class = relationship("SchoolClass", back_populates="enrollments")
    student = relationship("Student", back_populates="enrollments")
    selections = relationship("Selection", back_populates="enrollment", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Enrollment Aluno:{self.student_id} Turma:{self.school_class_id} Voluntario:{self.voluntario}>"
