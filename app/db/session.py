from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


def get_engine():
    db_url = settings.DATABASE_URL
    if db_url.startswith("postgresql"):
        return create_engine(
            db_url,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
        )
    else:
        return create_engine(
            db_url,
            connect_args={"check_same_thread": False},
        )


engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
