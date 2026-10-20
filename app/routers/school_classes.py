import os
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.school_class import SchoolClass
from app.models.school_term import SchoolTerm
from app.models.department import Department
from app.models.instructor import Instructor
from app.models.class_schedule import ClassSchedule
from app.models.requisition import Requisition
from app.models.enrollment import Enrollment

router = APIRouter(prefix="/schoolclasses", tags=["Turmas e Disciplinas"])
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "..", "templates"))

@router.get("", response_class=HTMLResponse)
def list_classes(
    request: Request,
    term_id: Optional[int] = None,
    department_id: Optional[int] = None,
    has_requisition: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(SchoolClass).options(
        joinedload(SchoolClass.department),
        joinedload(SchoolClass.school_term),
        joinedload(SchoolClass.instructors),
        joinedload(SchoolClass.class_schedules),
        joinedload(SchoolClass.requisitions),
        joinedload(SchoolClass.enrollments)
    )

    if term_id:
        query = query.filter(SchoolClass.school_term_id == term_id)
    if department_id:
        query = query.filter(SchoolClass.department_id == department_id)
    if search:
        search_fmt = f"%{search.strip()}%"
        query = query.filter(
            (SchoolClass.coddis.ilike(search_fmt)) | 
            (SchoolClass.nomdis.ilike(search_fmt)) |
            (SchoolClass.codtur.ilike(search_fmt))
        )
    if has_requisition == "1":
        query = query.filter(SchoolClass.requisitions.any())
    elif has_requisition == "0":
        query = query.filter(~SchoolClass.requisitions.any())

    classes = query.order_by(SchoolClass.coddis.asc(), SchoolClass.codtur.asc()).all()
    terms = db.query(SchoolTerm).order_by(SchoolTerm.year.desc(), SchoolTerm.period.desc()).all()
    departments = db.query(Department).order_by(Department.nomabvset.asc()).all()

    # Estatísticas
    total_classes = len(classes)
    unique_disciplines = len(set(c.coddis for c in classes))
    classes_with_req = sum(1 for c in classes if c.requisitions)
    total_enrollments = sum(len(c.enrollments) for c in classes)

    user = request.session.get("user")

    return templates.TemplateResponse(
        request=request,
        name="school_classes/index.html",
        context={
            "user": user,
            "classes": classes,
            "terms": terms,
            "departments": departments,
            "selected_term": term_id,
            "selected_dept": department_id,
            "selected_has_req": has_requisition,
            "search": search or "",
            "stats": {
                "total_classes": total_classes,
                "unique_disciplines": unique_disciplines,
                "classes_with_req": classes_with_req,
                "total_enrollments": total_enrollments
            }
        }
    )

@router.get("/create", response_class=HTMLResponse)
def create_class_form(request: Request, db: Session = Depends(get_db)):
    terms = db.query(SchoolTerm).order_by(SchoolTerm.year.desc()).all()
    departments = db.query(Department).order_by(Department.nomabvset).all()
    instructors = db.query(Instructor).order_by(Instructor.nompes).all()
    user = request.session.get("user")

    return templates.TemplateResponse(
        request=request,
        name="school_classes/create.html",
        context={
            "user": user,
            "terms": terms,
            "departments": departments,
            "instructors": instructors
        }
    )

@router.post("/create")
async def create_class(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    school_term_id = int(form.get("school_term_id", 0))
    department_id = int(form.get("department_id", 0))
    coddis = str(form.get("coddis", "")).strip().upper()
    nomdis = str(form.get("nomdis", "")).strip()
    codtur = str(form.get("codtur", "")).strip()
    tiptur = str(form.get("tiptur", "Teórica")).strip()

    dtainitur_str = form.get("dtainitur")
    dtafimtur_str = form.get("dtafimtur")

    dtainitur = datetime.strptime(dtainitur_str, "%Y-%m-%d") if dtainitur_str else None
    dtafimtur = datetime.strptime(dtafimtur_str, "%Y-%m-%d") if dtafimtur_str else None

    if not school_term_id or not department_id or not coddis or not codtur:
        return RedirectResponse(
            url="/schoolclasses/create?msg=Preencha+todos+os+campos+obrigatórios.&type=danger",
            status_code=303
        )

    # Verifica duplicidade
    existing = db.query(SchoolClass).filter(
        SchoolClass.school_term_id == school_term_id,
        SchoolClass.coddis == coddis,
        SchoolClass.codtur == codtur
    ).first()

    if existing:
        return RedirectResponse(
            url=f"/schoolclasses/create?msg=A+turma+{codtur}+da+disciplina+{coddis}+já+existe+neste+período.&type=warning",
            status_code=303
        )

    new_class = SchoolClass(
        school_term_id=school_term_id,
        department_id=department_id,
        coddis=coddis,
        nomdis=nomdis,
        codtur=codtur,
        tiptur=tiptur,
        dtainitur=dtainitur,
        dtafimtur=dtafimtur
    )
    db.add(new_class)
    db.flush()

    # Vincula docentes
    instructor_ids = [int(i) for i in form.getlist("instructor_ids") if i]
    if instructor_ids:
        insts = db.query(Instructor).filter(Instructor.id.in_(instructor_ids)).all()
        new_class.instructors = insts

    # Adiciona horário inicial se informado
    diasmnocp = str(form.get("diasmnocp", "")).strip()
    horent = str(form.get("horent", "")).strip()
    horsai = str(form.get("horsai", "")).strip()

    if diasmnocp and horent and horsai:
        schedule = db.query(ClassSchedule).filter(
            ClassSchedule.diasmnocp == diasmnocp,
            ClassSchedule.horent == horent,
            ClassSchedule.horsai == horsai
        ).first()
        if not schedule:
            schedule = ClassSchedule(diasmnocp=diasmnocp, horent=horent, horsai=horsai)
            db.add(schedule)
            db.flush()
        new_class.class_schedules.append(schedule)

    db.commit()
    return RedirectResponse(
        url=f"/schoolclasses/{new_class.id}?msg=Turma+{coddis}+criada+com+sucesso!&type=success",
        status_code=303
    )

@router.get("/{class_id}", response_class=HTMLResponse)
def class_details(class_id: int, request: Request, db: Session = Depends(get_db)):
    school_class = db.query(SchoolClass).options(
        joinedload(SchoolClass.department),
        joinedload(SchoolClass.school_term),
        joinedload(SchoolClass.instructors),
        joinedload(SchoolClass.class_schedules),
        joinedload(SchoolClass.requisitions).joinedload(Requisition.instructor),
        joinedload(SchoolClass.requisitions).joinedload(Requisition.activities),
        joinedload(SchoolClass.requisitions).joinedload(Requisition.recommendations),
        joinedload(SchoolClass.enrollments).joinedload(Enrollment.student)
    ).filter(SchoolClass.id == class_id).first()

    if not school_class:
        raise HTTPException(status_code=404, detail="Turma não encontrada.")

    user = request.session.get("user")
    return templates.TemplateResponse(
        request=request,
        name="school_classes/show.html",
        context={
            "user": user,
            "c": school_class
        }
    )

@router.get("/{class_id}/edit", response_class=HTMLResponse)
def edit_class_form(class_id: int, request: Request, db: Session = Depends(get_db)):
    school_class = db.query(SchoolClass).options(
        joinedload(SchoolClass.instructors),
        joinedload(SchoolClass.class_schedules)
    ).filter(SchoolClass.id == class_id).first()

    if not school_class:
        raise HTTPException(status_code=404, detail="Turma não encontrada.")

    terms = db.query(SchoolTerm).order_by(SchoolTerm.year.desc()).all()
    departments = db.query(Department).order_by(Department.nomabvset).all()
    instructors = db.query(Instructor).order_by(Instructor.nompes).all()
    user = request.session.get("user")

    selected_instructor_ids = [inst.id for inst in school_class.instructors]

    return templates.TemplateResponse(
        request=request,
        name="school_classes/edit.html",
        context={
            "user": user,
            "c": school_class,
            "terms": terms,
            "departments": departments,
            "instructors": instructors,
            "selected_instructor_ids": selected_instructor_ids
        }
    )

@router.post("/{class_id}/edit")
async def edit_class(class_id: int, request: Request, db: Session = Depends(get_db)):
    school_class = db.query(SchoolClass).filter(SchoolClass.id == class_id).first()
    if not school_class:
        raise HTTPException(status_code=404, detail="Turma não encontrada.")

    form = await request.form()
    school_class.school_term_id = int(form.get("school_term_id", school_class.school_term_id))
    school_class.department_id = int(form.get("department_id", school_class.department_id))
    school_class.coddis = str(form.get("coddis", school_class.coddis)).strip().upper()
    school_class.nomdis = str(form.get("nomdis", school_class.nomdis)).strip()
    school_class.codtur = str(form.get("codtur", school_class.codtur)).strip()
    school_class.tiptur = str(form.get("tiptur", school_class.tiptur or "Teórica")).strip()

    dtainitur_str = form.get("dtainitur")
    dtafimtur_str = form.get("dtafimtur")
    school_class.dtainitur = datetime.strptime(dtainitur_str, "%Y-%m-%d") if dtainitur_str else None
    school_class.dtafimtur = datetime.strptime(dtafimtur_str, "%Y-%m-%d") if dtafimtur_str else None

    # Atualiza docentes
    instructor_ids = [int(i) for i in form.getlist("instructor_ids") if i]
    insts = db.query(Instructor).filter(Instructor.id.in_(instructor_ids)).all()
    school_class.instructors = insts

    # Adiciona novo horário se preenchido
    diasmnocp = str(form.get("diasmnocp", "")).strip()
    horent = str(form.get("horent", "")).strip()
    horsai = str(form.get("horsai", "")).strip()

    if diasmnocp and horent and horsai:
        schedule = db.query(ClassSchedule).filter(
            ClassSchedule.diasmnocp == diasmnocp,
            ClassSchedule.horent == horent,
            ClassSchedule.horsai == horsai
        ).first()
        if not schedule:
            schedule = ClassSchedule(diasmnocp=diasmnocp, horent=horent, horsai=horsai)
            db.add(schedule)
            db.flush()
        if schedule not in school_class.class_schedules:
            school_class.class_schedules.append(schedule)

    db.commit()
    return RedirectResponse(
        url=f"/schoolclasses/{school_class.id}?msg=Turma+atualizada+com+sucesso!&type=success",
        status_code=303
    )

@router.post("/{class_id}/delete")
def delete_class(class_id: int, request: Request, db: Session = Depends(get_db)):
    school_class = db.query(SchoolClass).filter(SchoolClass.id == class_id).first()
    if not school_class:
        raise HTTPException(status_code=404, detail="Turma não encontrada.")

    cod = f"{school_class.coddis} (Turma {school_class.codtur})"
    db.delete(school_class)
    db.commit()

    return RedirectResponse(
        url=f"/schoolclasses?msg=Turma+{cod}+excluída+com+sucesso.&type=info",
        status_code=303
    )
