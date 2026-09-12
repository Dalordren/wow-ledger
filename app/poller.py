import time
from collections.abc import Callable
from typing import Protocol

import httpx2
from sqlalchemy.orm import Session

from app.blizzard import BlizzardClient, TokenPrice
from app.config import get_settings
from app.database import SessionLocal
from app.models import PriceSnapshot
from app.repository import record_price

RETRYABLE_STATUS_CODES = frozenset({429, 500, 502, 503, 504})
MAX_ATTEMPTS = 3
BACKOFF_BASE_SECONDS = 2


class PriceSource(Protocol):
    def get_token_price(self) -> TokenPrice: ...


def is_retryable(error: Exception) -> bool:
    if isinstance(error, httpx2.TransportError):
        return True
    if isinstance(error, httpx2.HTTPStatusError):
        return error.response.status_code in RETRYABLE_STATUS_CODES
    return False


def poll_once(
    client: PriceSource, session: Session, region: str
) -> PriceSnapshot | None:
    wow_token = client.get_token_price()
    token_price = wow_token.price
    updated_at = wow_token.updated_at
    snapshot = record_price(session, region, token_price, updated_at)
    session.commit()
    return snapshot


def poll_with_retry(
    client: PriceSource, session_factory: Callable[[], Session], region: str
) -> PriceSnapshot | None:
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            with session_factory() as session:
                return poll_once(client, session, region)
        except Exception as error:
            if not is_retryable(error) or attempt == MAX_ATTEMPTS:
                raise
            delay = BACKOFF_BASE_SECONDS**attempt
            print(f"attempt {attempt} failed({error}); Retrying in {delay}s")
            time.sleep(delay)
    raise RuntimeError("Retry exited without returning or raising")


def main() -> None:
    settings = get_settings()
    client = BlizzardClient(settings)
    while True:
        try:
            snapshot = poll_with_retry(client, SessionLocal, settings.blizzard_region)
        except Exception as error:
            print(f"Poll failed with {error}")
        else:
            if snapshot is None:
                print("No update available")
            else:
                print(f"Updated Wow token price is {snapshot.gold}g")
        time.sleep(settings.poll_interval_seconds)


if __name__ == "__main__":
    main()
