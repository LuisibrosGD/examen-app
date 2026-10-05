"""Configuración cargada desde el entorno y backend/.env."""

from pathlib import Path

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: SecretStr
    database_url_direct: SecretStr | None = None
    secret_key: SecretStr
    access_token_minutes: int = Field(default=1440, gt=0)
    cors_origins: list[str] = ["https://examen-app-lyart.vercel.app"]

    @field_validator("secret_key")
    @classmethod
    def validar_secreto(cls, value: SecretStr) -> SecretStr:
        if len(value.get_secret_value()) < 32:
            raise ValueError("SECRET_KEY debe tener al menos 32 caracteres.")
        return value

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[1] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        hide_input_in_errors=True,
    )


settings = Settings()
