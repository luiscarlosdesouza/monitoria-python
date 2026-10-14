import logging
from typing import Dict, Any, Tuple
from authlib.integrations.httpx_client import OAuth1Client
from app.config import settings

logger = logging.getLogger("usp_oauth")

class USPOAuthService:
    def __init__(self):
        self.client_key = settings.USP_CLIENT_KEY
        self.client_secret = settings.USP_CLIENT_SECRET
        self.callback_id = settings.USP_CALLBACK_ID
        self.base_url = settings.USP_OAUTH_URL.rstrip('/')
        
        self.request_token_url = f"{self.base_url}/request_token"
        self.authorize_url = f"{self.base_url}/authorize"
        self.access_token_url = f"{self.base_url}/access_token"
        self.user_info_url = f"{self.base_url}/usuariousp"

    def get_request_token(self, callback_url: str) -> Tuple[str, str, str]:
        """
        Obtém o request token da USP e retorna (authorization_url, oauth_token, oauth_token_secret).
        """
        client = OAuth1Client(
            client_id=self.client_key,
            client_secret=self.client_secret,
            redirect_uri=callback_url
        )
        try:
            token = client.fetch_request_token(
                self.request_token_url,
                data={"callback_id": self.callback_id}
            )
            oauth_token = token.get("oauth_token")
            oauth_token_secret = token.get("oauth_token_secret")
            auth_url = f"{self.authorize_url}?oauth_token={oauth_token}"
            return auth_url, oauth_token, oauth_token_secret
        except Exception as e:
            logger.error(f"Erro ao obter request_token da USP: {e}")
            raise e

    def fetch_user_data(self, oauth_token: str, oauth_token_secret: str, oauth_verifier: str) -> Dict[str, Any]:
        """
        Troca o token temporário por um access_token e busca os dados do usuário autenticado no wsusuario.
        """
        client = OAuth1Client(
            client_id=self.client_key,
            client_secret=self.client_secret,
            token=oauth_token,
            token_secret=oauth_token_secret,
            verifier=oauth_verifier
        )
        try:
            # 1. Troca por access token
            access_token = client.fetch_access_token(self.access_token_url)
            
            # 2. Requisita os dados do usuário
            client.token = access_token
            response = client.post(self.user_info_url)
            response.raise_for_status()
            
            # O serviço USP pode responder em JSON ou XML dependendo do header
            try:
                user_data = response.json()
            except Exception:
                # Se responder em texto/form-data
                user_data = {"raw_response": response.text}
                
            return self.normalize_user(user_data)
        except Exception as e:
            logger.error(f"Erro ao buscar usuário USP: {e}")
            raise e

    def normalize_user(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normaliza os campos retornados pela USP (loginUsuario, nomeUsuario, emailPrincipalUsuario).
        """
        codpes = str(raw.get("loginUsuario", "")).strip()
        name = raw.get("nomeUsuario", "Usuário USP")
        email = raw.get("emailPrincipalUsuario", "")
        
        # Determinação do perfil
        is_admin = codpes in settings.admin_nusp_list
        role = "admin" if is_admin else "user"

        # Verificar vínculos no retorno (Docente, Aluno, Funcionário)
        vinculos = raw.get("vinculo", [])
        if isinstance(vinculos, list):
            tipos = [v.get("tipoVinculo", "").upper() for v in vinculos if isinstance(v, dict)]
            if "DOCENTE" in tipos:
                role = "docente" if not is_admin else "admin"
            elif any("ALUNO" in t for t in tipos):
                role = "aluno" if not is_admin else "admin"

        return {
            "codpes": int(codpes) if codpes.isdigit() else None,
            "name": name,
            "email": email,
            "role": role,
            "raw": raw
        }

usp_oauth_service = USPOAuthService()
