import os
from collections.abc import Generator
from functools import lru_cache

import pytest
from app.core.config import Settings, get_settings
from app.models import Base
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker


def _database_url() -> str:
    return os.getenv(
        "TEST_DATABASE_URL",
        "postgresql+psycopg://postgres:postgres@localhost:5433/promocode_checker",
    )


def _postgres_available(database_url: str) -> bool:
    try:
        engine = create_engine(
            database_url,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 2},
        )
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        engine.dispose()
        return True
    except Exception:
        return False


@lru_cache
def postgres_available() -> bool:
    return _postgres_available(_database_url())


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    return get_settings()


@pytest.fixture(scope="session")
def engine():
    database_url = _database_url()
    engine = create_engine(database_url, pool_pre_ping=True)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def db_session(engine) -> Generator[Session, None, None]:
    connection = engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection, autoflush=False, autocommit=False)()
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()
