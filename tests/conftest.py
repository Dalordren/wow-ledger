import os

import pytest
from alembic.config import Config
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from alembic import command
from app.config import Settings
from app.database import get_db
from app.main import app

load_dotenv()

TEST_DATABASE_URL = os.environ["TEST_DATABASE_URL"]


@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine(TEST_DATABASE_URL)

    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", TEST_DATABASE_URL)
    command.upgrade(config, "head")

    yield engine
    engine.dispose()


@pytest.fixture
def db_session(test_engine):
    connection = test_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


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
        db_echo=False,
        jwt_secret_key=SecretStr(""),
        access_token_expiry_minutes=30,
    )


@pytest.fixture
def success_payload() -> dict[str, object]:
    return {
        "access_token": "mock_token",
        "token_type": "test_token",
        "expires_in": 86400,
    }


@pytest.fixture
def price_payload() -> dict[str, object]:
    return {"price": 50000, "last_updated_timestamp": 1788347472000}


@pytest.fixture
def api_client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
