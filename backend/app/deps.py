"""Dependencias reutilizables para sesiones y autorización."""

from collections.abc import Generator
from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Usuario
from app.security import decode_access_token

bearer = HTTPBearer(auto_error=False)


def get_db() -> Generator[Session, None, None]:
    with SessionLocal() as db:
        yield db


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    db: Annotated[Session, Depends(get_db)],
) -> Usuario:
    unauthorized = HTTPException(401, "Sesión inválida o expirada.", headers={"WWW-Authenticate": "Bearer"})
    if credentials is None:
        raise unauthorized
    try:
        usuario_id = decode_access_token(credentials.credentials)
    except (InvalidTokenError, ValueError, TypeError):
        raise unauthorized from None
    usuario = db.get(Usuario, usuario_id)
    if usuario is None:
        raise unauthorized
    return usuario
