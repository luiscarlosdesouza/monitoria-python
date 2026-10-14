"""
Script de Migração de Dados do Banco Legado (MySQL carapicuiba) para o Novo Banco (FastAPI/SQLAlchemy).
Uso:
    python -m scripts.migrate_legacy_data
"""
import sys
import pymysql
from pymysql.cursors import DictCursor
from sqlalchemy.orm import Session
from app.config import settings
from app.database import SessionLocal, init_db
from app.models import (
    User, SchoolTerm, Department, Course, Instructor, ClassSchedule,
    SchoolClass, Activity, Requisition, Student, SchoolRecord,
    Enrollment, Recommendation, Selection, Frequency, Scholarship,
    SelfEvaluation, InstructorEvaluation, MailTemplate
)

def get_legacy_connection():
    print(f"Conectando ao banco legado {settings.LEGACY_DB_USERNAME}@{settings.LEGACY_DB_HOST}:{settings.LEGACY_DB_PORT}/{settings.LEGACY_DB_DATABASE}...")
    return pymysql.connect(
        host=settings.LEGACY_DB_HOST,
        port=settings.LEGACY_DB_PORT,
        user=settings.LEGACY_DB_USERNAME,
        password=settings.LEGACY_DB_PASSWORD,
        database=settings.LEGACY_DB_DATABASE,
        charset='utf8mb4',
        cursorclass=DictCursor,
        connect_timeout=10
    )

def migrate():
    try:
        legacy_conn = get_legacy_connection()
    except Exception as e:
        print(f"\n[AVISO] Não foi possível conectar ao banco legado: {e}")
        print("Certifique-se de que o host 'carapicuiba' está acessível (VPN da USP ativa ou rede interna do IME).")
        return

    init_db()
    db: Session = SessionLocal()
    cursor = legacy_conn.cursor()

    try:
        # 1. Departamentos
        print("\n--- Migrando Departamentos ---")
        cursor.execute("SELECT * FROM departments")
        for row in cursor.fetchall():
            if not db.query(Department).filter(Department.id == row['id']).first():
                db.add(Department(
                    id=row['id'],
                    codset=row['codset'],
                    nomabvset=row['nomabvset'],
                    nomset=row['nomset'],
                    sglund=row.get('sglund', 'IME'),
                    nomund=row.get('nomund', 'Instituto de Matemática e Estatística'),
                    created_at=row.get('created_at'),
                    updated_at=row.get('updated_at')
                ))
        db.commit()
        print("Departamentos migrados.")

        # 2. Períodos Letivos
        print("\n--- Migrando Períodos Letivos ---")
        cursor.execute("SELECT * FROM school_terms")
        for row in cursor.fetchall():
            if not db.query(SchoolTerm).filter(SchoolTerm.id == row['id']).first():
                db.add(SchoolTerm(
                    id=row['id'],
                    year=row['year'],
                    period=row['period'],
                    status=row.get('status', 'Aberto'),
                    max_enrollments=row.get('max_enrollments', 3),
                    started_at=row.get('started_at'),
                    finished_at=row.get('finished_at'),
                    start_date_requisitions=row.get('start_date_requisitions'),
                    end_date_requisitions=row.get('end_date_requisitions'),
                    start_date_enrollments=row.get('start_date_enrollments'),
                    end_date_enrollments=row.get('end_date_enrollments'),
                    created_at=row.get('created_at'),
                    updated_at=row.get('updated_at')
                ))
        db.commit()
        print("Períodos letivos migrados.")

        # 3. Disciplinas e Turmas
        print("\n--- Migrando Turmas ---")
        cursor.execute("SELECT * FROM school_classes")
        for row in cursor.fetchall():
            if not db.query(SchoolClass).filter(SchoolClass.id == row['id']).first():
                db.add(SchoolClass(
                    id=row['id'],
                    school_term_id=row['school_term_id'],
                    department_id=row['department_id'],
                    codtur=row['codtur'],
                    tiptur=row.get('tiptur'),
                    nomdis=row.get('nomdis'),
                    coddis=row['coddis'],
                    dtainitur=row.get('dtainitur'),
                    dtafimtur=row.get('dtafimtur'),
                    created_at=row.get('created_at'),
                    updated_at=row.get('updated_at')
                ))
        db.commit()
        print("Turmas migradas com sucesso.")

        print("\n=== Migração concluída com sucesso! ===")
    except Exception as e:
        db.rollback()
        print(f"Erro durante a migração: {e}")
    finally:
        cursor.close()
        legacy_conn.close()
        db.close()

if __name__ == "__main__":
    migrate()
