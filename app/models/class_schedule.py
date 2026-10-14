from sqlalchemy import Column, Integer, String, DateTime, Table, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class_schedule_school_class = Table(
    "class_schedule_school_class",
    Base.metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("class_schedule_id", Integer, ForeignKey("class_schedules.id", ondelete="CASCADE"), nullable=False),
    Column("school_class_id", Integer, ForeignKey("school_classes.id", ondelete="CASCADE"), nullable=False),
)

class ClassSchedule(Base):
    __tablename__ = "class_schedules"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    diasmnocp = Column(String(50), nullable=False)  # Ex: Seg, Ter, Qua
    horent = Column(String(10), nullable=False)     # Horário entrada Ex: 08:00
    horsai = Column(String(10), nullable=False)     # Horário saída Ex: 10:00
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("diasmnocp", "horent", "horsai", name="uq_schedule_day_time"),
    )

    school_classes = relationship(
        "SchoolClass",
        secondary=class_schedule_school_class,
        back_populates="class_schedules"
    )

    def __repr__(self):
        return f"<ClassSchedule {self.diasmnocp} {self.horent}-{self.horsai}>"
