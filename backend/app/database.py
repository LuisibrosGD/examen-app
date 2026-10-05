"""Motor SQLAlchemy para PostgreSQL en Neon."""

from sqlalchemy import create_engine

from app.config import settings

engine = create_engine(
    settings.database_url.get_secret_value(),
    pool_pre_ping=True,
    connect_args={"connect_timeout": 10},
)
