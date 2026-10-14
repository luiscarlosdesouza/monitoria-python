from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models.school_class import SchoolClass
from app.models.school_term import SchoolTerm
from app.models.department import Department
from fastapi.templating import Jinja2Templates
import os

router = APIRouter(prefix="/schoolclasses", tags=["Turmas"])
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "..", "templates"))

@router.get("", response_class=HTMLResponse)
def list_classes(
    request: Request,
    term_id: Optional[int] = None,
    department_id: Optional[int] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(SchoolClass)
    
    if term_id:
        query = query.filter(SchoolClass.school_term_id == term_id)
    if department_id:
        query = query.filter(SchoolClass.department_id == department_id)
    if search:
        query = query.filter(
            (SchoolClass.coddis.ilike(f"%{search}%")) | 
            (SchoolClass.nomdis.ilike(f"%{search}%")) |
            (SchoolClass.codtur.ilike(f"%{search}%"))
        )

    classes = query.order_by(SchoolClass.coddis.asc(), SchoolClass.codtur.asc()).all()
    terms = db.query(SchoolTerm).order_by(SchoolTerm.year.desc(), SchoolTerm.period.desc()).all()
    departments = db.query(Department).order_by(Department.nomabvset.asc()).all()
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
            "search": search
        }
    )

@router.get("/{class_id}", response_class=HTMLResponse)
def class_details(class_id: int, request: Request, db: Session = Depends(get_db)):
    school_class = db.query(SchoolClass).filter(SchoolClass.id == class_id).first()
    if not school_class:
        raise HTTPException(status_code=404, detail="Turma não encontrada.")

    user = request.session.get("user")
    return templates.TemplateResponse(
        request=request,
        name="school_classes/show.html",
        context={
            "user": user,
            "school_class": school_class
        }
    )
