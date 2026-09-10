import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.config import Settings
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


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
