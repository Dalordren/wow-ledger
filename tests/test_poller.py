from contextlib import nullcontext
import time  # The standard module (has .sleep)
from datetime import time as dt_time
from datetime import UTC, datetime

import httpx2
import pytest
from fastapi import status

from app.blizzard import BlizzardClient, TokenPrice
from app.poller import is_retryable, poll_once, poll_with_retry
from tests.helpers import status_code_error


class FakeClient:
    """Fails the first N calls, then returns a reading."""

    def __init__(self, failures: int, parsed, error):
        self._failures = failures
        self._parsed = parsed
        self._error = error
        self.call_count = 0

    def get_token_price(self):
        self.call_count += 1
        if self.call_count <= self._failures:
            raise self._error
        return self._parsed


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (httpx2.ConnectError("Connection Refused"), True),
        (status_code_error(429), True),
        (status_code_error(502), True),
        (status_code_error(503), True),
        (status_code_error(504), True),
        (status_code_error(500), True),
        (status_code_error(400), False),
        (status_code_error(401), False),
        (status_code_error(404), False),
        (ValueError("Server error"), False),
        (RuntimeError("General system failure"), False),
    ],
)
def test_is_retryable(error, expected):
    assert is_retryable(error) is expected


def test_poll_once_records_fetched_price(
    api_settings, success_payload, db_session, price_payload
):

    def handler(request: httpx2.Request) -> httpx2.Response:
        if request.url.path.endswith("/token"):
            return httpx2.Response(status_code=status.HTTP_200_OK, json=success_payload)
        return httpx2.Response(
            status_code=status.HTTP_200_OK,
            json=price_payload,
        )

    transport = httpx2.MockTransport(handler)

    client = BlizzardClient(api_settings, transport=transport)

    price_snapshot = poll_once(client, db_session, api_settings.blizzard_region)
    assert price_snapshot is not None
    assert price_snapshot.published_at == datetime(2026, 9, 2, 11, 11, 12, tzinfo=UTC)
    assert price_snapshot.price_copper == 50000
    assert price_snapshot.gold == 5


def test_poll_with_retry_success_on_second_attempt(db_session, monkeypatch):
    delays = []
    monkeypatch.setattr(time, "sleep", lambda seconds: delays.append(seconds))
    client = FakeClient(
        failures=1,
        error=httpx2.ConnectError("dns failure"),
        parsed=TokenPrice(price=50000, last_updated_timestamp=1788347472000),
    )
    result = poll_with_retry(client, lambda: nullcontext(db_session), "us")

    assert result is not None
    assert client.call_count == 2
    assert delays == [2]


def test_poll_with_retry_does_not_retry_unauthorized(db_session, monkeypatch):
    delays = []
    monkeypatch.setattr(time, "sleep", lambda seconds: delays.append(seconds))
    client = FakeClient(
        failures=1,
        error=status_code_error(0),
        parsed=TokenPrice(price=50000, last_updated_timestamp=1788347472000),
    )
    with pytest.raises(httpx2.HTTPStatusError):
        poll_with_retry(client, lambda: nullcontext(db_session), "ca")
    assert client.call_count == 1
    assert delays == []
