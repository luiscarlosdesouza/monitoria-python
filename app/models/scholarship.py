from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Scholarship(Base):
    __tablename__ = "scholarships"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)  # Ex: Bolsa Monitoria IME, Bolsa PEEG, etc.

    def __repr__(self):
        return f"<Scholarship {self.name}>"

class ModelHasScholarship(Base):
    __tablename__ = "model_has_scholarships"

    scholarship_id = Column(Integer, ForeignKey("scholarships.id", ondelete="CASCADE"), primary_key=True)
    model_type = Column(String(255), primary_key=True)   # Ex: App\Models\Selection
    model_id = Column(Integer, primary_key=True)

    scholarship = relationship("Scholarship")

    def __repr__(self):
        return f"<ModelHasScholarship {self.model_type}:{self.model_id} Bolsa:{self.scholarship_id}>"
