"""
Backend Core Configuration Settings.
"""
import os
from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "Enterprise Real-Time Data Intelligence Platform"
    environment: str = os.getenv("ENVIRONMENT", "development")
    secret_key: str = os.getenv("SECRET_KEY", "enterprise-secret-key-change-in-production-3af41cdc")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
    admin_username: str = os.getenv("ADMIN_USERNAME", "admin")
    admin_password: str = os.getenv("ADMIN_PASSWORD", "adminpassword123")
    debug: bool = os.getenv("DEBUG", "True").lower() == "true"
    host: str = os.getenv("BACKEND_HOST", "0.0.0.0")
    port: int = int(os.getenv("BACKEND_PORT", "8000"))


settings = Settings()

