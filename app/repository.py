from datetime import datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.errors import EmailAlreadyRegistered
from app.models import PriceSnapshot, User


def record_price(
    session: Session,
    region: str,
    price_copper: int,
    published_at: datetime,
) -> PriceSnapshot | None:
    """Insert a price snapshot, or return None if this snapshot is already recorded."""
    statement = (
        insert(PriceSnapshot)
        .values(region=region, price_copper=price_copper, published_at=published_at)
        .on_conflict_do_nothing(constraint="uq_price_snapshots_region_published_at")
        .returning(PriceSnapshot)
    )
    return session.execute(statement).scalars().one_or_none()


def get_user_by_email(session: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    return session.execute(statement).scalar_one_or_none()


def create_user(session: Session, email: str, hashed_password: str) -> User:
    new_user = User(email=email, hashed_password=hashed_password)
    try:
        session.add(new_user)
        session.flush()
    except IntegrityError as error:
        session.rollback()
        raise EmailAlreadyRegistered() from error
    return new_user
