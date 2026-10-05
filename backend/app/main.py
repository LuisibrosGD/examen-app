"""API mínima con comprobación de conectividad a la base de datos."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.database import engine

app = FastAPI(title="Examen App")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET"],
    allow_headers=["Accept", "Content-Type"],
)


@app.get("/health")
def health() -> dict[str, str]:
    """Comprueba que Neon responde a una consulta SQL real."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1")).scalar_one()
    except SQLAlchemyError:
        raise HTTPException(
            status_code=503,
            detail="No se pudo conectar con la base de datos.",
        ) from None
    return {"status": "ok", "database": "ok"}
