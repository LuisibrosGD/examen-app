"""Hash argon2 y tokens JWT con algoritmo fijo y expiración obligatoria."""

from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.config import settings

hasher = PasswordHasher()
# Evita saltarse el trabajo de argon2 si el email no existe.
dummy_hash = hasher.hash("usuario-inexistente")


def hash_password(password: str) -> str:
    return hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False


def create_access_token(usuario_id: int) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": str(usuario_id), "iat": now, "exp": now + timedelta(minutes=settings.access_token_minutes)},
        settings.secret_key.get_secret_value(),
        algorithm="HS256",
    )


def decode_access_token(token: str) -> int:
    claims = jwt.decode(
        token, settings.secret_key.get_secret_value(), algorithms=["HS256"],
        options={"require": ["sub", "iat", "exp"]},
    )
    return int(claims["sub"])
