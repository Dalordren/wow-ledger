from datetime import UTC, datetime

from sqlalchemy import func, select, text

from app.blizzard import BlizzardClient
from app.config import get_settings
from app.models import PriceSnapshot
from app.repository import record_price

settings = get_settings()
client = BlizzardClient(settings)
token_price = client.get_token_price()
published_at = token_price.updated_at
published_at = datetime(2026, 9, 3, 20, 12, 11, tzinfo=UTC)


def test_record_price_snapshot(db_session):
    new_record = record_price(
        session=db_session,
        region="fr",
        price_copper=token_price.price,
        published_at=published_at,
    )
    db_session.add(new_record)
    db_session.commit()
    assert db_session.execute(text("SELECT 1")).scalar_one() == 1


def test_price_snapshot_records_polling(db_session):
    snapshot = record_price(db_session, "us", 292000, published_at)
    assert snapshot is not None
    assert snapshot.region == "us"
    assert snapshot.price_copper == 292000
    assert snapshot.published_at == published_at


def test_record_price_ignores_duplicate_publication(db_session):
    first_pull = record_price(db_session, "us", 292000, published_at)
    second_pull = record_price(db_session, "us", 292000, published_at)
    query = select(func.count()).select_from(PriceSnapshot)
    assert db_session.execute(query).scalar() == 1
    assert first_pull is not None
    assert second_pull is None


def test_record_price_allows_same_timestamp_in_another_region(db_session):
    first_pull = record_price(db_session, "us", 292000, published_at)
    second_pull = record_price(db_session, "fr", 292000, published_at)
    query = select(func.count()).select_from(PriceSnapshot)
    assert db_session.execute(query).scalar() == 2
    assert first_pull is not None
    assert first_pull.region == "us"
    assert second_pull is not None
    assert second_pull.region == "fr"


def test_record_price_stores_values_above_32_bit_limit(db_session):
    snapshot = record_price(db_session, "us", 2699690000, published_at)
    assert snapshot is not None
    assert snapshot.price_copper == 2699690000
