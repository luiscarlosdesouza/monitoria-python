from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.sql import func
from app.database import Base

class MailTemplate(Base):
    __tablename__ = "mail_templates"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    mail_class = Column(String(255), nullable=False)
    description = Column(String(256), nullable=False)
    sending_frequency = Column(String(50), nullable=False)           # Manual, Diário, Mensal, etc.
    sending_date = Column(String(50), nullable=True)
    sending_hour = Column(String(50), nullable=True)
    active = Column(Boolean, default=False, nullable=False)
    subject = Column(String(256), nullable=False)
    body = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<MailTemplate {self.name} Ativo:{self.active}>"
