"""Registro, login JSON y consulta del usuario autenticado."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import settings
from app.deps import get_current_user, get_db
from app.models import Usuario
from app.schemas import Credenciales, Registro, Token, UsuarioPublico
from app.security import create_access_token, dummy_hash, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["Usuarios"])


@router.post("/registro", response_model=UsuarioPublico, status_code=201)
def registro(datos: Registro, db: Annotated[Session, Depends(get_db)]) -> Usuario:
    usuario = Usuario(email=str(datos.email), nombre=datos.nombre, password_hash=hash_password(datos.password.get_secret_value()))
    db.add(usuario)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "El email ya está registrado.") from None
    db.refresh(usuario)
    return usuario


@router.post("/login", response_model=Token)
def login(datos: Credenciales, db: Annotated[Session, Depends(get_db)]) -> Token:
    usuario = db.scalar(select(Usuario).where(Usuario.email == str(datos.email)))
    valid = verify_password(usuario.password_hash if usuario else dummy_hash, datos.password.get_secret_value())
    if usuario is None or not valid:
        raise HTTPException(401, "Email o contraseña incorrectos.", headers={"WWW-Authenticate": "Bearer"})
    return Token(access_token=create_access_token(usuario.id), expires_in=settings.access_token_minutes * 60)


@router.get("/me", response_model=UsuarioPublico)
def me(usuario: Annotated[Usuario, Depends(get_current_user)]) -> Usuario:
    return usuario
