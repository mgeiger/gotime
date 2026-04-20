from __future__ import annotations

import json

import httpx
import pytest
import respx
from typer.testing import CliRunner

from gotime import __version__
from gotime.cli import app


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for key in [
        "GOTIME_DATABASE_URL",
        "GOTIME_STORE_RAW_RESPONSES",
        "GOOGLE_MAPS_API_KEY",
        "BING_MAPS_API_KEY",
        "TOMTOM_API_KEY",
        "HERE_API_KEY",
        "MAPQUEST_API_KEY",
        "MAPBOX_API_KEY",
        "AZURE_MAPS_API_KEY",
    ]:
        monkeypatch.delenv(key, raising=False)


def test_version(runner):
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_providers_list(runner):
    result = runner.invoke(app, ["providers", "list"])
    assert result.exit_code == 0
    assert "google" in result.stdout
    assert "tomtom" in result.stdout


def test_db_info_redacts(runner, monkeypatch):
    monkeypatch.setenv("GOTIME_DATABASE_URL", "postgresql://user:pw@host:5432/db")
    result = runner.invoke(app, ["db", "info"])
    assert result.exit_code == 0
    assert "user:pw" not in result.stdout
    assert "***" in result.stdout


def test_db_info_sqlite_passthrough(runner, monkeypatch):
    monkeypatch.setenv("GOTIME_DATABASE_URL", "sqlite:///./x.db")
    result = runner.invoke(app, ["db", "info"])
    assert result.exit_code == 0
    assert "sqlite" in result.stdout


@respx.mock
def test_query_table(runner, monkeypatch):
    monkeypatch.setenv("GOOGLE_MAPS_API_KEY", "k")
    respx.get("https://maps.googleapis.com/maps/api/directions/json").mock(
        return_value=httpx.Response(
            200,
            json={
                "status": "OK",
                "routes": [
                    {
                        "legs": [
                            {
                                "duration": {"value": 600},
                                "duration_in_traffic": {"value": 720},
                                "distance": {"value": 1609},
                                "steps": [{"a": 1}],
                            }
                        ]
                    }
                ],
            },
        )
    )
    result = runner.invoke(
        app,
        [
            "query",
            "--origin",
            "42.36,-71.07",
            "--destination",
            "42.35,-71.10",
            "--provider",
            "google",
        ],
    )
    assert result.exit_code == 0
    assert "google" in result.stdout


@respx.mock
def test_query_json(runner, monkeypatch):
    monkeypatch.setenv("GOOGLE_MAPS_API_KEY", "k")
    respx.get("https://maps.googleapis.com/maps/api/directions/json").mock(
        return_value=httpx.Response(
            200,
            json={
                "status": "OK",
                "routes": [{"legs": [{"duration": {"value": 60}, "distance": {"value": 100}, "steps": []}]}],
            },
        )
    )
    result = runner.invoke(
        app,
        [
            "query",
            "--origin",
            "42.36,-71.07",
            "--destination",
            "42.35,-71.10",
            "--provider",
            "google",
            "--json",
        ],
    )
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert "google" in payload
    assert payload["google"]["duration_seconds"] == 60


def test_query_invalid_origin(runner):
    result = runner.invoke(
        app,
        [
            "query",
            "--origin",
            "nope",
            "--destination",
            "42.35,-71.10",
            "--provider",
            "google",
        ],
    )
    assert result.exit_code != 0


def test_query_missing_key_shows_error(runner):
    result = runner.invoke(
        app,
        [
            "query",
            "--origin",
            "42.36,-71.07",
            "--destination",
            "42.35,-71.10",
            "--provider",
            "google",
            "--json",
        ],
    )
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert "no API key" in payload["google"]["error"]


