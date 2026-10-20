import os
import re
from typing import Optional, List
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.requisition import Requisition
from app.models.school_class import SchoolClass
from app.models.school_term import SchoolTerm
from app.models.department import Department
from app.models.instructor import Instructor
from app.models.activity import Activity
from app.models.student import Student
from app.models.recommendation import Recommendation
from app.models.enrollment import Enrollment
from app.services.permissions import can_manage_requisitions, is_admin, is_secretaria

router = APIRouter(prefix="/requisitions", tags=["Pedidos de Monitoria"])

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "..", "templates"))

@router.get("", response_class=HTMLResponse)
def list_requisitions(
    request: Request,
    term_id: Optional[int] = None,
    department_id: Optional[int] = None,
    priority: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Requisition).options(
        joinedload(Requisition.instructor),
        joinedload(Requisition.school_class).joinedload(SchoolClass.department),
        joinedload(Requisition.school_class).joinedload(SchoolClass.school_term),
        joinedload(Requisition.activities),
        joinedload(Requisition.recommendations).joinedload(Recommendation.student)
    )

    if term_id:
        query = query.join(SchoolClass).filter(SchoolClass.school_term_id == term_id)
    if department_id:
        if not term_id:
            query = query.join(SchoolClass)
        query = query.filter(SchoolClass.department_id == department_id)
    if priority:
        query = query.filter(Requisition.priority == priority)

    requisitions = query.order_by(Requisition.created_at.desc()).all()

    # Filtros e dados auxiliares
    terms = db.query(SchoolTerm).order_by(SchoolTerm.year.desc(), SchoolTerm.period.desc()).all()
    departments = db.query(Department).order_by(Department.nomabvset).all()

    # Estatísticas rápidas
    total_requests = len(requisitions)
    total_monitors = sum(r.requested_number for r in requisitions)
    unique_classes = len(set(r.school_class_id for r in requisitions))

    user = request.session.get("user")

    return templates.TemplateResponse(
        request=request,
        name="requisitions/index.html",
        context={
            "user": user,
            "requisitions": requisitions,
            "terms": terms,
            "departments": departments,
            "selected_term_id": term_id,
            "selected_department_id": department_id,
            "selected_priority": priority,
            "stats": {
                "total_requests": total_requests,
                "total_monitors": total_monitors,
                "unique_classes": unique_classes,
            }
        }
    )

