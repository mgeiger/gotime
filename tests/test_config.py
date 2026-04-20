from pathlib import Path

from gotime.config import Settings, load_settings


def test_load_settings_defaults(monkeypatch):
    for key in [
        "GOTIME_DATABASE_URL",
        "GOOGLE_MAPS_API_KEY",
        "BING_MAPS_API_KEY",
        "TOMTOM_API_KEY",
        "HERE_API_KEY",
        "MAPQUEST_API_KEY",
        "MAPBOX_API_KEY",
        "AZURE_MAPS_API_KEY",
        "GOTIME_STORE_RAW_RESPONSES",
    ]:
        monkeypatch.delenv(key, raising=False)
    settings = load_settings(env_file=Path("/nonexistent/.env.missing"))
    assert settings.database_url == "sqlite:///./gotime.db"
    assert settings.google_maps_api_key is None
    # raw-response persistence is off by default (ToS posture).
    assert settings.store_raw_responses is False


def test_api_key_for_lookup():
    settings = Settings(
        database_url="sqlite:///:memory:",
        google_maps_api_key="g",
        bing_maps_api_key="b",
        tomtom_api_key="t",
        here_api_key="h",
        mapquest_api_key="m",
        mapbox_api_key="x",
        azure_maps_api_key="a",
    )
    for name, expected in [
        ("google", "g"),
        ("BING", "b"),
        ("tomtom", "t"),
        ("here", "h"),
        ("mapquest", "m"),
        ("MAPBOX", "x"),
        ("azure", "a"),
    ]:
        assert settings.api_key_for(name) == expected
    assert settings.api_key_for("unknown") is None


def test_load_settings_reads_env(monkeypatch):
    monkeypatch.setenv("GOTIME_DATABASE_URL", "postgresql://x@y/z")
    monkeypatch.setenv("GOOGLE_MAPS_API_KEY", "abc")
    s = load_settings()
    assert s.database_url == "postgresql://x@y/z"
    assert s.google_maps_api_key == "abc"


def test_store_raw_responses_truthy_values(monkeypatch):
    for raw, expected in [
        ("1", True),
        ("true", True),
        ("TRUE", True),
        ("yes", True),
        ("on", True),
        (" True ", True),
        ("0", False),
        ("false", False),
        ("no", False),
        ("off", False),
        ("", False),
        ("garbage", False),
    ]:
        monkeypatch.setenv("GOTIME_STORE_RAW_RESPONSES", raw)
        s = load_settings()
        assert s.store_raw_responses is expected, f"GOTIME_STORE_RAW_RESPONSES={raw!r}"
