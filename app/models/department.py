from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    codset = Column(Integer, unique=True, index=True, nullable=False)
    nomabvset = Column(String(50), nullable=False)  # Ex: MAC, MAT, MAE, MAP
    nomset = Column(String(255), nullable=False)
    sglund = Column(String(50), default="IME", nullable=False)
    nomund = Column(String(255), default="Instituto de Matematica e Estatistica", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    school_classes = relationship("SchoolClass", back_populates="department")
    instructors = relationship("Instructor", back_populates="department")

    def __repr__(self):
        return f"<Department {self.nomabvset} - {self.nomset}>"
