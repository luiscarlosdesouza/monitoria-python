from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class SchoolRecord(Base):
    __tablename__ = "school_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    schoolterm_id = Column(Integer, ForeignKey("school_terms.id", ondelete="CASCADE"), nullable=False)
    file_path = Column(String(255), nullable=False)  # Caminho do PDF do histórico
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("student_id", "schoolterm_id", name="uq_school_record_student_term"),
    )

    student = relationship("Student", back_populates="school_records")
    school_term = relationship("SchoolTerm")

    def __repr__(self):
        return f"<SchoolRecord Aluno:{self.student_id} Periodo:{self.schoolterm_id}>"
