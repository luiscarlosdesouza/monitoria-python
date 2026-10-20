import os
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.config import settings
from app.models.school_term import SchoolTerm
from app.models.school_class import SchoolClass
from app.models.department import Department
from app.models.instructor import Instructor
from app.models.student import Student
from app.models.requisition import Requisition
from app.models.enrollment import Enrollment
from app.models.selection import Selection
from app.models.frequency import Frequency
from app.models.scholarship import Scholarship, ModelHasScholarship
from app.models.mail_template import MailTemplate
from app.services.permissions import (
    is_admin,
    is_secretaria,
    is_comissao,
    is_docente,
    can_manage_selections,
    can_manage_frequencies,
    get_user_permissions
)

router = APIRouter(prefix="/admin", tags=["Administração"])
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "..", "templates"))

def has_admin_panel_access(user: Optional[dict]) -> bool:
    if not user:
        return False
    return is_admin(user) or is_secretaria(user) or is_comissao(user)

# -------------------------------------------------------------
# 1. Dashboard Administrativo
# -------------------------------------------------------------
@router.get("", response_class=HTMLResponse)
def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    user = request.session.get("user")
    if not has_admin_panel_access(user):
        return RedirectResponse(
            url="/?msg=Acesso restrito: faça login com perfil administrativo autorizado.&type=danger", 
            status_code=303
        )
    
    # Métricas Globais
    total_terms = db.query(SchoolTerm).count()
    total_classes = db.query(SchoolClass).count()
    total_instructors = db.query(Instructor).count()

    total_requisitions = db.query(Requisition).count()
    total_requested_monitors = sum(r[0] for r in db.query(Requisition.requested_number).all()) or 0
    total_enrollments = db.query(Enrollment).count()
    total_selections = db.query(Selection).count()
    active_selections = db.query(Selection).filter(Selection.sitatl == "Ativo").count()
    total_frequencies = db.query(Frequency).filter(Frequency.registered == True).count()

    # Dados por Departamento
    departments = db.query(Department).all()
    dept_stats = []
    for d in departments:
        d_classes = db.query(SchoolClass).filter(SchoolClass.department_id == d.id).count()
        d_instructors = db.query(Instructor).filter(Instructor.department_id == d.id).count()
        d_reqs = db.query(Requisition).join(SchoolClass).filter(SchoolClass.department_id == d.id).count()
        dept_stats.append({
            "dept": d,
            "classes": d_classes,
            "instructors": d_instructors,
            "requisitions": d_reqs
        })

    # Período ativo
    active_term = db.query(SchoolTerm).filter(SchoolTerm.status == "Aberto").order_by(SchoolTerm.year.desc()).first()
    if not active_term:
        active_term = db.query(SchoolTerm).order_by(SchoolTerm.year.desc()).first()

    return templates.TemplateResponse(
        request=request,
        name="admin/dashboard.html",
        context={
            "user": user,
            "active_term": active_term,
            "dept_stats": dept_stats,
            "stats": {
                "total_terms": total_terms,
                "total_classes": total_classes,
                "total_instructors": total_instructors,
                "total_requisitions": total_requisitions,
                "total_requested_monitors": total_requested_monitors,
                "total_enrollments": total_enrollments,
                "total_selections": total_selections,
                "active_selections": active_selections,
                "total_frequencies": total_frequencies
            }
        }
    )

