"""Contratos JSON de autenticación; nunca exponen el hash."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr, field_validator


class Credenciales(BaseModel):
    email: EmailStr = Field(max_length=254)
    password: SecretStr = Field(min_length=1, max_length=128)

    @field_validator("email", mode="before")
    @classmethod
    def normalizar_email(cls, value: object) -> object:
        return value.strip().lower() if isinstance(value, str) else value


class Registro(Credenciales):
    nombre: str = Field(min_length=1, max_length=150)
    password: SecretStr = Field(min_length=8, max_length=128)

    @field_validator("nombre", mode="before")
    @classmethod
    def limpiar_nombre(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class UsuarioPublico(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    nombre: str
    creado_en: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
