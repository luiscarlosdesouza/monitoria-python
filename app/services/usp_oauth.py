import logging
from typing import Dict, Any, Tuple
from authlib.integrations.httpx_client import OAuth1Client
from app.config import settings

logger = logging.getLogger("usp_oauth")

class USPOAuthService:
    @property
    def client_key(self) -> str:
        return settings.oauth_key

    @property
    def client_secret(self) -> str:
        return settings.oauth_secret

    @property
    def callback_id(self) -> str:
        return settings.oauth_callback_id

    @property
    def base_url(self) -> str:
        return settings.USP_OAUTH_URL.rstrip('/')
        
    @property
    def request_token_url(self) -> str:
        return f"{self.base_url}/request_token"

    @property
    def authorize_url(self) -> str:
        return f"{self.base_url}/authorize"

    @property
    def access_token_url(self) -> str:
        return f"{self.base_url}/access_token"

    @property
    def user_info_url(self) -> str:
        return f"{self.base_url}/usuariousp"

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
            # No protocolo da USP, o request_token NÃO recebe body (isso alteraria a assinatura OAuth 1.0)
            token = client.fetch_request_token(self.request_token_url)
            oauth_token = token.get("oauth_token")
            oauth_token_secret = token.get("oauth_token_secret")
            
            # O callback_id é anexado na URL de autorização para o usuário
            auth_url = f"{self.authorize_url}?oauth_token={oauth_token}&callback_id={self.callback_id}"
            return auth_url, oauth_token, oauth_token_secret
        except Exception as e:
            logger.error(f"Erro ao obter request_token da USP (key={self.client_key}, callback_id={self.callback_id}): {e}")
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
            # 1. Troca por access token (USP recebe oauth_verifier na URL/body)
            access_token = client.fetch_access_token(
                f"{self.access_token_url}?oauth_verifier={oauth_verifier}",
                data={"oauth_verifier": oauth_verifier, "oauth_token": oauth_token}
            )
            
            # 2. Requisita os dados do usuário via POST
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
