from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models.school_term import SchoolTerm
from app.models.school_class import SchoolClass
from fastapi.templating import Jinja2Templates
import os

router = APIRouter(prefix="/schoolterms", tags=["Períodos Letivos"])
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "..", "templates"))

@router.get("", response_class=HTMLResponse)
def list_terms(request: Request, db: Session = Depends(get_db)):
    terms = db.query(SchoolTerm).order_by(SchoolTerm.year.desc(), SchoolTerm.period.desc()).all()
    user = request.session.get("user")
    return templates.TemplateResponse(
        request=request,
        name="school_terms/index.html",
        context={"user": user, "terms": terms}
    )

@router.get("/create", response_class=HTMLResponse)
def create_term_form(request: Request):
    user = request.session.get("user")
    return templates.TemplateResponse(
        request=request,
        name="school_terms/create.html",
        context={"user": user}
    )

@router.post("/create")
def create_term(
    year: int = Form(...),
    period: str = Form(...),
    status: str = Form("Aberto"),
    max_enrollments: int = Form(3),
    evaluation_period: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    existing = db.query(SchoolTerm).filter(SchoolTerm.year == year, SchoolTerm.period == period).first()
    if existing:
        raise HTTPException(status_code=400, detail="Este período letivo já está cadastrado.")

    term = SchoolTerm(
        year=year,
        period=period,
        status=status,
        max_enrollments=max_enrollments,
        evaluation_period=evaluation_period
    )
    db.add(term)
    db.commit()
    return RedirectResponse(url="/schoolterms", status_code=303)

@router.get("/{term_id}", response_class=HTMLResponse)
def term_details(term_id: int, request: Request, db: Session = Depends(get_db)):
    term = db.query(SchoolTerm).filter(SchoolTerm.id == term_id).first()
    if not term:
        raise HTTPException(status_code=404, detail="Período não encontrado.")
    classes = db.query(SchoolClass).filter(SchoolClass.school_term_id == term_id).all()
    user = request.session.get("user")
    return templates.TemplateResponse(
        request=request,
        name="school_terms/show.html",
        context={"user": user, "term": term, "classes": classes}
    )
