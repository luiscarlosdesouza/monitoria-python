import logging
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.config import settings
from app.models.user import User
from app.services.usp_oauth import usp_oauth_service

logger = logging.getLogger("auth_router")
router = APIRouter(tags=["Autenticação"])

@router.get("/auth/login")
def login(request: Request):
    """
    Inicia o fluxo OAuth 1.0a da USP.
    """
    callback_url = str(request.base_url).rstrip('/') + "/callback"
    try:
        auth_url, oauth_token, oauth_token_secret = usp_oauth_service.get_request_token(callback_url)
        # Salva o segredo temporário na sessão do usuário
        request.session["oauth_token"] = oauth_token
        request.session["oauth_token_secret"] = oauth_token_secret
        return RedirectResponse(url=auth_url)
    except Exception as e:
        logger.error(f"Erro no handshake OAuth USP: {e}")
        # Em ambiente de desenvolvimento, se a USP não responder, redireciona com mensagem amigável
        if settings.ENVIRONMENT == "development":
            return RedirectResponse(url="/auth/dev-choice")
        raise HTTPException(status_code=500, detail=f"Erro ao conectar com servidor OAuth USP: {str(e)}")

@router.get("/callback")
@router.get("/auth/callback")
def auth_callback(
    request: Request,
    oauth_token: str = None,
    oauth_verifier: str = None,
    db: Session = Depends(get_db)
):
    """
    Callback chamado pela USP com o verifier.
    """
    if not oauth_token or not oauth_verifier:
        raise HTTPException(status_code=400, detail="Tokens de autorização ausentes no retorno da USP.")

    token_secret = request.session.get("oauth_token_secret")
    if not token_secret:
        raise HTTPException(status_code=400, detail="Sessão expirada durante o login. Tente novamente.")

    try:
        user_info = usp_oauth_service.fetch_user_data(
            oauth_token=oauth_token,
            oauth_token_secret=token_secret,
            oauth_verifier=oauth_verifier
        )

        codpes = user_info.get("codpes")
        name = user_info.get("name", "Usuário USP")
        email = user_info.get("email") or f"{codpes}@usp.br"
        from app.models.user import ROLE_ADMINISTRADOR, ROLE_ALUNO, normalize_role
        role = normalize_role(user_info.get("role", ROLE_ALUNO))

        # Localiza ou cadastra o usuário no banco local
        user = db.query(User).filter(User.codpes == codpes).first() if codpes else None
        if not user and email:
            user = db.query(User).filter(User.email == email).first()

        if not user:
            user = User(
                name=name,
                email=email,
                codpes=codpes,
                role=role
            )
            db.add(user)
        else:
            user.name = name
            user.email = email
            # Se estiver na lista de admins, garante Administrador
            if str(codpes) in settings.admin_nusp_list:
                user.role = ROLE_ADMINISTRADOR
            elif user.role:
                # Preserva o perfil que foi configurado para ele no sistema de monitoria
                user.role = normalize_role(user.role)
            else:
                user.role = role

        db.commit()
        db.refresh(user)

        # Grava na sessão HTTP
        request.session["user"] = {
            "id": user.id,
            "codpes": user.codpes,
            "name": user.name,
            "email": user.email,
            "role": user.role
        }

        # Limpa tokens temporários da sessão
        request.session.pop("oauth_token", None)
        request.session.pop("oauth_token_secret", None)

        return RedirectResponse(url="/", status_code=303)
    except Exception as e:
        logger.error(f"Erro no processamento do callback USP: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao autenticar usuário: {str(e)}")

@router.get("/auth/logout")
def logout(request: Request):
    """
    Desloga o usuário do sistema.
    """
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)

@router.get("/auth/dev-login")
def dev_login(request: Request, codpes: int = 7762448, role: str = "Administrador", name: str = None, db: Session = Depends(get_db)):
    """
    Atalho exclusivo de desenvolvimento para testar os 7 perfis do sistema rapidamente.
    """
    if settings.ENVIRONMENT != "development":
        raise HTTPException(status_code=403, detail="Não permitido em produção.")

    from app.models.user import normalize_role
    target_role = normalize_role(role)

    user = db.query(User).filter(User.codpes == codpes).first()
    user_name = name or f"Usuário {target_role} ({codpes})"
    
    if not user:
        user = User(
            name=user_name,
            email=f"{codpes}@ime.usp.br",
            codpes=codpes,
            role=target_role
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        user.role = target_role
        if name:
            user.name = name
        db.commit()
        db.refresh(user)

    request.session["user"] = {
        "id": user.id,
        "codpes": user.codpes,
        "name": user.name,
        "email": user.email,
        "role": user.role
    }
    return RedirectResponse(url="/", status_code=303)

