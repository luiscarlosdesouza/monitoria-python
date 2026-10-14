from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.database import Base

class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    codcur = Column(Integer, index=True, nullable=False)
    nomcur = Column(String(255), nullable=False)
    codhab = Column(Integer, default=0, nullable=False)
    nomhab = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Course {self.codcur} - {self.nomcur}>"
