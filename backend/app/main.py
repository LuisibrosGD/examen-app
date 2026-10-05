"""API mínima con comprobación de conectividad a la base de datos."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.database import engine
from app.config import settings
from app.routers.auth import router as auth_router

app = FastAPI(title="Examen App")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Accept", "Content-Type", "Authorization"],
)
app.include_router(auth_router)


@app.exception_handler(RequestValidationError)
async def validation_error(_request, exc: RequestValidationError) -> JSONResponse:
    """No devuelve contraseñas ni otros valores de entrada en errores 422."""
    return JSONResponse(status_code=422, content={"detail": [
        {"loc": list(error["loc"]), "msg": error["msg"], "type": error["type"]}
        for error in exc.errors()
    ]})


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
