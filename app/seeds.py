from datetime import datetime
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import (
    Department, Activity, Scholarship, SchoolTerm, SchoolClass, 
    Instructor, Student, Requisition, ClassSchedule, Enrollment
)

def run_seeds():
    """
    Insere dados padrão (departamentos IME, atividades e bolsas) se ainda não existirem.
    NÃO chama init_db() para evitar recursão infinita.
    """
    db: Session = SessionLocal()
    try:
        # 1. Departamentos do IME
        depts_data = [
            {"codset": 5000, "nomabvset": "MAC", "nomset": "Departamento de Ciência da Computação"},
            {"codset": 5001, "nomabvset": "MAT", "nomset": "Departamento de Matemática"},
            {"codset": 5002, "nomabvset": "MAE", "nomset": "Departamento de Estatística"},
            {"codset": 5003, "nomabvset": "MAP", "nomset": "Departamento de Matemática Aplicada"},
        ]
        for d in depts_data:
            if not db.query(Department).filter(Department.codset == d["codset"]).first():
                db.add(Department(**d))

        # 2. Atividades
        activities = [
            "Atendimento a alunos em dúvidas teóricas e práticas",
            "Correção de listas de exercícios e trabalhos",
            "Plantão de dúvidas presencial e remoto",
            "Fiscalização e auxílio na aplicação de provas",
            "Apoio em aulas de laboratório de informática"
        ]
        for a in activities:
            if not db.query(Activity).filter(Activity.description == a).first():
                db.add(Activity(description=a))

        # 3. Bolsas
        scholarships = ["PEEG", "PAE", "PAPI", "Pós do IME", "Voluntário (Sem bolsa)"]
        for s in scholarships:
            if not db.query(Scholarship).filter(Scholarship.name == s).first():
                db.add(Scholarship(name=s))

        # 4. Período Letivo Inicial (2026 - 1º Semestre)
        term = db.query(SchoolTerm).filter(SchoolTerm.year == 2026, SchoolTerm.period == "1º Semestre").first()
        if not term:
            term = SchoolTerm(
                year=2026,
                period="1º Semestre",
                status="Aberto",
                max_enrollments=3,
                started_at=datetime(2026, 2, 23),
                finished_at=datetime(2026, 7, 10),
                start_date_requisitions=datetime(2026, 1, 15),
                end_date_requisitions=datetime(2026, 2, 20),
                start_date_enrollments=datetime(2026, 2, 1),
                end_date_enrollments=datetime(2026, 2, 28)
            )
            db.add(term)

        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    from app.database import init_db
    init_db()
    run_seeds()
    print("Seeds executados manualmente com sucesso!")
