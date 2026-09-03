import os

import pytest
from alembic import command
from alembic.config import Config
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from fastapi.testclient import TestClient
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
    session = Session(bind=transaction)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client():
    return TestClient(app)
