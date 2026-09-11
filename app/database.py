from collections.abc import Iterator

from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

settings = get_settings()
DATABASE_URL = settings.database_url.get_secret_value()

engine = create_engine(DATABASE_URL, echo=settings.db_echo, pool_pre_ping=True)
SessionLocal = sessionmaker(autoflush=False, bind=engine, expire_on_commit=False)

convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=convention)


def get_db() -> Iterator[Session]:
    with SessionLocal() as session:
        yield session
