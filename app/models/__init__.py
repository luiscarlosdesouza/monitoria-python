from app.models.user import User
from app.models.school_term import SchoolTerm
from app.models.department import Department
from app.models.course import Course
from app.models.instructor import Instructor, instructor_school_class
from app.models.class_schedule import ClassSchedule, class_schedule_school_class
from app.models.school_class import SchoolClass
from app.models.activity import Activity, activity_requisition
from app.models.requisition import Requisition
from app.models.student import Student
from app.models.school_record import SchoolRecord
from app.models.enrollment import Enrollment
from app.models.recommendation import Recommendation
from app.models.selection import Selection
from app.models.frequency import Frequency
from app.models.scholarship import Scholarship, ModelHasScholarship
from app.models.evaluation import SelfEvaluation, InstructorEvaluation
from app.models.mail_template import MailTemplate

__all__ = [
    "User",
    "SchoolTerm",
    "Department",
    "Course",
    "Instructor",
    "instructor_school_class",
    "ClassSchedule",
    "class_schedule_school_class",
    "SchoolClass",
    "Activity",
    "activity_requisition",
    "Requisition",
    "Student",
    "SchoolRecord",
    "Enrollment",
    "Recommendation",
    "Selection",
    "Frequency",
    "Scholarship",
    "ModelHasScholarship",
    "SelfEvaluation",
    "InstructorEvaluation",
    "MailTemplate",
]
