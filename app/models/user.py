from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.database import Base

ROLE_SECRETARIA = "Secretaria"
ROLE_DOCENTE = "Docente"
ROLE_ALUNO = "Aluno"
ROLE_MONITOR = "Monitor"
ROLE_PRESIDENTE_COMISSAO = "Presidente de Comissão"
ROLE_MEMBRO_COMISSAO = "Membro de Comissão"
ROLE_ADMINISTRADOR = "Administrador"

ROLES = [
    ROLE_SECRETARIA,
    ROLE_DOCENTE,
    ROLE_ALUNO,
    ROLE_MONITOR,
    ROLE_PRESIDENTE_COMISSAO,
    ROLE_MEMBRO_COMISSAO,
    ROLE_ADMINISTRADOR,
]

ROLE_BADGES = {
    ROLE_ADMINISTRADOR: {"bg": "danger", "icon": "fa-user-shield", "label": "Administrador"},
    ROLE_SECRETARIA: {"bg": "primary", "icon": "fa-id-badge", "label": "Secretaria"},
    ROLE_PRESIDENTE_COMISSAO: {"bg": "warning", "icon": "fa-crown", "label": "Presidente de Comissão"},
    ROLE_MEMBRO_COMISSAO: {"bg": "info", "icon": "fa-users-between-lines", "label": "Membro de Comissão"},
    ROLE_DOCENTE: {"bg": "secondary", "icon": "fa-chalkboard-user", "label": "Docente"},
    ROLE_MONITOR: {"bg": "teal", "icon": "fa-laptop-code", "label": "Monitor"},
    ROLE_ALUNO: {"bg": "success", "icon": "fa-user-graduate", "label": "Aluno"},
}

def normalize_role(role_raw: str) -> str:
    """
    Normaliza roles antigas ou variações para um dos 7 perfis oficiais.
    """
    if not role_raw:
        return ROLE_ALUNO
    r = str(role_raw).strip()
    r_lower = r.lower()
    
    if r_lower in ["admin", "administrador"]:
        return ROLE_ADMINISTRADOR
    if r_lower in ["secretaria", "sec"]:
        return ROLE_SECRETARIA
    if r_lower in ["docente", "professor", "prof"]:
        return ROLE_DOCENTE
    if r_lower in ["monitor"]:
        return ROLE_MONITOR
    if r_lower in ["presidente de comissão", "presidente de comissao", "presidente", "comissao_pres"]:
        return ROLE_PRESIDENTE_COMISSAO
    if r_lower in ["membro de comissão", "membro de comissao", "membro", "comissao_membro", "comissao"]:
        return ROLE_MEMBRO_COMISSAO
    if r_lower in ["aluno", "student", "user"]:
        return ROLE_ALUNO
    
    # Se já corresponder a algum dos oficiais
    for official in ROLES:
        if r.lower() == official.lower():
            return official
            
    return ROLE_ALUNO

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    codpes = Column(Integer, index=True, nullable=True) # NUSP
    role = Column(String(50), default=ROLE_ALUNO, nullable=False)
    password_hash = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<User id={self.id} codpes={self.codpes} name={self.name} role={self.role}>"

    @property
    def is_admin(self) -> bool:
        return self.role == ROLE_ADMINISTRADOR

    @property
    def is_secretaria(self) -> bool:
        return self.role == ROLE_SECRETARIA

    @property
    def is_comissao(self) -> bool:
        return self.role in [ROLE_PRESIDENTE_COMISSAO, ROLE_MEMBRO_COMISSAO]

    @property
    def is_docente(self) -> bool:
        return self.role == ROLE_DOCENTE

    @property
    def is_monitor(self) -> bool:
        return self.role == ROLE_MONITOR

    @property
    def is_aluno(self) -> bool:
        return self.role == ROLE_ALUNO

