from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

# Configuração flexível de engine (SQLite local ou MySQL/MariaDB em produção)
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args=connect_args
    )
else:
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=3600
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

import time
import logging

logger = logging.getLogger("database")

def init_db(max_retries: int = 15, retry_delay: int = 2):
    # Import all models to ensure they are registered with Base metadata
    import app.models  # noqa: F401
    
    for attempt in range(1, max_retries + 1):
        try:
            Base.metadata.create_all(bind=engine)
            try:
                from app.seeds import run_seeds
                run_seeds()
            except Exception as se:
                logger.warning(f"Aviso ao executar seeds automáticos: {se}")
            logger.info("Banco de dados e modelos inicializados com sucesso!")
            break
        except Exception as e:
            if attempt == max_retries:
                logger.error(f"Falha definitiva ao conectar ao banco de dados: {e}")
                raise e
            logger.warning(f"Aguardando banco de dados (tentativa {attempt}/{max_retries})...")
            time.sleep(retry_delay)
