from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class SelfEvaluation(Base):
    __tablename__ = "self_evaluations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    selection_id = Column(Integer, ForeignKey("selections.id", ondelete="CASCADE"), nullable=False)
    student_amount = Column(Integer, default=0, nullable=False)        # Quantidade média de alunos atendidos
    homework_amount = Column(Integer, default=0, nullable=False)       # Quantidade de listas corrigidas
    secondary_activity = Column(Text, nullable=True)                  # Outras atividades realizadas
    workload = Column(Integer, default=12, nullable=False)             # Carga horária semanal média cumprida
    workload_reason = Column(Text, nullable=True)                     # Justificativa de variação na carga
    comments = Column(Text, nullable=True)                            # Comentários gerais
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    selection = relationship("Selection", back_populates="self_evaluations")

    def __repr__(self):
        return f"<SelfEvaluation Selecao:{self.selection_id}>"

class InstructorEvaluation(Base):
    __tablename__ = "instructor_evaluations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    selection_id = Column(Integer, ForeignKey("selections.id", ondelete="CASCADE"), nullable=False)
    ease_of_contact = Column(Integer, default=5, nullable=False)      # Facilidade de contato (1 a 5)
    efficiency = Column(Integer, default=5, nullable=False)           # Eficiência e pontualidade (1 a 5)
    reliability = Column(Integer, default=5, nullable=False)          # Assiduidade e confiabilidade (1 a 5)
    overall = Column(Integer, default=5, nullable=False)              # Avaliação geral (1 a 5)
    comments = Column(Text, nullable=True)                            # Parecer do docente
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    selection = relationship("Selection", back_populates="instructor_evaluations")

    def __repr__(self):
        return f"<InstructorEvaluation Selecao:{self.selection_id} Geral:{self.overall}>"
