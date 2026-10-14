from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Selection(Base):
    __tablename__ = "selections"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    school_class_id = Column(Integer, ForeignKey("school_classes.id", ondelete="CASCADE"), nullable=False)
    enrollment_id = Column(Integer, ForeignKey("enrollments.id", ondelete="SET NULL"), nullable=True)
    requisition_id = Column(Integer, ForeignKey("requisitions.id", ondelete="CASCADE"), nullable=False)
    selecionado_sem_inscricao = Column(Boolean, default=False, nullable=False)
    codpescad = Column(String(20), nullable=True)     # NUSP do operador que efetuou a escolha
    dtafimvin = Column(String(50), nullable=True)     # Data de encerramento do vínculo
    sitatl = Column(String(50), default="Ativo")      # Situação: Ativo, Desligado, Finalizado
    motdes = Column(String(512), nullable=True)       # Motivo do desligamento eventual
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    student = relationship("Student", back_populates="selections")
    school_class = relationship("SchoolClass", back_populates="selections")
    enrollment = relationship("Enrollment", back_populates="selections")
    requisition = relationship("Requisition", back_populates="selections")
    self_evaluations = relationship("SelfEvaluation", back_populates="selection", cascade="all, delete-orphan")
    instructor_evaluations = relationship("InstructorEvaluation", back_populates="selection", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Selection Aluno:{self.student_id} Turma:{self.school_class_id} Status:{self.sitatl}>"
