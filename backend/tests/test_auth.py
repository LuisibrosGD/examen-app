"""Verifica persistencia, autenticación y rechazo de tokens inválidos."""

from datetime import datetime, timedelta, timezone

import jwt
import pytest
from sqlalchemy import select

from app.config import settings
from app.database import SessionLocal
from app.models import Usuario
from app.security import verify_password

USER = {"email": "persona@example.com", "nombre": "Persona", "password": "UnaClaveSegura123"}


def register_and_login(client):
    response = client.post("/auth/registro", json=USER)
    assert response.status_code == 201
    login = client.post("/auth/login", json={"email": USER["email"], "password": USER["password"]})
    assert login.status_code == 200
    return response.json(), login.json()["access_token"]


def test_register_login_and_me(client):
    public, token = register_and_login(client)
    assert set(public) == {"id", "email", "nombre", "creado_en"}
    with SessionLocal() as db:
        user = db.scalar(select(Usuario))
        assert user.password_hash.startswith("$argon2id$")
        assert verify_password(user.password_hash, USER["password"])
        assert user.password_hash != USER["password"]
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json() == public


def test_normalization_and_duplicate_email(client):
    data = {**USER, "email": " PERSONA@EXAMPLE.COM ", "nombre": " Persona "}
    first = client.post("/auth/registro", json=data)
    assert first.status_code == 201
    assert first.json()["email"] == USER["email"]
    assert first.json()["nombre"] == USER["nombre"]
    assert client.post("/auth/registro", json=USER).status_code == 409
    assert client.post("/auth/login", json={"email": data["email"], "password": USER["password"]}).status_code == 200


@pytest.mark.parametrize("changes", [{"email": "invalido"}, {"nombre": "   "}, {"password": "corta"}])
def test_invalid_registration(client, changes):
    response = client.post("/auth/registro", json={**USER, **changes})
    assert response.status_code == 422
    assert all("input" not in error for error in response.json()["detail"])
    with SessionLocal() as db:
        assert db.scalar(select(Usuario)) is None


def test_bad_credentials_do_not_identify_existing_emails(client):
    register_and_login(client)
    responses = [client.post("/auth/login", json={"email": email, "password": "Incorrecta"})
                 for email in [USER["email"], "nadie@example.com"]]
    assert all(response.status_code == 401 for response in responses)
    assert responses[0].json() == responses[1].json()


@pytest.mark.parametrize("kind", ["absent", "malformed", "expired", "forged", "missing_exp", "unknown_user", "wrong_algorithm", "invalid_sub"])
def test_invalid_tokens(client, kind):
    public, token = register_and_login(client)
    now = datetime.now(timezone.utc)
    claims = {"sub": str(public["id"]), "iat": now, "exp": now + timedelta(minutes=5)}
    key = settings.secret_key.get_secret_value()
    algorithm = "HS256"
    if kind == "expired":
        claims["exp"] = now - timedelta(seconds=1)
    elif kind == "forged":
        key = "otra-clave-de-pruebas-completamente-diferente-123"
    elif kind == "missing_exp":
        del claims["exp"]
    elif kind == "unknown_user":
        claims["sub"] = "999999"
    elif kind == "wrong_algorithm":
        algorithm = "HS384"
    elif kind == "invalid_sub":
        claims["sub"] = "abc"
    token = jwt.encode(claims, key, algorithm=algorithm)
    if kind == "malformed":
        token = "invalid-token"
    headers = {} if kind == "absent" else {"Authorization": f"Bearer {token}"}
    response = client.get("/auth/me", headers=headers)
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_me_is_current_user_only(client):
    public, token = register_and_login(client)
    other = client.post("/auth/registro", json={**USER, "email": "otra@example.com"})
    assert other.status_code == 201
    response = client.get("/auth/me?usuario_id=" + str(other.json()["id"]), headers={"Authorization": f"Bearer {token}"})
    assert response.json()["id"] == public["id"]


def test_cors_accepts_bearer_and_rejects_other_origins(client):
    headers = {"Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "authorization,content-type"}
    response = client.options("/auth/login", headers=headers)
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == headers["Origin"]
    response = client.options("/auth/login", headers={**headers, "Origin": "https://otro.example.com"})
    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers
