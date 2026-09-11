import httpx2
import pytest
from fastapi import status
from pydantic import SecretStr

from app.blizzard import BlizzardClient, TokenPrice
from app.config import Settings


@pytest.fixture
def api_settings() -> Settings:
    return Settings(
        blizzard_client_id="test",
        blizzard_client_secret=SecretStr("test"),
        blizzard_region="fr",
        database_url=SecretStr(""),
    )


@pytest.fixture
def success_payload() -> dict[str, object]:
    return {
        "access_token": "mock_token",
        "token_type": "test_token",
        "expires_in": 86400,
    }


def test_get_access_token_returns_token_from_response(api_settings, success_payload):

    def handler(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(status_code=status.HTTP_200_OK, json=success_payload)

    transport = httpx2.MockTransport(handler)

    client = BlizzardClient(api_settings, transport=transport)
    access_token = client.get_access_token()
    assert access_token == "mock_token"


def test_only_authenticates_once(api_settings, success_payload):
    requests = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        requests.append(request)
        return httpx2.Response(status_code=status.HTTP_200_OK, json=success_payload)

    transport = httpx2.MockTransport(handler)

    client = BlizzardClient(api_settings, transport=transport)
    first_token = client.get_access_token()
    second_token = client.get_access_token()
    assert first_token == second_token
    assert len(requests) == 1


def test_get_access_token_raises_on_401(api_settings):

    def handler(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(status_code=status.HTTP_401_UNAUTHORIZED)

    transport = httpx2.MockTransport(handler)
    client = BlizzardClient(api_settings, transport=transport)

    with pytest.raises(httpx2.HTTPStatusError) as exception:
        client.get_access_token()

    assert exception.value.response.status_code == status.HTTP_401_UNAUTHORIZED


def test_copper_to_gold_conversion():
    token_price_in_gold = TokenPrice(price=50000, last_updated_timestamp=1788347472000)
    assert token_price_in_gold.gold == 5


def test_get_token_price_returns_parsed_price(api_settings, success_payload):
    requests = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        requests.append(request)
        if request.url.path.endswith("/token"):
            return httpx2.Response(status_code=status.HTTP_200_OK, json=success_payload)
        return httpx2.Response(
            status_code=status.HTTP_200_OK,
            json={"price": 50000, "last_updated_timestamp": 1788347472000},
        )

    transport = httpx2.MockTransport(handler)

    client = BlizzardClient(api_settings, transport=transport)

    token_price = client.get_token_price()
    assert requests[1].headers["Authorization"] == "Bearer mock_token"
    assert token_price.price == 50000
    assert token_price.gold == 5
