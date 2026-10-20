import os
import shutil
import time
from typing import Optional, List
from fastapi import APIRouter, Request, Depends, Form, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.enrollment import Enrollment
from app.models.school_class import SchoolClass
from app.models.school_term import SchoolTerm
from app.models.department import Department
from app.models.student import Student
from app.models.school_record import SchoolRecord
from app.models.instructor import Instructor

router = APIRouter(prefix="/enrollments", tags=["Inscrições de Alunos"])
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "..", "templates"))

# Diretório para armazenamento dos históricos escolares
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "static", "uploads", "historicos")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.get("", response_class=HTMLResponse)
def list_enrollments(
    request: Request,
    term_id: Optional[int] = None,
    department_id: Optional[int] = None,
    school_class_id: Optional[int] = None,
    voluntario: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    user = request.session.get("user")
    
    # Inscrições do usuário logado (se for aluno ou tiver codpes)
    my_enrollments = []
    current_student = None
    if user and user.get("codpes"):
        current_student = db.query(Student).filter(Student.codpes == str(user["codpes"])).first()
        if current_student:
            my_enrollments = db.query(Enrollment).options(
                joinedload(Enrollment.school_class).joinedload(SchoolClass.department),
                joinedload(Enrollment.school_class).joinedload(SchoolClass.school_term),
                joinedload(Enrollment.school_class).joinedload(SchoolClass.class_schedules),
                joinedload(Enrollment.school_class).joinedload(SchoolClass.instructors)
            ).filter(Enrollment.student_id == current_student.id).all()

    # Consulta geral com filtros
    query = db.query(Enrollment).options(
        joinedload(Enrollment.student),
        joinedload(Enrollment.school_class).joinedload(SchoolClass.department),
        joinedload(Enrollment.school_class).joinedload(SchoolClass.school_term),
        joinedload(Enrollment.school_class).joinedload(SchoolClass.instructors)
    )

    if term_id:
        query = query.join(SchoolClass).filter(SchoolClass.school_term_id == term_id)
    if department_id:
        if not term_id:
            query = query.join(SchoolClass)
        query = query.filter(SchoolClass.department_id == department_id)
    if school_class_id:
        query = query.filter(Enrollment.school_class_id == school_class_id)
    if voluntario is not None and voluntario != "":
        is_voluntario = (voluntario == "1" or voluntario.lower() == "true")
        query = query.filter(Enrollment.voluntario == is_voluntario)
    if search:
        search_pattern = f"%{search}%"
        query = query.join(Student).filter(
            (Student.nompes.ilike(search_pattern)) | (Student.codpes.ilike(search_pattern))
        )

    enrollments = query.order_by(Enrollment.created_at.desc()).all()

    # Dados para filtros
    terms = db.query(SchoolTerm).order_by(SchoolTerm.year.desc(), SchoolTerm.period.desc()).all()
    departments = db.query(Department).order_by(Department.nomabvset).all()

    # Estatísticas
    total_enrollments = len(enrollments)
    total_students = len(set(e.student_id for e in enrollments))
    total_voluntarios = sum(1 for e in enrollments if e.voluntario)
    total_bolsistas = total_enrollments - total_voluntarios

    return templates.TemplateResponse(
        request=request,
        name="enrollments/index.html",
        context={
            "user": user,
            "enrollments": enrollments,
            "my_enrollments": my_enrollments,
            "current_student": current_student,
            "terms": terms,
            "departments": departments,
            "selected_term_id": term_id,
            "selected_department_id": department_id,
            "selected_school_class_id": school_class_id,
            "selected_voluntario": voluntario,
            "search": search or "",
            "stats": {
                "total_enrollments": total_enrollments,
                "total_students": total_students,
                "total_voluntarios": total_voluntarios,
                "total_bolsistas": total_bolsistas
            }
        }
    )

@router.get("/create", response_class=HTMLResponse)
def create_enrollment_form(
    request: Request,
    term_id: Optional[int] = None,
    class_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    user = request.session.get("user")
    if not user:
        return templates.TemplateResponse(
            request=request,
            name="enrollments/login_required.html",
            context={"user": None}
        )

    # Identifica ou inicializa o estudante no banco
    codpes = str(user.get("codpes"))
    student = db.query(Student).filter(Student.codpes == codpes).first()
    if not student:
        student = Student(
            codpes=codpes,
            nompes=user.get("name", f"Aluno {codpes}"),
            codema=user.get("email")
        )
        db.add(student)
        db.commit()
        db.refresh(student)

    # Período letivo atual (mais recente ou selecionado)
    if term_id:
        active_term = db.query(SchoolTerm).filter(SchoolTerm.id == term_id).first()
    else:
        active_term = db.query(SchoolTerm).filter(SchoolTerm.status == "Aberto").order_by(SchoolTerm.year.desc()).first()
        if not active_term:
            active_term = db.query(SchoolTerm).order_by(SchoolTerm.year.desc()).first()

    # Conta quantas inscrições o aluno já possui no período
    term_classes_ids = []
    my_term_enrollments_count = 0
    if active_term:
        term_classes = db.query(SchoolClass.id).filter(SchoolClass.school_term_id == active_term.id).all()
        term_classes_ids = [c[0] for c in term_classes]
        my_term_enrollments_count = db.query(Enrollment).filter(
            Enrollment.student_id == student.id,
            Enrollment.school_class_id.in_(term_classes_ids)
        ).count()

    # Lista de turmas abertas
    query_classes = db.query(SchoolClass).options(
        joinedload(SchoolClass.department),
        joinedload(SchoolClass.school_term),
        joinedload(SchoolClass.instructors),
        joinedload(SchoolClass.class_schedules),
        joinedload(SchoolClass.requisitions)
    )
    if active_term:
        query_classes = query_classes.filter(SchoolClass.school_term_id == active_term.id)
    
    classes = query_classes.order_by(SchoolClass.coddis, SchoolClass.codtur).all()

    # Identifica turmas onde o aluno já se inscreveu
    already_enrolled_class_ids = set()
    if student:
        current_enrs = db.query(Enrollment.school_class_id).filter(Enrollment.student_id == student.id).all()
        already_enrolled_class_ids = {e[0] for e in current_enrs}

    # Verifica se já tem histórico escolar enviado para este período
    existing_record = None
    if active_term and student:
        existing_record = db.query(SchoolRecord).filter(
            SchoolRecord.student_id == student.id,
            SchoolRecord.schoolterm_id == active_term.id
        ).first()

    return templates.TemplateResponse(
        request=request,
        name="enrollments/create.html",
        context={
            "user": user,
            "student": student,
            "active_term": active_term,
            "classes": classes,
            "selected_class_id": class_id,
            "already_enrolled_class_ids": already_enrolled_class_ids,
            "my_enrollments_count": my_term_enrollments_count,
            "max_enrollments": active_term.max_enrollments if active_term else 3,
            "existing_record": existing_record
        }
    )

@router.post("/create")
async def create_enrollment(
    request: Request,
    db: Session = Depends(get_db)
):
    user = request.session.get("user")
    if not user:
        return RedirectResponse(
            url="/enrollments?msg=Faça+login+com+a+Senha+Única+para+se+inscrever.&type=danger",
            status_code=303
        )

    form = await request.form()
    school_class_id = int(form.get("school_class_id", 0))
    voluntario = form.get("voluntario") in ["true", "True", "1", "on"]
    disponibilidade_diurno = form.get("disponibilidade_diurno") in ["true", "True", "1", "on"]
    disponibilidade_noturno = form.get("disponibilidade_noturno") in ["true", "True", "1", "on"]
    preferencia_horario = form.get("preferencia_horario")
    observacoes = form.get("observacoes")

    if not school_class_id:
        return RedirectResponse(
            url="/enrollments/create?msg=Selecione+uma+turma+para+se+inscrever.&type=danger",
            status_code=303
        )

    # Garante o aluno no banco
    codpes = str(user.get("codpes"))
    student = db.query(Student).filter(Student.codpes == codpes).first()
    if not student:
        student = Student(
            codpes=codpes,
            nompes=user.get("name", f"Aluno {codpes}"),
            codema=user.get("email")
        )
        db.add(student)
        db.flush()

    # Busca a turma
    school_class = db.query(SchoolClass).filter(SchoolClass.id == school_class_id).first()
    if not school_class:
        raise HTTPException(status_code=404, detail="Turma não encontrada.")

    # Verifica limite máximo de inscrições no período
    term = school_class.school_term
    if term:
        term_class_ids = [c.id for c in db.query(SchoolClass.id).filter(SchoolClass.school_term_id == term.id).all()]
        current_count = db.query(Enrollment).filter(
            Enrollment.student_id == student.id,
            Enrollment.school_class_id.in_(term_class_ids),
            Enrollment.school_class_id != school_class_id
        ).count()

        if current_count >= term.max_enrollments:
            return RedirectResponse(
                url=f"/enrollments?msg=Você+já+atingiu+o+limite+máximo+de+{term.max_enrollments}+inscrições+para+este+período.&type=warning",
                status_code=303
            )

    # Trata upload opcional do histórico escolar (PDF)
    history_file = form.get("history_file")
    if history_file and hasattr(history_file, "filename") and history_file.filename:
        filename = history_file.filename
        ext = os.path.splitext(filename)[1].lower()
        if ext in [".pdf"]:
            safe_name = f"historico_{student.codpes}_{term.id if term else '0'}_{int(time.time())}.pdf"
            file_destination = os.path.join(UPLOAD_DIR, safe_name)
            
            with open(file_destination, "wb") as buffer:
                content = await history_file.read()
                buffer.write(content)

            # Registra no SchoolRecord
            if term:
                rec = db.query(SchoolRecord).filter(
                    SchoolRecord.student_id == student.id,
                    SchoolRecord.schoolterm_id == term.id
                ).first()
                if rec:
                    rec.file_path = f"/static/uploads/historicos/{safe_name}"
                else:
                    rec = SchoolRecord(
                        student_id=student.id,
                        schoolterm_id=term.id,
                        file_path=f"/static/uploads/historicos/{safe_name}"
                    )
                    db.add(rec)

    # Cria ou atualiza a inscrição
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
        new_enr = Enrollment(
            school_class_id=school_class_id,
            student_id=student.id,
            voluntario=voluntario,
            disponibilidade_diurno=disponibilidade_diurno,
            disponibilidade_noturno=disponibilidade_noturno,
            preferencia_horario=preferencia_horario,
            observacoes=observacoes
        )
        db.add(new_enr)

    db.commit()
    return RedirectResponse(
        url="/enrollments?msg=Inscrição+realizada+com+sucesso!&type=success",
        status_code=303
    )

@router.get("/{enrollment_id}", response_class=HTMLResponse)
def view_enrollment(enrollment_id: int, request: Request, db: Session = Depends(get_db)):
    enr = db.query(Enrollment).options(
        joinedload(Enrollment.student).joinedload(Student.school_records),
        joinedload(Enrollment.school_class).joinedload(SchoolClass.department),
        joinedload(Enrollment.school_class).joinedload(SchoolClass.school_term),
        joinedload(Enrollment.school_class).joinedload(SchoolClass.class_schedules),
        joinedload(Enrollment.school_class).joinedload(SchoolClass.instructors)
    ).filter(Enrollment.id == enrollment_id).first()

    if not enr:
        raise HTTPException(status_code=404, detail="Inscrição não encontrada.")

    # Localiza o histórico escolar vinculado ao aluno e período desta turma
    term_id = enr.school_class.school_term_id
    school_record = None
    if term_id and enr.student:
        school_record = db.query(SchoolRecord).filter(
            SchoolRecord.student_id == enr.student.id,
            SchoolRecord.schoolterm_id == term_id
        ).first()

    user = request.session.get("user")

    return templates.TemplateResponse(
        request=request,
        name="enrollments/show.html",
        context={
            "user": user,
            "enr": enr,
            "school_record": school_record
        }
    )

@router.get("/{enrollment_id}/edit", response_class=HTMLResponse)
def edit_enrollment_form(enrollment_id: int, request: Request, db: Session = Depends(get_db)):
    enr = db.query(Enrollment).options(
        joinedload(Enrollment.student),
        joinedload(Enrollment.school_class).joinedload(SchoolClass.department),
        joinedload(Enrollment.school_class).joinedload(SchoolClass.school_term)
    ).filter(Enrollment.id == enrollment_id).first()

    if not enr:
        raise HTTPException(status_code=404, detail="Inscrição não encontrada.")

    user = request.session.get("user")

    # Verifica permissão: apenas o próprio aluno ou admin pode editar
    if user and str(user.get("codpes")) != str(enr.student.codpes) and user.get("role") != "admin":
        return RedirectResponse(
            url="/enrollments?msg=Você+só+pode+editar+suas+próprias+inscrições.&type=danger",
            status_code=303
        )

    return templates.TemplateResponse(
        request=request,
        name="enrollments/edit.html",
        context={
            "user": user,
            "enr": enr
        }
    )

@router.post("/{enrollment_id}/edit")
async def edit_enrollment(enrollment_id: int, request: Request, db: Session = Depends(get_db)):
    enr = db.query(Enrollment).filter(Enrollment.id == enrollment_id).first()
    if not enr:
        raise HTTPException(status_code=404, detail="Inscrição não encontrada.")

    user = request.session.get("user")
    student = enr.student
    if user and str(user.get("codpes")) != str(student.codpes) and user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Não autorizado a alterar esta inscrição.")

    form = await request.form()
    enr.voluntario = form.get("voluntario") in ["true", "True", "1", "on"]
    enr.disponibilidade_diurno = form.get("disponibilidade_diurno") in ["true", "True", "1", "on"]
    enr.disponibilidade_noturno = form.get("disponibilidade_noturno") in ["true", "True", "1", "on"]
    enr.preferencia_horario = form.get("preferencia_horario")
    enr.observacoes = form.get("observacoes")

    db.commit()
    return RedirectResponse(
        url=f"/enrollments/{enr.id}?msg=Inscrição+atualizada+com+sucesso!&type=success",
        status_code=303
    )

@router.post("/{enrollment_id}/delete")
def delete_enrollment(enrollment_id: int, request: Request, db: Session = Depends(get_db)):
    enr = db.query(Enrollment).filter(Enrollment.id == enrollment_id).first()
    if not enr:
        raise HTTPException(status_code=404, detail="Inscrição não encontrada.")

    user = request.session.get("user")
    student = enr.student
    if user and str(user.get("codpes")) != str(student.codpes) and user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Não autorizado a cancelar esta inscrição.")

    db.delete(enr)
    db.commit()
    return RedirectResponse(
        url="/enrollments?msg=Inscrição+cancelada+com+sucesso.&type=info",
        status_code=303
    )
