from datetime import datetime
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import (
    Department, Activity, Scholarship, SchoolTerm, SchoolClass, 
    Instructor, Student, Requisition, ClassSchedule, Enrollment,
    MailTemplate
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
            db.flush()

        # 5. Docentes Iniciais (se não existirem)
        dept_mac = db.query(Department).filter(Department.nomabvset == "MAC").first()
        dept_mat = db.query(Department).filter(Department.nomabvset == "MAT").first()
        dept_mae = db.query(Department).filter(Department.nomabvset == "MAE").first()

        inst_data = [
            {"codpes": "7762448", "nompes": "Luis Carlos de Souza", "codema": "luiscarlos@ime.usp.br", "department_id": dept_mac.id if dept_mac else 1},
            {"codpes": "2803642", "nompes": "Prof. Dr. Alfredo Goldman", "codema": "gold@ime.usp.br", "department_id": dept_mac.id if dept_mac else 1},
            {"codpes": "5085616", "nompes": "Profa. Dra. Cristina Gomes Fernandes", "codema": "cris@ime.usp.br", "department_id": dept_mac.id if dept_mac else 1},
            {"codpes": "1002001", "nompes": "Prof. Dr. Severino Toscano", "codema": "toscano@ime.usp.br", "department_id": dept_mat.id if dept_mat else 2},
            {"codpes": "1002002", "nompes": "Profa. Dra. Nancy Garcia", "codema": "nancy@ime.usp.br", "department_id": dept_mae.id if dept_mae else 3},
        ]
        for item in inst_data:
            if not db.query(Instructor).filter(Instructor.codpes == item["codpes"]).first():
                db.add(Instructor(**item))
        db.flush()

        # 6. Turmas Iniciais (se não existirem)
        if db.query(SchoolClass).count() == 0 and term:
            classes_data = [
                {
                    "school_term_id": term.id,
                    "department_id": dept_mac.id if dept_mac else 1,
                    "coddis": "MAC0110",
                    "nomdis": "Introdução à Computação",
                    "codtur": "45",
                    "tiptur": "Teórica",
                    "dtainitur": datetime(2026, 2, 23),
                    "dtafimtur": datetime(2026, 7, 10),
                },
                {
                    "school_term_id": term.id,
                    "department_id": dept_mac.id if dept_mac else 1,
                    "coddis": "MAC0110",
                    "nomdis": "Introdução à Computação",
                    "codtur": "46",
                    "tiptur": "Teórica/Prática",
                    "dtainitur": datetime(2026, 2, 23),
                    "dtafimtur": datetime(2026, 7, 10),
                },
                {
                    "school_term_id": term.id,
                    "department_id": dept_mac.id if dept_mac else 1,
                    "coddis": "MAC0121",
                    "nomdis": "Estruturas de Dados",
                    "codtur": "04",
                    "tiptur": "Teórica",
                    "dtainitur": datetime(2026, 2, 23),
                    "dtafimtur": datetime(2026, 7, 10),
                },
                {
                    "school_term_id": term.id,
                    "department_id": dept_mat.id if dept_mat else 2,
                    "coddis": "MAT0111",
                    "nomdis": "Cálculo Diferencial e Integral I",
                    "codtur": "21",
                    "tiptur": "Teórica",
                    "dtainitur": datetime(2026, 2, 23),
                    "dtafimtur": datetime(2026, 7, 10),
                },
                {
                    "school_term_id": term.id,
                    "department_id": dept_mae.id if dept_mae else 3,
                    "coddis": "MAE0119",
                    "nomdis": "Introdução à Probabilidade e Estatística I",
                    "codtur": "01",
                    "tiptur": "Teórica",
                    "dtainitur": datetime(2026, 2, 23),
                    "dtafimtur": datetime(2026, 7, 10),
                },
            ]
            for c in classes_data:
                sc = SchoolClass(**c)
                db.add(sc)
            db.flush()

            # Vincula docentes às turmas
            inst_gold = db.query(Instructor).filter(Instructor.codpes == "2803642").first()
            inst_cris = db.query(Instructor).filter(Instructor.codpes == "5085616").first()
            inst_toscano = db.query(Instructor).filter(Instructor.codpes == "1002001").first()

            class_mac110 = db.query(SchoolClass).filter(SchoolClass.coddis == "MAC0110", SchoolClass.codtur == "45").first()
            class_mac121 = db.query(SchoolClass).filter(SchoolClass.coddis == "MAC0121").first()
            class_mat111 = db.query(SchoolClass).filter(SchoolClass.coddis == "MAT0111").first()

            if class_mac110 and inst_gold:
                class_mac110.instructors.append(inst_gold)
            if class_mac121 and inst_cris:
                class_mac121.instructors.append(inst_cris)
            if class_mat111 and inst_toscano:
                class_mat111.instructors.append(inst_toscano)

        # 7. Modelos de E-mail Padrão (se não existirem)
        if db.query(MailTemplate).count() == 0:
            templates_data = [
                {
                    "name": "Resultado da Seleção",
                    "mail_class": "SelectionResultMail",
                    "description": "Notificação enviada ao candidato informando o resultado da seleção e atribuição de bolsa.",
                    "sending_frequency": "Manual",
                    "active": True,
                    "subject": "[Monitoria IME-USP] Resultado do Processo Seletivo de Monitoria",
                    "body": "Prezado(a) {nome},\n\nParabéns! Você foi selecionado(a) como monitor(a) para a turma {disciplina} ({turma}) no período letivo {periodo}.\n\nModalidade: {modalidade}\n\nFavor comparecer ao departamento para orientações iniciais.\n\nAtenciosamente,\nComissão de Graduação - IME-USP"
                },
                {
                    "name": "Lembrete de Frequência Mensal",
                    "mail_class": "MonthlyFrequencyMail",
                    "description": "Lembrete mensal enviado aos docentes para atestar a frequência dos monitores bolsistas.",
                    "sending_frequency": "Mensal",
                    "active": True,
                    "subject": "[Monitoria IME-USP] Lembrete de Atesto de Frequência de Monitores",
                    "body": "Prezado(a) Professor(a),\n\nInformamos que o período para atesto da frequência mensal dos monitores da sua turma {disciplina} está aberto no sistema.\n\nAcesse o sistema em https://monitoria.ime.usp.br para validar a frequência.\n\nAtenciosamente,\nSecretaria de Graduação - IME-USP"
                }
            ]
            for tmpl in templates_data:
                db.add(MailTemplate(**tmpl))

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
