import os
from typing import Literal
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Spaceness API"
    debug: bool = True
    port: int = 8000
    host: str = "0.0.0.0"

    database_url: str = "sqlite+aiosqlite:///shop.db"

    email_host: str = ""
    email_port: int = 587
    email_user: str = ""
    email_password: str = ""

    admin_email: str = "admin@shop.local"
    admin_password: str = "admin123"

    secret_key: str = "dev-secret-key-change-in-production"
    cors_origins: str = "*"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @property
    def db_driver(self) -> Literal["postgresql", "sqlite"]:
        return "postgresql" if "postgresql" in self.database_url else "sqlite"


settings = Settings()
