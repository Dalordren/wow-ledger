from fastapi import Depends
import time
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.blizzard import BlizzardClient
from app.config import get_settings
from app.database import get_db
from app.models import PriceSnapshot
from app.repository import record_price


def poll_once(
    client: BlizzardClient, session: Session, region: str
) -> PriceSnapshot | None:
    wow_token = client.get_token_price()
    token_price = wow_token.price
    updated_at = wow_token.updated_at
    new_record = record_price(session, region, token_price, updated_at)
    session.commit()
    return new_record


def main() -> None:
    settings = get_settings()
    client = BlizzardClient(settings)
    while True:
        with SessionLocal() as session:
            new_record = poll_once(client, session, settings.blizzard_region)
        if new_record is None:
            print("No Updated Wow token price")
        else:
            print(f"Updated Wow token price is {new_record.price_copper}")
        time.sleep(settings.poll_interval_seconds)


if __name__ == "__main__":
    main()
