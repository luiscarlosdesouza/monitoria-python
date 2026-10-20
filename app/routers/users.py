import os
from typing import Optional
from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app.config import settings
from app.models.user import (
    User, 
    ROLES, 
    ROLE_ADMINISTRADOR, 
    ROLE_SECRETARIA,
    ROLE_DOCENTE,
    ROLE_ALUNO,
    ROLE_MONITOR,
    ROLE_PRESIDENTE_COMISSAO,
    ROLE_MEMBRO_COMISSAO,
    ROLE_BADGES, 
    normalize_role
)
from app.models.instructor import Instructor
from app.models.student import Student
from app.models.enrollment import Enrollment
from app.models.selection import Selection
from app.models.school_class import SchoolClass
from app.services.permissions import (
    get_user_permissions, 
    is_admin, 
    can_manage_users
)

router = APIRouter(tags=["Usuários"])
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "..", "templates"))

@router.get("/users", response_class=HTMLResponse)
@router.get("/admin/users", response_class=HTMLResponse)
def list_users(
    request: Request,
    q: Optional[str] = None,
    role_filter: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Listagem de usuários com Nome, Número USP, E-mail, Perfil e Ações.
    Acesso restrito a Administradores (e visualização para Secretaria).
    """
    current_user = request.session.get("user")
    perms = get_user_permissions(current_user)

    if not perms["is_admin"] and not perms["is_secretaria"]:
        return RedirectResponse(
            url="/?msg=Acesso restrito ao menu de Usuários. Faça login com perfil autorizado.&type=danger", 
            status_code=303
        )

    query = db.query(User)

    if q and q.strip():
        term = f"%{q.strip()}%"
        if q.strip().isdigit():
            query = query.filter(or_(User.codpes == int(q.strip()), User.name.ilike(term), User.email.ilike(term)))
        else:
            query = query.filter(or_(User.name.ilike(term), User.email.ilike(term)))

    if role_filter and role_filter != "all":
        norm_filter = normalize_role(role_filter)
        query = query.filter(User.role == norm_filter)

    users = query.order_by(User.name.asc()).all()

    # Contadores por perfil
    all_users = db.query(User).all()
    stats = {
        "total": len(all_users),
        ROLE_ADMINISTRADOR: sum(1 for u in all_users if normalize_role(u.role) == ROLE_ADMINISTRADOR),
        ROLE_SECRETARIA: sum(1 for u in all_users if normalize_role(u.role) == ROLE_SECRETARIA),
        ROLE_DOCENTE: sum(1 for u in all_users if normalize_role(u.role) == ROLE_DOCENTE),
        ROLE_ALUNO: sum(1 for u in all_users if normalize_role(u.role) == ROLE_ALUNO),
        ROLE_MONITOR: sum(1 for u in all_users if normalize_role(u.role) == ROLE_MONITOR),
        ROLE_PRESIDENTE_COMISSAO: sum(1 for u in all_users if normalize_role(u.role) == ROLE_PRESIDENTE_COMISSAO),
        ROLE_MEMBRO_COMISSAO: sum(1 for u in all_users if normalize_role(u.role) == ROLE_MEMBRO_COMISSAO),
    }

    return templates.TemplateResponse(
        request=request,
        name="users/index.html",
        context={
            "user": current_user,
            "perms": perms,
            "users": users,
            "stats": stats,
            "roles": ROLES,
            "role_badges": ROLE_BADGES,
            "q": q or "",
            "role_filter": role_filter or "all",
            "admin_nusp_list": settings.admin_nusp_list
        }
    )

@router.get("/users/{user_id}", response_class=HTMLResponse)
@router.get("/admin/users/{user_id}", response_class=HTMLResponse)
def user_details(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Exibe os detalhes cadastrais e histórico do usuário no sistema.
    """
    current_user = request.session.get("user")
    perms = get_user_permissions(current_user)

    if not perms["is_admin"] and not perms["is_secretaria"]:
        return RedirectResponse(url="/?msg=Acesso restrito.&type=danger", status_code=303)

    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        return RedirectResponse(url="/users?msg=Usuário não encontrado.&type=danger", status_code=303)

    # Buscar histórico relacionado (Docente ou Aluno/Monitor)
    instructor = None
    student = None
    classes_taught = []
    enrollments = []
    selections = []

    if target_user.codpes:
        instructor = db.query(Instructor).filter(Instructor.codpes == target_user.codpes).first()
        if instructor:
            classes_taught = instructor.school_classes

        student = db.query(Student).filter(Student.codpes == target_user.codpes).first()
        if student:
            enrollments = db.query(Enrollment).filter(Enrollment.student_id == student.id).all()
            selections = db.query(Selection).filter(Selection.student_id == student.id).all()

    norm_role = normalize_role(target_user.role)
    badge = ROLE_BADGES.get(norm_role, {"bg": "secondary", "icon": "fa-user", "label": norm_role})

    return templates.TemplateResponse(
        request=request,
        name="users/show.html",
        context={
            "user": current_user,
            "perms": perms,
            "target_user": target_user,
            "norm_role": norm_role,
            "badge": badge,
            "roles": ROLES,
            "instructor": instructor,
            "classes_taught": classes_taught,
            "student": student,
            "enrollments": enrollments,
            "selections": selections,
        }
    )

@router.post("/users/create")
@router.post("/admin/users/create")
def create_user(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    codpes: Optional[int] = Form(None),
    role: str = Form(ROLE_ALUNO),
    db: Session = Depends(get_db)
):
    """
    Cadastra previamente um usuário ou define sua função inicial.
    """
    current_user = request.session.get("user")
    perms = get_user_permissions(current_user)

    if not perms["can_manage_users"]:
        return RedirectResponse(url="/users?msg=Apenas administradores podem cadastrar usuários.&type=danger", status_code=303)

    norm_role = normalize_role(role)
    clean_email = email.strip().lower()
    clean_name = name.strip()

    # Verificar se já existe por codpes ou email
    existing_user = None
    if codpes:
        existing_user = db.query(User).filter(User.codpes == codpes).first()
    if not existing_user and clean_email:
        existing_user = db.query(User).filter(User.email == clean_email).first()

    if existing_user:
        existing_user.name = clean_name
        existing_user.role = norm_role
        if codpes:
            existing_user.codpes = codpes
        db.commit()
        return RedirectResponse(
            url=f"/users?msg=Usuário {clean_name} (Nº USP {codpes}) já existia e teve o perfil atualizado para '{norm_role}'.&type=success",
            status_code=303
        )

    new_user = User(
        name=clean_name,
        email=clean_email,
        codpes=codpes,
        role=norm_role
    )
    db.add(new_user)
    db.commit()

    return RedirectResponse(
        url=f"/users?msg=Usuário {clean_name} cadastrado com sucesso com perfil '{norm_role}'!&type=success",
        status_code=303
    )

@router.post("/users/{user_id}/edit")
@router.post("/admin/users/{user_id}/edit")
def edit_user(
    user_id: int,
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    codpes: Optional[int] = Form(None),
    role: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Edita os dados e o perfil de um usuário.
    """
    current_user = request.session.get("user")
    perms = get_user_permissions(current_user)

    if not perms["can_manage_users"]:
        return RedirectResponse(url="/users?msg=Apenas administradores podem alterar perfis.&type=danger", status_code=303)

    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        return RedirectResponse(url="/users?msg=Usuário não encontrado.&type=danger", status_code=303)

    norm_role = normalize_role(role)

    # Proteção: impedir que o usuário logado despromova a si mesmo se for admin
    if current_user and current_user.get("id") == target_user.id and norm_role != ROLE_ADMINISTRADOR:
        return RedirectResponse(
            url="/users?msg=Você não pode remover seus próprios privilégios de Administrador.&type=danger", 
            status_code=303
        )

    target_user.name = name.strip()
    target_user.email = email.strip().lower()
    target_user.codpes = codpes
    target_user.role = norm_role

    db.commit()

    return RedirectResponse(
        url=f"/users?msg=Perfil de {target_user.name} atualizado com sucesso para '{norm_role}'.&type=success",
        status_code=303
    )

@router.post("/users/{user_id}/delete")
@router.post("/admin/users/{user_id}/delete")
def delete_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Exclui um usuário do sistema.
    """
    current_user = request.session.get("user")
    perms = get_user_permissions(current_user)

    if not perms["can_manage_users"]:
        return RedirectResponse(url="/users?msg=Apenas administradores podem excluir usuários.&type=danger", status_code=303)

    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        return RedirectResponse(url="/users?msg=Usuário não encontrado.&type=danger", status_code=303)

    # Não permitir excluir a si próprio
    if current_user and current_user.get("id") == target_user.id:
        return RedirectResponse(
            url="/users?msg=Operação cancelada: você não pode excluir sua própria conta de usuário logado.&type=danger",
            status_code=303
        )

    user_name = target_user.name
    db.delete(target_user)
    db.commit()

    return RedirectResponse(
        url=f"/users?msg=Usuário {user_name} excluído com sucesso.&type=warning",
        status_code=303
    )
