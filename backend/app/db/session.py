from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    pass


connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def set_tenant_context(db: Session, firm_id: str) -> None:
    if settings.database_url.startswith("postgresql"):
        db.execute(text("select set_config('app.current_firm_id', :firm_id, true)"), {"firm_id": firm_id})


def init_database() -> None:
    from app.db import models  # noqa: F401

    if settings.auto_create_db:
        Base.metadata.create_all(bind=engine)


def get_database_status() -> dict[str, str]:
    mode = "postgresql-rls" if settings.database_url.startswith("postgresql") else "sqlite-dev"
    return {"mode": mode, "url": settings.database_url.split("@")[-1]}
