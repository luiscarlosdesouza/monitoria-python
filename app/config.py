import os
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = os.getenv("APP_NAME", "Sistema de Monitoria - IME-USP")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-key-change-in-production-123456")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    APP_PORT: int = int(os.getenv("APP_PORT", "8020"))
    
    # Novo Banco de Dados (App local SQLite ou MySQL MariaDB em produção)
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "sqlite:///./monitoria.db"
    )
    
    # USP Senha Única OAuth 1.0a
    USP_CLIENT_KEY: str = os.getenv("USP_CLIENT_KEY", os.getenv("SENHAUNICA_KEY", "ime_helios"))
    USP_CLIENT_SECRET: str = os.getenv("USP_CLIENT_SECRET", os.getenv("SENHAUNICA_SECRET", "udhMktxPF5cTcYjEOk8tyB12Fm1aH8fJvAmqGtWt"))
    USP_CALLBACK_ID: str = os.getenv("USP_CALLBACK_ID", os.getenv("SENHAUNICA_CALLBACK_ID", "82"))
    USP_CALLBACK_URL: str = os.getenv("USP_CALLBACK_URL", "http://localhost:8020/auth/callback")
    USP_OAUTH_URL: str = os.getenv("USP_OAUTH_URL", "https://uspdigital.usp.br/wsusuario/oauth")
    SENHAUNICA_ADMINS: str = os.getenv("SENHAUNICA_ADMINS", "7762448,2803642,5085616")
    
    # USP Replicado (Sybase / MSSQL)
    REPLICADO_HOST: str = os.getenv("REPLICADO_HOST", "200.144.255.63")
    REPLICADO_PORT: str = os.getenv("REPLICADO_PORT", "1433")
    REPLICADO_DATABASE: str = os.getenv("REPLICADO_DATABASE", "replicado")
    REPLICADO_USERNAME: str = os.getenv("REPLICADO_USERNAME", "replicado-r")
    REPLICADO_PASSWORD: str = os.getenv("REPLICADO_PASSWORD", "4rqu1mede$")
    REPLICADO_SYBASE: int = int(os.getenv("REPLICADO_SYBASE", "1"))
    
    # Banco de Dados Legado (Para script de migração e consulta)
    LEGACY_DB_HOST: str = os.getenv("DB_HOST", "carapicuiba")
    LEGACY_DB_PORT: int = int(os.getenv("DB_PORT", "3306"))
    LEGACY_DB_DATABASE: str = os.getenv("DB_DATABASE", "monitoria")
    LEGACY_DB_USERNAME: str = os.getenv("DB_USERNAME", "monitoria")
    LEGACY_DB_PASSWORD: str = os.getenv("DB_PASSWORD", "N^HbydDzh!CQx6%b^+R)&aT#{")
    
    # E-mail SMTP
    MAIL_HOST: str = os.getenv("MAIL_HOST", "smtp.ime.usp.br")
    MAIL_PORT: int = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USERNAME: str = os.getenv("MAIL_USERNAME", "apoio")
    MAIL_PASSWORD: str = os.getenv("MAIL_PASSWORD", "")
    MAIL_FROM_ADDRESS: str = os.getenv("MAIL_FROM_ADDRESS", "sistemas@ime.usp.br")
    
    @property
    def admin_nusp_list(self) -> List[str]:
        return [n.strip() for n in self.SENHAUNICA_ADMINS.split(",") if n.strip()]

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"

settings = Settings()