# -------------------------------------------------------------
# 2. Seleção e Atribuição de Bolsas
# -------------------------------------------------------------
@router.get("/selections", response_class=HTMLResponse)
def list_selections(
    request: Request,
    term_id: Optional[int] = None,
    department_id: Optional[int] = None,
    school_class_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    user = request.session.get("user")
    if not has_admin_panel_access(user):
        return RedirectResponse(
            url="/?msg=Acesso restrito: faça login com perfil administrativo autorizado.&type=danger", 
            status_code=303
        )

    # Período ativo padrão

    terms = db.query(SchoolTerm).order_by(SchoolTerm.year.desc(), SchoolTerm.period.desc()).all()
    departments = db.query(Department).order_by(Department.nomabvset).all()
    scholarships = db.query(Scholarship).order_by(Scholarship.name).all()

    active_term_id = term_id or (terms[0].id if terms else None)

    # Turmas que possuem pedidos de monitoria no período
    classes_query = db.query(SchoolClass).options(
        joinedload(SchoolClass.department),
        joinedload(SchoolClass.requisitions),
        joinedload(SchoolClass.enrollments).joinedload(Enrollment.student),
        joinedload(SchoolClass.selections).joinedload(Selection.student)
    ).join(Requisition)

    if active_term_id:
        classes_query = classes_query.filter(SchoolClass.school_term_id == active_term_id)
    if department_id:
        classes_query = classes_query.filter(SchoolClass.department_id == department_id)
    if school_class_id:
        classes_query = classes_query.filter(SchoolClass.id == school_class_id)

    classes_with_req = classes_query.order_by(SchoolClass.coddis, SchoolClass.codtur).all()

    # Todas as seleções efetuadas para o período
    selections_query = db.query(Selection).options(
        joinedload(Selection.student),
        joinedload(Selection.school_class).joinedload(SchoolClass.department),
        joinedload(Selection.school_class).joinedload(SchoolClass.school_term),
        joinedload(Selection.requisition)
    )
    if active_term_id:
        selections_query = selections_query.join(SchoolClass).filter(SchoolClass.school_term_id == active_term_id)

    selections = selections_query.order_by(Selection.created_at.desc()).all()

    # Mapeia as bolsas das seleções
    selection_scholarships = {}
    mhs_records = db.query(ModelHasScholarship).filter(ModelHasScholarship.model_type == "Selection").all()
    mhs_map = {m.model_id: m.scholarship for m in mhs_records}
    for s in selections:
        selection_scholarships[s.id] = mhs_map.get(s.id)

    return templates.TemplateResponse(
        request=request,
        name="admin/selections.html",
        context={
            "user": user,
            "terms": terms,
            "departments": departments,
            "scholarships": scholarships,
            "selected_term_id": active_term_id,
            "selected_dept_id": department_id,
            "selected_class_id": school_class_id,
            "classes_with_req": classes_with_req,
            "selections": selections,
            "selection_scholarships": selection_scholarships
        }
    )

@router.post("/selections/create")
async def create_selection(request: Request, db: Session = Depends(get_db)):
    user = request.session.get("user")
    if not has_admin_panel_access(user):
        return RedirectResponse(url="/?msg=Acesso restrito.&type=danger", status_code=303)

    form = await request.form()
    school_class_id = int(form.get("school_class_id", 0))
    student_id = int(form.get("student_id", 0))
    scholarship_id = int(form.get("scholarship_id", 0))
    enrollment_id_raw = form.get("enrollment_id")
    enrollment_id = int(enrollment_id_raw) if enrollment_id_raw else None

    codpescad = str(user.get("codpes")) if user else None


    # Busca a requisição da turma
    requisition = db.query(Requisition).filter(Requisition.school_class_id == school_class_id).first()
    if not requisition:
        return RedirectResponse(
            url="/admin/selections?msg=A+turma+selecionada+não+possui+pedido+de+monitoria+cadastrado.&type=danger",
            status_code=303
        )

    # Verifica se o aluno já está selecionado para esta turma
    existing = db.query(Selection).filter(
        Selection.school_class_id == school_class_id,
        Selection.student_id == student_id,
        Selection.sitatl == "Ativo"
    ).first()

    if existing:
        return RedirectResponse(
            url="/admin/selections?msg=Este+candidato+já+está+selecionado+como+monitor+nesta+turma.&type=warning",
            status_code=303
        )

    selection = Selection(
        student_id=student_id,
        school_class_id=school_class_id,
        requisition_id=requisition.id,
        enrollment_id=enrollment_id,
        selecionado_sem_inscricao=(enrollment_id is None),
        codpescad=codpescad,
        sitatl="Ativo"
    )
    db.add(selection)
    db.flush()

    # Vincula bolsa
    if scholarship_id:
        mhs = ModelHasScholarship(
            scholarship_id=scholarship_id,
            model_type="Selection",
            model_id=selection.id
        )
        db.add(mhs)

    db.commit()
    return RedirectResponse(
        url="/admin/selections?msg=Monitor+selecionado+e+atribuído+com+sucesso!&type=success",
        status_code=303
    )

@router.post("/selections/{selection_id}/status")
async def update_selection_status(selection_id: int, request: Request, db: Session = Depends(get_db)):
    user = request.session.get("user")
    if not has_admin_panel_access(user):
        return RedirectResponse(url="/?msg=Acesso restrito.&type=danger", status_code=303)

    selection = db.query(Selection).filter(Selection.id == selection_id).first()
    if not selection:
        raise HTTPException(status_code=404, detail="Seleção não encontrada.")

    form = await request.form()
    status = str(form.get("status", "Ativo")).strip()
    motdes = form.get("motdes")

    selection.sitatl = status
    selection.motdes = motdes
    if status != "Ativo":
        selection.dtafimvin = datetime.now().strftime("%Y-%m-%d")

    db.commit()
    return RedirectResponse(
        url=f"/admin/selections?msg=Status+do+vínculo+do+monitor+atualizado+para+{status}.&type=info",
        status_code=303
    )

@router.post("/selections/{selection_id}/delete")
def delete_selection(selection_id: int, request: Request, db: Session = Depends(get_db)):
    user = request.session.get("user")
    if not has_admin_panel_access(user):
        return RedirectResponse(url="/?msg=Acesso restrito.&type=danger", status_code=303)

    selection = db.query(Selection).filter(Selection.id == selection_id).first()
    if not selection:
        raise HTTPException(status_code=404, detail="Seleção não encontrada.")

    # Remove vínculo com bolsa
    db.query(ModelHasScholarship).filter(
        ModelHasScholarship.model_type == "Selection",
        ModelHasScholarship.model_id == selection.id
    ).delete()

    db.delete(selection)
    db.commit()
    return RedirectResponse(
        url="/admin/selections?msg=Seleção+removida+com+sucesso.&type=info",
        status_code=303
    )

# -------------------------------------------------------------
# 3. Atesto de Frequência Mensal
# -------------------------------------------------------------
@router.get("/frequencies", response_class=HTMLResponse)
def list_frequencies(
    request: Request,
    term_id: Optional[int] = None,
    month: Optional[int] = None,
    department_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    user = request.session.get("user")
    if not has_admin_panel_access(user) and not is_docente(user):
        return RedirectResponse(url="/?msg=Acesso restrito: apenas Administração e Docentes podem atestar frequência.&type=danger", status_code=303)

    current_month = month or datetime.now().month


    terms = db.query(SchoolTerm).order_by(SchoolTerm.year.desc()).all()
    departments = db.query(Department).order_by(Department.nomabvset).all()

    active_term_id = term_id or (terms[0].id if terms else None)

    # Monitores ativos selecionados no período
    query = db.query(Selection).options(
        joinedload(Selection.student),
        joinedload(Selection.school_class).joinedload(SchoolClass.department),
        joinedload(Selection.school_class).joinedload(SchoolClass.instructors)
    ).filter(Selection.sitatl == "Ativo")

    if active_term_id:
        query = query.join(SchoolClass).filter(SchoolClass.school_term_id == active_term_id)
    if department_id:
        if not active_term_id:
            query = query.join(SchoolClass)
        query = query.filter(SchoolClass.department_id == department_id)

    active_monitors = query.all()

    # Registros de frequência existentes para o mês
    frequencies_map = {}
    if active_monitors:
        student_ids = [m.student_id for m in active_monitors]
        class_ids = [m.school_class_id for m in active_monitors]
        freq_records = db.query(Frequency).filter(
            Frequency.student_id.in_(student_ids),
            Frequency.school_class_id.in_(class_ids),
            Frequency.month == current_month
        ).all()
        for f in freq_records:
            frequencies_map[(f.student_id, f.school_class_id)] = f.registered

    months_list = [
        (1, "Janeiro"), (2, "Fevereiro"), (3, "Março"), (4, "Abril"),
        (5, "Maio"), (6, "Junho"), (7, "Julho"), (8, "Agosto"),
        (9, "Setembro"), (10, "Outubro"), (11, "Novembro"), (12, "Dezembro")
    ]

    return templates.TemplateResponse(
        request=request,
        name="admin/frequencies.html",
        context={
            "user": user,
            "terms": terms,
            "departments": departments,
            "selected_term_id": active_term_id,
            "selected_month": current_month,
            "selected_dept_id": department_id,
            "active_monitors": active_monitors,
            "frequencies_map": frequencies_map,
            "months_list": months_list
        }
    )

@router.post("/frequencies/toggle")
async def toggle_frequency(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    student_id = int(form.get("student_id", 0))
    school_class_id = int(form.get("school_class_id", 0))
    month = int(form.get("month", datetime.now().month))
    term_id = form.get("term_id")

    freq = db.query(Frequency).filter(
        Frequency.student_id == student_id,
        Frequency.school_class_id == school_class_id,
        Frequency.month == month
    ).first()

    if freq:
        freq.registered = not freq.registered
        state = "Atestada" if freq.registered else "Pendente"
    else:
        freq = Frequency(
            student_id=student_id,
            school_class_id=school_class_id,
            month=month,
            registered=True
        )
        db.add(freq)
        state = "Atestada"

    db.commit()
    redirect_url = f"/admin/frequencies?month={month}"
    if term_id:
        redirect_url += f"&term_id={term_id}"
    return RedirectResponse(
        url=f"{redirect_url}&msg=Frequência+do+mês+{month}+marcada+como+{state}.&type=success",
        status_code=303
    )

# -------------------------------------------------------------
# 4. Gestão de Docentes
# -------------------------------------------------------------
@router.get("/instructors", response_class=HTMLResponse)
def list_instructors(
    request: Request,
    department_id: Optional[int] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    user = request.session.get("user")
    if not is_admin(user) and not is_secretaria(user):
        return RedirectResponse(
            url="/?msg=Acesso restrito: apenas Administrador e Secretaria.&type=danger", 
            status_code=303
        )

    query = db.query(Instructor).options(
        joinedload(Instructor.department),
        joinedload(Instructor.school_classes)
    )


    if department_id:
        query = query.filter(Instructor.department_id == department_id)
    if search:
        search_fmt = f"%{search.strip()}%"
        query = query.filter((Instructor.nompes.ilike(search_fmt)) | (Instructor.codpes.ilike(search_fmt)))

    instructors = query.order_by(Instructor.nompes).all()
    departments = db.query(Department).order_by(Department.nomabvset).all()

    return templates.TemplateResponse(
        request=request,
        name="admin/instructors.html",
        context={
            "user": user,
            "instructors": instructors,
            "departments": departments,
            "selected_dept_id": department_id,
            "search": search or ""
        }
    )

@router.post("/instructors/create")
async def create_instructor(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    codpes = str(form.get("codpes", "")).strip()
    nompes = str(form.get("nompes", "")).strip()
    codema = str(form.get("codema", "")).strip()
    department_id = int(form.get("department_id", 0))

    if not codpes or not nompes or not department_id:
        return RedirectResponse(
            url="/admin/instructors?msg=Nº+USP,+Nome+e+Departamento+são+obrigatórios.&type=danger",
            status_code=303
        )

    existing = db.query(Instructor).filter(Instructor.codpes == codpes).first()
    if existing:
        return RedirectResponse(
            url=f"/admin/instructors?msg=Já+existe+um+docente+cadastrado+com+o+Nº+USP+{codpes}.&type=warning",
            status_code=303
        )

    inst = Instructor(
        codpes=codpes,
        nompes=nompes,
        codema=codema,
        department_id=department_id
    )
    db.add(inst)
    db.commit()

    return RedirectResponse(
        url=f"/admin/instructors?msg=Docente+{nompes}+cadastrado+com+sucesso!&type=success",
        status_code=303
    )

@router.post("/instructors/{instructor_id}/edit")
async def edit_instructor(instructor_id: int, request: Request, db: Session = Depends(get_db)):
    inst = db.query(Instructor).filter(Instructor.id == instructor_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Docente não encontrado.")

    form = await request.form()
    inst.nompes = str(form.get("nompes", inst.nompes)).strip()
    inst.codema = str(form.get("codema", inst.codema or "")).strip()
    inst.department_id = int(form.get("department_id", inst.department_id))

    db.commit()
    return RedirectResponse(
        url=f"/admin/instructors?msg=Docente+{inst.nompes}+atualizado+com+sucesso!&type=success",
        status_code=303
    )

@router.post("/instructors/{instructor_id}/delete")
def delete_instructor(instructor_id: int, request: Request, db: Session = Depends(get_db)):
    inst = db.query(Instructor).filter(Instructor.id == instructor_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Docente não encontrado.")

    db.delete(inst)
    db.commit()
    return RedirectResponse(
        url="/admin/instructors?msg=Docente+removido+com+sucesso.&type=info",
        status_code=303
    )

# -------------------------------------------------------------
# 5. Gestão de Departamentos
# -------------------------------------------------------------
@router.get("/departments", response_class=HTMLResponse)
def list_departments(request: Request, db: Session = Depends(get_db)):
    user = request.session.get("user")
    if not is_admin(user) and not is_secretaria(user):
        return RedirectResponse(
            url="/?msg=Acesso restrito: apenas Administrador e Secretaria.&type=danger", 
            status_code=303
        )

    departments = db.query(Department).options(
        joinedload(Department.school_classes),
        joinedload(Department.instructors)
    ).order_by(Department.nomabvset).all()

    return templates.TemplateResponse(
        request=request,
        name="admin/departments.html",
        context={
            "user": user,
            "departments": departments
        }
    )

# -------------------------------------------------------------
# 6. Modelos de E-mail
# -------------------------------------------------------------
@router.get("/mailtemplates", response_class=HTMLResponse)
def list_mail_templates(request: Request, db: Session = Depends(get_db)):
    user = request.session.get("user")
    if not is_admin(user) and not is_secretaria(user):
        return RedirectResponse(
            url="/?msg=Acesso restrito: apenas Administrador e Secretaria.&type=danger", 
            status_code=303
        )

    templates_list = db.query(MailTemplate).order_by(MailTemplate.name).all()


    return templates.TemplateResponse(
        request=request,
        name="admin/mail_templates.html",
        context={
            "user": user,
            "mail_templates": templates_list
        }
    )

@router.post("/mailtemplates/{template_id}/edit")
async def edit_mail_template(template_id: int, request: Request, db: Session = Depends(get_db)):
    tmpl = db.query(MailTemplate).filter(MailTemplate.id == template_id).first()
    if not tmpl:
        raise HTTPException(status_code=404, detail="Modelo de e-mail não encontrado.")

    form = await request.form()
    tmpl.subject = str(form.get("subject", tmpl.subject)).strip()
    tmpl.body = str(form.get("body", tmpl.body)).strip()
    tmpl.active = form.get("active") in ["true", "True", "1", "on"]

    db.commit()
    return RedirectResponse(
        url=f"/admin/mailtemplates?msg=Modelo+{tmpl.name}+atualizado+com+sucesso!&type=success",
        status_code=303
    )
