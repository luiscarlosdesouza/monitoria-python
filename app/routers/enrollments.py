from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models.enrollment import Enrollment
from app.models.school_class import SchoolClass
from app.models.student import Student
from fastapi.templating import Jinja2Templates
import os

router = APIRouter(prefix="/enrollments", tags=["Inscrições de Alunos"])
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "..", "templates"))

@router.get("", response_class=HTMLResponse)
def list_enrollments(request: Request, db: Session = Depends(get_db)):
    enrollments = db.query(Enrollment).all()
    user = request.session.get("user")
    return templates.TemplateResponse(
        request=request,
        name="enrollments/index.html",
        context={"user": user, "enrollments": enrollments}
    )

@router.get("/create", response_class=HTMLResponse)
def create_enrollment_form(request: Request, db: Session = Depends(get_db)):
    classes = db.query(SchoolClass).all()
    user = request.session.get("user")
    return templates.TemplateResponse(
        request=request,
        name="enrollments/create.html",
        context={"user": user, "classes": classes}
    )

@router.post("/create")
def create_enrollment(
    request: Request,
    school_class_id: int = Form(...),
    voluntario: bool = Form(False),
    disponibilidade_diurno: bool = Form(False),
    disponibilidade_noturno: bool = Form(False),
    preferencia_horario: Optional[str] = Form(None),
    observacoes: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Faça login com a Senha Única USP para se inscrever.")

    codpes = str(user.get("codpes"))
    name = user.get("name")
    email = user.get("email")

    # Garante que o registro de Student existe
    student = db.query(Student).filter(Student.codpes == codpes).first()
    if not student:
        student = Student(codpes=codpes, nompes=name, codema=email)
        db.add(student)
        db.commit()
        db.refresh(student)

    # Verifica se já está inscrito nesta turma
    existing = db.query(Enrollment).filter(
        Enrollment.school_class_id == school_class_id,
        Enrollment.student_id == student.id
    ).first()

    if existing:
        existing.voluntario = voluntario
        existing.disponibilidade_diurno = disponibilidade_diurno
        existing.disponibilidade_noturno = disponibilidade_noturno
        existing.preferencia_horario = preferencia_horario
        existing.observacoes = observacoes
    else:
        enrollment = Enrollment(
            school_class_id=school_class_id,
            student_id=student.id,
            voluntario=voluntario,
            disponibilidade_diurno=disponibilidade_diurno,
            disponibilidade_noturno=disponibilidade_noturno,
            preferencia_horario=preferencia_horario,
            observacoes=observacoes
        )
        db.add(enrollment)

    db.commit()
    return RedirectResponse(url="/enrollments", status_code=303)
