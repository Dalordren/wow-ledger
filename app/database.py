from sqlalchemy import create_engine
from collections.abc import Iterator
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from app.config import get_settings

settings = get_settings()
DATABASE_URL = settings.database_url.get_secret_value()

engine = create_engine(DATABASE_URL, echo=settings.db_echo, pool_pre_ping=True)
SessionLocal = sessionmaker(autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Iterator[Session]:
    with SessionLocal() as session:
        yield session
