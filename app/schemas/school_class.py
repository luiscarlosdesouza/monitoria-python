from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.schemas.department import DepartmentResponse

class ClassScheduleSchema(BaseModel):
    id: Optional[int] = None
    diasmnocp: str
    horent: str
    horsai: str

    class Config:
        from_attributes = True

class SchoolClassBase(BaseModel):
    school_term_id: int
    department_id: int
    codtur: str
    tiptur: Optional[str] = None
    nomdis: Optional[str] = None
    coddis: str
    dtainitur: Optional[datetime] = None
    dtafimtur: Optional[datetime] = None

class SchoolClassCreate(SchoolClassBase):
    pass

class SchoolClassResponse(SchoolClassBase):
    id: int
    department: Optional[DepartmentResponse] = None
    class_schedules: List[ClassScheduleSchema] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
