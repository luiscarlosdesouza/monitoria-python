from typing import Optional, Dict, Any
from app.config import settings
from app.models.user import (
    ROLE_ADMINISTRADOR,
    ROLE_SECRETARIA,
    ROLE_PRESIDENTE_COMISSAO,
    ROLE_MEMBRO_COMISSAO,
    ROLE_DOCENTE,
    ROLE_MONITOR,
    ROLE_ALUNO,
    ROLES,
    ROLE_BADGES,
    normalize_role
)

def is_authenticated(user: Optional[Dict[str, Any]]) -> bool:
    return bool(user and user.get("id"))

def is_admin(user: Optional[Dict[str, Any]]) -> bool:
    if not user:
        return False
    role = normalize_role(user.get("role", ""))
    if role == ROLE_ADMINISTRADOR:
        return True
    if str(user.get("codpes")) in settings.admin_nusp_list:
        return True
    return False

def is_secretaria(user: Optional[Dict[str, Any]]) -> bool:
    if not user:
        return False
    return normalize_role(user.get("role", "")) == ROLE_SECRETARIA

def is_comissao(user: Optional[Dict[str, Any]]) -> bool:
    if not user:
        return False
    return normalize_role(user.get("role", "")) in [ROLE_PRESIDENTE_COMISSAO, ROLE_MEMBRO_COMISSAO]

def is_docente(user: Optional[Dict[str, Any]]) -> bool:
    if not user:
        return False
    return normalize_role(user.get("role", "")) == ROLE_DOCENTE

def is_monitor(user: Optional[Dict[str, Any]]) -> bool:
    if not user:
        return False
    return normalize_role(user.get("role", "")) == ROLE_MONITOR

def is_aluno(user: Optional[Dict[str, Any]]) -> bool:
    if not user:
        return False
    return normalize_role(user.get("role", "")) == ROLE_ALUNO

# Permissões específicas de Ação
def can_manage_users(user: Optional[Dict[str, Any]]) -> bool:
    """Apenas Administradores podem gerenciar e alterar perfis de usuários."""
    return is_admin(user)

def can_manage_classes(user: Optional[Dict[str, Any]]) -> bool:
    """Administradores e Secretaria podem criar, editar e excluir turmas."""
    return is_admin(user) or is_secretaria(user)

def can_manage_terms(user: Optional[Dict[str, Any]]) -> bool:
    """Administradores e Secretaria podem criar, editar períodos e fazer upload de editais."""
    return is_admin(user) or is_secretaria(user)

def can_manage_requisitions(user: Optional[Dict[str, Any]]) -> bool:
    """Administradores, Secretaria e Docentes podem abrir e gerenciar requisições."""
    return is_admin(user) or is_secretaria(user) or is_docente(user)

def can_manage_selections(user: Optional[Dict[str, Any]]) -> bool:
    """Administração, Secretaria e Membros da Comissão de Monitoria gerenciam seleções e bolsas."""
    return is_admin(user) or is_secretaria(user) or is_comissao(user)

def can_manage_frequencies(user: Optional[Dict[str, Any]]) -> bool:
    """Administração, Secretaria, Comissão e Docentes atestam frequências."""
    return is_admin(user) or is_secretaria(user) or is_comissao(user) or is_docente(user)

def get_user_permissions(user: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Retorna mapa consolidado de permissões para uso em templates e controladores.
    """
    role = normalize_role(user.get("role", "")) if user else ""
    badge = ROLE_BADGES.get(role, {"bg": "secondary", "icon": "fa-user", "label": role or "Visitante"})
    
    return {
        "is_authenticated": is_authenticated(user),
        "role": role,
        "role_badge": badge,
        "is_admin": is_admin(user),
        "is_secretaria": is_secretaria(user),
        "is_comissao": is_comissao(user),
        "is_docente": is_docente(user),
        "is_monitor": is_monitor(user),
        "is_aluno": is_aluno(user),
        "can_manage_users": can_manage_users(user),
        "can_manage_classes": can_manage_classes(user),
        "can_manage_terms": can_manage_terms(user),
        "can_manage_requisitions": can_manage_requisitions(user),
        "can_manage_selections": can_manage_selections(user),
        "can_manage_frequencies": can_manage_frequencies(user),
    }
