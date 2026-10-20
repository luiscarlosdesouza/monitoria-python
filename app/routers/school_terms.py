import os
import time
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Request, Depends, Form, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.school_term import SchoolTerm
from app.models.school_class import SchoolClass
from app.models.requisition import Requisition
from app.models.enrollment import Enrollment
from app.services.permissions import can_manage_terms

router = APIRouter(prefix="/schoolterms", tags=["Períodos Letivos"])

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "..", "templates"))

# Diretório para editais oficiais
EDITAIS_DIR = os.path.join(os.path.dirname(__file__), "..", "static", "uploads", "editais")
os.makedirs(EDITAIS_DIR, exist_ok=True)

@router.get("", response_class=HTMLResponse)
def list_terms(
    request: Request,
    status: Optional[str] = None,
    year: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = db.query(SchoolTerm).options(
        joinedload(SchoolTerm.school_classes)
    )

    if status:
        query = query.filter(SchoolTerm.status == status)
    if year:
        query = query.filter(SchoolTerm.year == year)

    terms = query.order_by(SchoolTerm.year.desc(), SchoolTerm.period.desc()).all()

    # Estatísticas
    total_terms = len(terms)
    active_terms = sum(1 for t in terms if t.status in ["Aberto", "Em Andamento"])
    total_classes_all = sum(len(t.school_classes) for t in terms)

    # Anos disponíveis para filtro
    available_years = sorted(list(set(t.year for t in db.query(SchoolTerm.year).all())), reverse=True)

    user = request.session.get("user")
    now = datetime.now()

    return templates.TemplateResponse(
        request=request,
        name="school_terms/index.html",
        context={
            "user": user,
            "terms": terms,
            "available_years": available_years,
            "selected_status": status,
            "selected_year": year,
            "now": now,
            "stats": {
                "total_terms": total_terms,
                "active_terms": active_terms,
                "total_classes": total_classes_all
            }
        }
    )

@router.get("/create", response_class=HTMLResponse)
def create_term_form(request: Request):
    user = request.session.get("user")
    if not can_manage_terms(user):
        return RedirectResponse(
            url="/schoolterms?msg=Acesso restrito: apenas Administrador e Secretaria podem gerenciar períodos letivos.&type=danger",
            status_code=303
        )
    current_year = datetime.now().year

    return templates.TemplateResponse(
        request=request,
        name="school_terms/create.html",
        context={
            "user": user,
            "current_year": current_year
        }
    )

@router.post("/create")
async def create_term(
    request: Request,
    db: Session = Depends(get_db)
):
    user = request.session.get("user")
    if not can_manage_terms(user):
        return RedirectResponse(
            url="/schoolterms?msg=Acesso restrito: apenas Administrador e Secretaria podem cadastrar períodos.&type=danger",
            status_code=303
        )

    form = await request.form()

    year = int(form.get("year", datetime.now().year))
    period = str(form.get("period", "1º Semestre")).strip()
    status = str(form.get("status", "Aberto")).strip()
    max_enrollments = int(form.get("max_enrollments", 3))
    evaluation_period = form.get("evaluation_period")

    # Datas de aulas
    started_at_str = form.get("started_at")
    finished_at_str = form.get("finished_at")
    started_at = datetime.strptime(started_at_str, "%Y-%m-%d") if started_at_str else None
    finished_at = datetime.strptime(finished_at_str, "%Y-%m-%d") if finished_at_str else None

    # Datas de requisições de docentes
    start_req_str = form.get("start_date_requisitions")
    end_req_str = form.get("end_date_requisitions")
    start_date_requisitions = datetime.strptime(start_req_str, "%Y-%m-%d") if start_req_str else None
    end_date_requisitions = datetime.strptime(end_req_str, "%Y-%m-%d") if end_req_str else None

    # Datas de inscrições de alunos
    start_enr_str = form.get("start_date_enrollments")
    end_enr_str = form.get("end_date_enrollments")
    start_date_enrollments = datetime.strptime(start_enr_str, "%Y-%m-%d") if start_enr_str else None
    end_date_enrollments = datetime.strptime(end_enr_str, "%Y-%m-%d") if end_enr_str else None

    # Verifica duplicidade
    existing = db.query(SchoolTerm).filter(SchoolTerm.year == year, SchoolTerm.period == period).first()
    if existing:
        return RedirectResponse(
            url=f"/schoolterms/create?msg=O+período+letivo+{year}+-+{period}+já+está+cadastrado.&type=warning",
            status_code=303
        )

    # Trata upload opcional do Edital (PDF)
    notice_file = form.get("notice_file")
    public_notice_file_path = None
    if notice_file and hasattr(notice_file, "filename") and notice_file.filename:
        filename = notice_file.filename
        ext = os.path.splitext(filename)[1].lower()
        if ext in [".pdf"]:
            safe_name = f"edital_{year}_{period.replace(' ', '_')}_{int(time.time())}.pdf"
            dest = os.path.join(EDITAIS_DIR, safe_name)
            with open(dest, "wb") as buffer:
                content = await notice_file.read()
                buffer.write(content)
            public_notice_file_path = f"/static/uploads/editais/{safe_name}"

    term = SchoolTerm(
        year=year,
        period=period,
        status=status,
        max_enrollments=max_enrollments,
        evaluation_period=evaluation_period,
        public_notice_file_path=public_notice_file_path,
        started_at=started_at,
        finished_at=finished_at,
        start_date_requisitions=start_date_requisitions,
        end_date_requisitions=end_date_requisitions,
        start_date_enrollments=start_date_enrollments,
        end_date_enrollments=end_date_enrollments
    )
    db.add(term)
    db.commit()

    return RedirectResponse(
        url=f"/schoolterms/{term.id}?msg=Período+letivo+{year}/{period}+criado+com+sucesso!&type=success",
        status_code=303
    )

@router.get("/{term_id}", response_class=HTMLResponse)
def term_details(term_id: int, request: Request, db: Session = Depends(get_db)):
    term = db.query(SchoolTerm).options(
        joinedload(SchoolTerm.school_classes).joinedload(SchoolClass.department),
        joinedload(SchoolTerm.school_classes).joinedload(SchoolClass.instructors),
        joinedload(SchoolTerm.school_classes).joinedload(SchoolClass.requisitions),
        joinedload(SchoolTerm.school_classes).joinedload(SchoolClass.enrollments)
    ).filter(SchoolTerm.id == term_id).first()

    if not term:
        raise HTTPException(status_code=404, detail="Período letivo não encontrado.")

    # Estatísticas do período
    classes = term.school_classes
    total_classes = len(classes)
    total_requisitions = sum(len(c.requisitions) for c in classes)
    total_requested_monitors = sum(sum(r.requested_number for r in c.requisitions) for c in classes)
    total_enrollments = sum(len(c.enrollments) for c in classes)

    user = request.session.get("user")
    now = datetime.now()

    return templates.TemplateResponse(
        request=request,
        name="school_terms/show.html",
        context={
            "user": user,
            "term": term,
            "classes": classes,
            "now": now,
            "stats": {
                "total_classes": total_classes,
                "total_requisitions": total_requisitions,
                "total_requested_monitors": total_requested_monitors,
                "total_enrollments": total_enrollments
            }
        }
    )

@router.get("/{term_id}/edit", response_class=HTMLResponse)
def edit_term_form(term_id: int, request: Request, db: Session = Depends(get_db)):
    user = request.session.get("user")
    if not can_manage_terms(user):
        return RedirectResponse(
            url=f"/schoolterms/{term_id}?msg=Acesso restrito: apenas Administrador e Secretaria podem editar períodos letivos.&type=danger",
            status_code=303
        )

    term = db.query(SchoolTerm).filter(SchoolTerm.id == term_id).first()
    if not term:
        raise HTTPException(status_code=404, detail="Período letivo não encontrado.")

    return templates.TemplateResponse(
        request=request,
        name="school_terms/edit.html",
        context={
            "user": user,
            "term": term
        }
    )

@router.post("/{term_id}/edit")
async def edit_term(term_id: int, request: Request, db: Session = Depends(get_db)):
    user = request.session.get("user")
    if not can_manage_terms(user):
        return RedirectResponse(
            url=f"/schoolterms/{term_id}?msg=Acesso restrito.&type=danger",
            status_code=303
        )

    term = db.query(SchoolTerm).filter(SchoolTerm.id == term_id).first()
    if not term:
        raise HTTPException(status_code=404, detail="Período letivo não encontrado.")

    form = await request.form()
    term.year = int(form.get("year", term.year))
    term.period = str(form.get("period", term.period)).strip()
    term.status = str(form.get("status", term.status)).strip()
    term.max_enrollments = int(form.get("max_enrollments", term.max_enrollments))
    term.evaluation_period = form.get("evaluation_period")

    # Datas de aulas
    started_at_str = form.get("started_at")
    finished_at_str = form.get("finished_at")
    term.started_at = datetime.strptime(started_at_str, "%Y-%m-%d") if started_at_str else None
    term.finished_at = datetime.strptime(finished_at_str, "%Y-%m-%d") if finished_at_str else None

    # Datas de requisições
    start_req_str = form.get("start_date_requisitions")
    end_req_str = form.get("end_date_requisitions")
    term.start_date_requisitions = datetime.strptime(start_req_str, "%Y-%m-%d") if start_req_str else None
    term.end_date_requisitions = datetime.strptime(end_req_str, "%Y-%m-%d") if end_req_str else None

    # Datas de inscrições
    start_enr_str = form.get("start_date_enrollments")
    end_enr_str = form.get("end_date_enrollments")
    term.start_date_enrollments = datetime.strptime(start_enr_str, "%Y-%m-%d") if start_enr_str else None
    term.end_date_enrollments = datetime.strptime(end_enr_str, "%Y-%m-%d") if end_enr_str else None

    # Upload de novo Edital (se enviado)
    notice_file = form.get("notice_file")
    if notice_file and hasattr(notice_file, "filename") and notice_file.filename:
        filename = notice_file.filename
        ext = os.path.splitext(filename)[1].lower()
        if ext in [".pdf"]:
            safe_name = f"edital_{term.year}_{term.period.replace(' ', '_')}_{int(time.time())}.pdf"
            dest = os.path.join(EDITAIS_DIR, safe_name)
            with open(dest, "wb") as buffer:
                content = await notice_file.read()
                buffer.write(content)
            term.public_notice_file_path = f"/static/uploads/editais/{safe_name}"

    db.commit()
    return RedirectResponse(
        url=f"/schoolterms/{term.id}?msg=Período+letivo+atualizado+com+sucesso!&type=success",
        status_code=303
    )

@router.post("/{term_id}/delete")
def delete_term(term_id: int, request: Request, db: Session = Depends(get_db)):
    user = request.session.get("user")
    if not can_manage_terms(user):
        return RedirectResponse(
            url="/schoolterms?msg=Acesso restrito: apenas Administrador e Secretaria podem excluir períodos letivos.&type=danger",
            status_code=303
        )

    term = db.query(SchoolTerm).filter(SchoolTerm.id == term_id).first()
    if not term:
        raise HTTPException(status_code=404, detail="Período letivo não encontrado.")

    label = f"{term.year}/{term.period}"
    db.delete(term)
    db.commit()

    return RedirectResponse(
        url=f"/schoolterms?msg=Período+letivo+{label}+excluído+com+sucesso.&type=info",
        status_code=303
    )

