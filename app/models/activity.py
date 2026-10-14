from sqlalchemy import Column, Integer, String, DateTime, Table, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

activity_requisition = Table(
    "activity_requisition",
    Base.metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("activity_id", Integer, ForeignKey("activities.id", ondelete="CASCADE"), nullable=False),
    Column("requisition_id", Integer, ForeignKey("requisitions.id", ondelete="CASCADE"), nullable=False),
)

class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    description = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    requisitions = relationship("Requisition", secondary=activity_requisition, back_populates="activities")

    def __repr__(self):
        return f"<Activity {self.description}>"
