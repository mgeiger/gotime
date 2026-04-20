"""Shared pytest fixtures."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from gotime.config import Settings
from gotime.db.session import create_engine_from_url, make_sessionmaker
from gotime.models import Waypoint


@pytest.fixture
def origin() -> Waypoint:
    return Waypoint(latitude=42.3554, longitude=-71.0654, label="home")


@pytest.fixture
def destination() -> Waypoint:
    return Waypoint(latitude=42.3467, longitude=-71.0972, label="work")


@pytest.fixture
def in_memory_engine() -> Iterator[Engine]:
    engine = create_engine_from_url("sqlite:///:memory:")
    yield engine
    engine.dispose()


@pytest.fixture
def SessionFactory(in_memory_engine: Engine) -> sessionmaker[Session]:
    return make_sessionmaker(in_memory_engine)


@pytest.fixture
def db_session(SessionFactory: sessionmaker[Session]) -> Iterator[Session]:
    session = SessionFactory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def all_keys_settings() -> Settings:
    return Settings(
        database_url="sqlite:///:memory:",
        google_maps_api_key="g-test",
        bing_maps_api_key="b-test",
        tomtom_api_key="t-test",
        here_api_key="h-test",
        mapquest_api_key="mq-test",
        mapbox_api_key="mb-test",
        azure_maps_api_key="a-test",
    )
