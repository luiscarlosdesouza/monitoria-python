from sqlalchemy import Column, Integer, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Frequency(Base):
    __tablename__ = "frequencies"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    school_class_id = Column(Integer, ForeignKey("school_classes.id", ondelete="CASCADE"), nullable=False)
    month = Column(Integer, nullable=False)                         # Mês de referência (1-12)
    registered = Column(Boolean, default=False, nullable=False)     # Frequência atestada pelo docente
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("student_id", "school_class_id", "month", name="uq_frequency_student_class_month"),
    )

    student = relationship("Student", back_populates="frequencies")
    school_class = relationship("SchoolClass", back_populates="frequencies")

    def __repr__(self):
        return f"<Frequency Aluno:{self.student_id} Turma:{self.school_class_id} Mes:{self.month} Atestado:{self.registered}>"
