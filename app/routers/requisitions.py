from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional, List
from app.database import get_db
from app.models.requisition import Requisition
from app.models.school_class import SchoolClass
from app.models.instructor import Instructor
from app.models.activity import Activity
from fastapi.templating import Jinja2Templates
import os

router = APIRouter(prefix="/requisitions", tags=["Pedidos de Monitoria"])
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "..", "templates"))

@router.get("", response_class=HTMLResponse)
def list_requisitions(request: Request, db: Session = Depends(get_db)):
    requisitions = db.query(Requisition).all()
    user = request.session.get("user")
    return templates.TemplateResponse(
        request=request,
        name="requisitions/index.html",
        context={"user": user, "requisitions": requisitions}
    )

@router.get("/create", response_class=HTMLResponse)
def create_requisition_form(request: Request, db: Session = Depends(get_db)):
    classes = db.query(SchoolClass).all()
    instructors = db.query(Instructor).all()
    activities = db.query(Activity).all()
    user = request.session.get("user")
    return templates.TemplateResponse(
        request=request,
        name="requisitions/create.html",
        context={
            "user": user, 
            "classes": classes, 
            "instructors": instructors,
            "activities": activities
        }
    )

@router.post("/create")
def create_requisition(
    school_class_id: int = Form(...),
    instructor_id: int = Form(...),
    requested_number: int = Form(1),
    priority: str = Form("Normal"),
    comments: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    existing = db.query(Requisition).filter(
        Requisition.school_class_id == school_class_id,
        Requisition.instructor_id == instructor_id
    ).first()
    
    if existing:
        existing.requested_number = requested_number
        existing.priority = priority
        existing.comments = comments
    else:
        req = Requisition(
            school_class_id=school_class_id,
            instructor_id=instructor_id,
            requested_number=requested_number,
            priority=priority,
            comments=comments
        )
        db.add(req)

    db.commit()
    return RedirectResponse(url="/requisitions", status_code=303)
