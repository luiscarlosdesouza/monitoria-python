from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class SchoolTermBase(BaseModel):
    year: int
    period: str
    status: str = "Aberto"
    evaluation_period: Optional[str] = None
    max_enrollments: int = 3
    public_notice_file_path: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    start_date_requisitions: Optional[datetime] = None
    end_date_requisitions: Optional[datetime] = None
    start_date_enrollments: Optional[datetime] = None
    end_date_enrollments: Optional[datetime] = None

class SchoolTermCreate(SchoolTermBase):
    pass

class SchoolTermUpdate(BaseModel):
    year: Optional[int] = None
    period: Optional[str] = None
    status: Optional[str] = None
    evaluation_period: Optional[str] = None
    max_enrollments: Optional[int] = None
    public_notice_file_path: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    start_date_requisitions: Optional[datetime] = None
    end_date_requisitions: Optional[datetime] = None
    start_date_enrollments: Optional[datetime] = None
    end_date_enrollments: Optional[datetime] = None

class SchoolTermResponse(SchoolTermBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