@respx.mock
def test_query_json_partial_error(runner, monkeypatch):
    monkeypatch.setenv("GOOGLE_MAPS_API_KEY", "k")
    respx.get("https://maps.googleapis.com/maps/api/directions/json").mock(
        return_value=httpx.Response(500, text="boom")
    )
    result = runner.invoke(
        app,
        [
            "query",
            "--origin",
            "42.36,-71.07",
            "--destination",
            "42.35,-71.10",
            "--provider",
            "google",
            "--json",
        ],
    )
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert "error" in payload["google"]


# ---------------------------------------------------------------------------
# providers verify / verify-keys
# ---------------------------------------------------------------------------


def _google_ok_response() -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "status": "OK",
            "routes": [
                {
                    "legs": [
                        {
                            "duration": {"value": 60},
                            "duration_in_traffic": {"value": 60},
                            "distance": {"value": 100},
                            "steps": [],
                        }
                    ]
                }
            ],
        },
    )


@respx.mock
def test_providers_verify_all_ok(runner, monkeypatch):
    monkeypatch.setenv("GOOGLE_MAPS_API_KEY", "good-key")
    respx.get("https://maps.googleapis.com/maps/api/directions/json").mock(return_value=_google_ok_response())
    result = runner.invoke(app, ["providers", "verify", "--provider", "google", "--json"])
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    assert payload == [{"provider": "google", "status": "ok", "detail": None}]


@respx.mock
def test_providers_verify_invalid_key_fails(runner, monkeypatch):
    monkeypatch.setenv("GOOGLE_MAPS_API_KEY", "bad-key")
    respx.get("https://maps.googleapis.com/maps/api/directions/json").mock(
        return_value=httpx.Response(
            200, json={"status": "REQUEST_DENIED", "error_message": "The provided API key is invalid."}
        )
    )
    result = runner.invoke(app, ["providers", "verify", "--provider", "google", "--json"])
    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload[0]["status"] == "invalid"


def test_providers_verify_missing_key_passes(runner):
    # No GOOGLE_MAPS_API_KEY exported => `missing`, which is non-failing.
    result = runner.invoke(app, ["providers", "verify", "--provider", "google", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload[0] == {"provider": "google", "status": "missing", "detail": "no API key configured"}


@respx.mock
def test_providers_verify_table_output_uses_status(runner, monkeypatch):
    monkeypatch.setenv("GOOGLE_MAPS_API_KEY", "good-key")
    respx.get("https://maps.googleapis.com/maps/api/directions/json").mock(return_value=_google_ok_response())
    result = runner.invoke(app, ["providers", "verify", "--provider", "google"])
    assert result.exit_code == 0
    assert "google" in result.stdout
    assert "ok" in result.stdout


@respx.mock
def test_top_level_verify_keys_alias(runner, monkeypatch):
    monkeypatch.setenv("GOOGLE_MAPS_API_KEY", "good-key")
    respx.get("https://maps.googleapis.com/maps/api/directions/json").mock(return_value=_google_ok_response())
    result = runner.invoke(app, ["verify-keys", "--provider", "google", "--json", "--timeout", "2.5"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload[0]["status"] == "ok"


@respx.mock
def test_providers_verify_mixed_results_fail_fast(runner, monkeypatch):
    # google ok, tomtom 401 -> overall exit 1 because `invalid` is non-passing.
    monkeypatch.setenv("GOOGLE_MAPS_API_KEY", "g")
    monkeypatch.setenv("TOMTOM_API_KEY", "t")
    respx.get("https://maps.googleapis.com/maps/api/directions/json").mock(return_value=_google_ok_response())
    respx.get(url__regex=r"https://api\.tomtom\.com/routing/1/calculateRoute/.*").mock(
        return_value=httpx.Response(401, text="invalid key")
    )
    result = runner.invoke(app, ["providers", "verify", "--provider", "google", "--provider", "tomtom", "--json"])
    assert result.exit_code == 1
    statuses = {row["provider"]: row["status"] for row in json.loads(result.stdout)}
    assert statuses == {"google": "ok", "tomtom": "invalid"}
