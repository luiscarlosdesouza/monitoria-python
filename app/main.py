import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from app.config import settings
from app.database import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicialização do banco de dados ao iniciar o servidor
    init_db()
    yield

app = FastAPI(
    title=settings.APP_NAME,
    description="Sistema de Monitoria - IME/USP portado para FastAPI e SQLAlchemy",
    version="1.0.0",
    lifespan=lifespan
)

# Configuração de sessão (cookies criptografados para auth)
app.add_middleware(
    SessionMiddleware, 
    secret_key=settings.SECRET_KEY, 
    session_cookie="monitoria_session",
    max_age=14 * 24 * 3600  # 14 dias
)

# Arquivos estáticos e templates
static_dir = os.path.join(os.path.dirname(__file__), "static")
templates_dir = os.path.join(os.path.dirname(__file__), "templates")

if not os.path.exists(static_dir):
    os.makedirs(static_dir, exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=templates_dir)

from app.services.permissions import get_user_permissions, normalize_role
templates.env.globals["get_user_permissions"] = get_user_permissions
templates.env.globals["normalize_role"] = normalize_role

from app.routers import auth, school_terms, school_classes, requisitions, enrollments, admin, users

app.include_router(auth.router)
app.include_router(school_terms.router)
app.include_router(school_classes.router)
app.include_router(requisitions.router)
app.include_router(enrollments.router)
app.include_router(admin.router)
app.include_router(users.router)

@app.get("/health")
def health():
    return {"status": "ok", "app": settings.APP_NAME, "env": settings.ENVIRONMENT}

@app.get("/")
def home(request: Request):
    user = request.session.get("user")
    perms = get_user_permissions(user)
    return templates.TemplateResponse(
        request=request, 
        name="index.html", 
        context={
            "user": user,
            "perms": perms,
            "app_name": settings.APP_NAME
        }
    )

