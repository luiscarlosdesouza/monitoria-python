from sqlalchemy import Column, Integer, String, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class SchoolTerm(Base):
    __tablename__ = "school_terms"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    year = Column(Integer, nullable=False)
    period = Column(String(50), nullable=False)  # Ex: '1º Semestre', '2º Semestre'
    status = Column(String(50), default="Aberto", nullable=False)  # Aberto, Em Andamento, Finalizado
    evaluation_period = Column(String(50), nullable=True)
    max_enrollments = Column(Integer, default=3, nullable=False)
    public_notice_file_path = Column(String(255), nullable=True)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    start_date_requisitions = Column(DateTime, nullable=True)
    end_date_requisitions = Column(DateTime, nullable=True)
    start_date_enrollments = Column(DateTime, nullable=True)
    end_date_enrollments = Column(DateTime, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("year", "period", name="uq_year_period"),
    )

    school_classes = relationship("SchoolClass", back_populates="school_term", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<SchoolTerm {self.year}/{self.period} - {self.status}>"
