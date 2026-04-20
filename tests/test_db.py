from sqlalchemy import inspect

from gotime.db import Base, Location, Provider, Trip, TripApiLog, User, create_engine_from_url


def test_schema_has_expected_tables():
    engine = create_engine_from_url("sqlite:///:memory:")
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    assert {"users", "providers", "locations", "trips", "trip_api_logs"}.issubset(tables)
    assert Base.metadata.tables  # declarative base registered


def test_models_are_importable():
    # Smoke test that we can instantiate the ORM classes.
    assert User().__tablename__ == "users"
    assert Provider(name="x").name == "x"
    assert Location(address="a").address == "a"
    assert Trip().__tablename__ == "trips"
    assert TripApiLog(raw_json={"a": 1}).raw_json == {"a": 1}
