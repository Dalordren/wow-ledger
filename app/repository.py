from datetime import datetime

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models import PriceSnapshot


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
