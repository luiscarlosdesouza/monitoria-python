from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
from app.models.activity import activity_requisition

class Requisition(Base):
    __tablename__ = "requisitions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    instructor_id = Column(Integer, ForeignKey("instructors.id", ondelete="CASCADE"), nullable=False)
    school_class_id = Column(Integer, ForeignKey("school_classes.id", ondelete="CASCADE"), nullable=False)
    requested_number = Column(Integer, nullable=False, default=1)
    priority = Column(String(50), nullable=False, default="Normal")  # Prioridade do pedido
    comments = Column(Text, nullable=True)                          # Justificativa / Observações
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("instructor_id", "school_class_id", name="uq_requisition_instructor_class"),
    )

    instructor = relationship("Instructor", back_populates="requisitions")
    school_class = relationship("SchoolClass", back_populates="requisitions")
    activities = relationship("Activity", secondary=activity_requisition, back_populates="requisitions")
    recommendations = relationship("Recommendation", back_populates="requisition", cascade="all, delete-orphan")
    selections = relationship("Selection", back_populates="requisition", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Requisition Turma:{self.school_class_id} Solicitados:{self.requested_number}>"