@router.get("/create", response_class=HTMLResponse)
def create_requisition_form(
    request: Request,
    class_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    user = request.session.get("user")
    if not can_manage_requisitions(user):
        return RedirectResponse(
            url="/requisitions?msg=Acesso restrito: apenas Docentes e Administração podem abrir pedidos de monitoria.&type=danger",
            status_code=303
        )
    
    # Busca turmas abertas / disponíveis
    classes = db.query(SchoolClass).options(
        joinedload(SchoolClass.department),
        joinedload(SchoolClass.school_term),
        joinedload(SchoolClass.instructors)
    ).order_by(SchoolClass.coddis, SchoolClass.codtur).all()

    instructors = db.query(Instructor).order_by(Instructor.nompes).all()
    activities = db.query(Activity).order_by(Activity.description).all()
    terms = db.query(SchoolTerm).order_by(SchoolTerm.year.desc()).all()

    # Identifica se o usuário logado é um docente cadastrado
    current_instructor_id = None
    if user and user.get("codpes"):
        matched_inst = db.query(Instructor).filter(Instructor.codpes == str(user["codpes"])).first()
        if matched_inst:
            current_instructor_id = matched_inst.id

    return templates.TemplateResponse(
        request=request,
        name="requisitions/create.html",
        context={
            "user": user,
            "classes": classes,
            "instructors": instructors,
            "activities": activities,
            "terms": terms,
            "selected_class_id": class_id,
            "current_instructor_id": current_instructor_id
        }
    )

@router.post("/create")
async def create_requisition(request: Request, db: Session = Depends(get_db)):
    user = request.session.get("user")
    if not can_manage_requisitions(user):
        return RedirectResponse(
            url="/requisitions?msg=Acesso restrito: apenas Docentes e Administração podem abrir pedidos de monitoria.&type=danger",
            status_code=303
        )

    form = await request.form()

    
    school_class_id = int(form.get("school_class_id", 0))
    instructor_id = int(form.get("instructor_id", 0))
    requested_number = int(form.get("requested_number", 1))
    priority = str(form.get("priority", "Normal"))
    comments = form.get("comments")
    activity_ids = [int(a) for a in form.getlist("activity_ids") if a]
    recommended_students_raw = str(form.get("recommended_students", "")).strip()

    if not school_class_id or not instructor_id:
        return RedirectResponse(
            url="/requisitions/create?msg=Turma+e+Docente+são+obrigatórios&type=danger",
            status_code=303
        )

    # Localiza ou inicializa a requisição
    existing = db.query(Requisition).filter(
        Requisition.school_class_id == school_class_id,
        Requisition.instructor_id == instructor_id
    ).first()

    if existing:
        req = existing
        req.requested_number = requested_number
        req.priority = priority
        req.comments = comments
    else:
        req = Requisition(
            school_class_id=school_class_id,
            instructor_id=instructor_id,
            requested_number=requested_number,
            priority=priority,
            comments=comments
        )
        db.add(req)
        db.flush()

    # Atualiza atividades associadas
    selected_activities = db.query(Activity).filter(Activity.id.in_(activity_ids)).all()
    req.activities = selected_activities

    # Processa recomendações de alunos (formato: Nº USP e opcionalmente Nome, separados por vírgula ou nova linha)
    # Exemplo: 1234567, 7654321 ou 1234567 - Maria Silva
    if recommended_students_raw:
        # Remove recomendações anteriores para recriar
        db.query(Recommendation).filter(Recommendation.requisition_id == req.id).delete()
        
        lines = re.split(r"[\n,;]+", recommended_students_raw)
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Extrai o número USP (sequência numérica)
            match_cod = re.search(r"\b\d{5,9}\b", line)
            codpes = match_cod.group(0) if match_cod else None
            
            if codpes:
                # Extrai nome se fornecido após separador '-' ou similar
                rest = line.replace(codpes, "").strip(" -:()")
                nompes = rest if rest else f"Aluno USP {codpes}"

                student = db.query(Student).filter(Student.codpes == codpes).first()
                if not student:
                    student = Student(codpes=codpes, nompes=nompes)
                    db.add(student)
                    db.flush()

                rec = Recommendation(
                    student_id=student.id,
                    requisition_id=req.id
                )
                db.add(rec)

    db.commit()
    return RedirectResponse(
        url="/requisitions?msg=Solicitação+de+monitoria+salva+com+sucesso!&type=success", 
        status_code=303
    )

@router.get("/{requisition_id}", response_class=HTMLResponse)
def view_requisition(requisition_id: int, request: Request, db: Session = Depends(get_db)):
    req = db.query(Requisition).options(
        joinedload(Requisition.instructor).joinedload(Instructor.department),
        joinedload(Requisition.school_class).joinedload(SchoolClass.department),
        joinedload(Requisition.school_class).joinedload(SchoolClass.school_term),
        joinedload(Requisition.school_class).joinedload(SchoolClass.class_schedules),
        joinedload(Requisition.activities),
        joinedload(Requisition.recommendations).joinedload(Recommendation.student)
    ).filter(Requisition.id == requisition_id).first()

    if not req:
        raise HTTPException(status_code=404, detail="Pedido de monitoria não encontrado.")

    # Busca também candidatos já inscritos nesta turma
    enrollments = db.query(Enrollment).options(
        joinedload(Enrollment.student)
    ).filter(Enrollment.school_class_id == req.school_class_id).all()

    user = request.session.get("user")

    return templates.TemplateResponse(
        request=request,
        name="requisitions/show.html",
        context={
            "user": user,
            "req": req,
            "enrollments": enrollments
        }
    )

@router.get("/{requisition_id}/edit", response_class=HTMLResponse)
def edit_requisition_form(requisition_id: int, request: Request, db: Session = Depends(get_db)):
    req = db.query(Requisition).options(
        joinedload(Requisition.instructor),
        joinedload(Requisition.activities),
        joinedload(Requisition.recommendations).joinedload(Recommendation.student)
    ).filter(Requisition.id == requisition_id).first()

    if not req:
        raise HTTPException(status_code=404, detail="Pedido de monitoria não encontrado.")

    user = request.session.get("user")
    is_owner = bool(user and user.get("codpes") and req.instructor and str(user["codpes"]) == str(req.instructor.codpes))
    if not is_admin(user) and not is_secretaria(user) and not is_owner:
        return RedirectResponse(
            url=f"/requisitions/{requisition_id}?msg=Acesso restrito: você não tem permissão para editar este pedido.&type=danger",
            status_code=303
        )

    classes = db.query(SchoolClass).options(
        joinedload(SchoolClass.department),
        joinedload(SchoolClass.school_term)
    ).order_by(SchoolClass.coddis, SchoolClass.codtur).all()

    instructors = db.query(Instructor).order_by(Instructor.nompes).all()
    activities = db.query(Activity).order_by(Activity.description).all()

    # Formata recomendações atuais em texto amigável
    rec_texts = []
    for rec in req.recommendations:
        rec_texts.append(f"{rec.student.codpes} - {rec.student.nompes}")
    recommendations_str = "\n".join(rec_texts)

    selected_activity_ids = [a.id for a in req.activities]

    return templates.TemplateResponse(
        request=request,
        name="requisitions/edit.html",
        context={
            "user": user,
            "req": req,
            "classes": classes,
            "instructors": instructors,
            "activities": activities,
            "selected_activity_ids": selected_activity_ids,
            "recommendations_str": recommendations_str
        }
    )

@router.post("/{requisition_id}/edit")
async def edit_requisition(requisition_id: int, request: Request, db: Session = Depends(get_db)):
    req = db.query(Requisition).options(joinedload(Requisition.instructor)).filter(Requisition.id == requisition_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Pedido de monitoria não encontrado.")

    user = request.session.get("user")
    is_owner = bool(user and user.get("codpes") and req.instructor and str(user["codpes"]) == str(req.instructor.codpes))
    if not is_admin(user) and not is_secretaria(user) and not is_owner:
        return RedirectResponse(
            url=f"/requisitions/{requisition_id}?msg=Acesso restrito.&type=danger",
            status_code=303
        )

    form = await request.form()
    req.requested_number = int(form.get("requested_number", 1))
    req.priority = str(form.get("priority", "Normal"))
    req.comments = form.get("comments")

    activity_ids = [int(a) for a in form.getlist("activity_ids") if a]
    req.activities = db.query(Activity).filter(Activity.id.in_(activity_ids)).all()

    recommended_students_raw = str(form.get("recommended_students", "")).strip()
    db.query(Recommendation).filter(Recommendation.requisition_id == req.id).delete()

    if recommended_students_raw:
        lines = re.split(r"[\n,;]+", recommended_students_raw)
        for line in lines:
            line = line.strip()
            if not line:
                continue
            match_cod = re.search(r"\b\d{5,9}\b", line)
            codpes = match_cod.group(0) if match_cod else None
            if codpes:
                rest = line.replace(codpes, "").strip(" -:()")
                nompes = rest if rest else f"Aluno USP {codpes}"
                student = db.query(Student).filter(Student.codpes == codpes).first()
                if not student:
                    student = Student(codpes=codpes, nompes=nompes)
                    db.add(student)
                    db.flush()

                rec = Recommendation(student_id=student.id, requisition_id=req.id)
                db.add(rec)

    db.commit()
    return RedirectResponse(
        url=f"/requisitions/{req.id}?msg=Pedido+atualizado+com+sucesso!&type=success", 
        status_code=303
    )

@router.post("/{requisition_id}/delete")
def delete_requisition(requisition_id: int, request: Request, db: Session = Depends(get_db)):
    req = db.query(Requisition).options(joinedload(Requisition.instructor)).filter(Requisition.id == requisition_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Pedido não encontrado.")

    user = request.session.get("user")
    is_owner = bool(user and user.get("codpes") and req.instructor and str(user["codpes"]) == str(req.instructor.codpes))
    if not is_admin(user) and not is_secretaria(user) and not is_owner:
        return RedirectResponse(
            url=f"/requisitions?msg=Acesso restrito: você não tem permissão para excluir este pedido.&type=danger",
            status_code=303
        )

    db.delete(req)
    db.commit()
    return RedirectResponse(
        url="/requisitions?msg=Pedido+de+monitoria+excluído+com+sucesso!&type=info", 
        status_code=303
    )

