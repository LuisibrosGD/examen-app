"""Motor SQLAlchemy para PostgreSQL en Neon."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings

engine = create_engine(
    settings.database_url.get_secret_value(),
    pool_pre_ping=True,
    connect_args={"connect_timeout": 10} if settings.database_url.get_secret_value().startswith("postgresql") else {},
)

SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
