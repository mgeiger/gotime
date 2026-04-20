"""Verify that gotime's logging helpers never emit credentials."""

from __future__ import annotations

import logging

import httpx
import pytest
import respx

from gotime.logging import REDACTED, RedactingFilter, configure_logging, get_logger, redact
from gotime.models import Waypoint
from gotime.providers.google import GoogleProvider

FAKE_KEY = "AIzaSyFAKEKEYDOESNOTEXIST_0123456789"


class TestRedact:
    @pytest.mark.parametrize(
        "raw",
        [
            f"https://maps.googleapis.com/directions?origin=A&destination=B&key={FAKE_KEY}",
            f"https://api.tomtom.com/routing/1/...?key={FAKE_KEY}&traffic=true",
            f"https://here.example/v8/routes?apiKey={FAKE_KEY}",
            f"https://bing.example/routes?key={FAKE_KEY}&maxSolutions=1",
            f"https://mapbox.example/directions?access_token={FAKE_KEY}",
            f"Authorization: Bearer {FAKE_KEY}",
            f"X-Api-Key: {FAKE_KEY}",
            f"Ocp-Apim-Subscription-Key: {FAKE_KEY}",
            f"subscription-key={FAKE_KEY}",
            f"apiKey={FAKE_KEY}",
        ],
    )
    def test_strips_known_secret_carriers(self, raw: str) -> None:
        out = redact(raw)
        assert FAKE_KEY not in out
        assert REDACTED in out

    def test_none_input_is_empty_string(self) -> None:
        assert redact(None) == ""

    def test_non_string_coerces(self) -> None:
        assert redact(12345) == "12345"


class TestRedactingFilter:
    def test_filter_rewrites_record_message(self) -> None:
        logger = logging.getLogger("gotime.test_filter")
        logger.addFilter(RedactingFilter())
        records: list[logging.LogRecord] = []

        class _Capture(logging.Handler):
            def emit(self, record: logging.LogRecord) -> None:
                records.append(record)

        cap = _Capture(level=logging.DEBUG)
        logger.addHandler(cap)
        logger.setLevel(logging.DEBUG)
        try:
            logger.info("GET https://x.example/?key=%s end", FAKE_KEY)
        finally:
            logger.removeHandler(cap)
        assert records
        rendered = records[-1].getMessage()
        assert FAKE_KEY not in rendered
        assert REDACTED in rendered


class TestConfigureLogging:
    def test_idempotent_attachment(self) -> None:
        configure_logging()
        configure_logging()
        gt = logging.getLogger("gotime")
        redacting = [f for f in gt.filters if isinstance(f, RedactingFilter)]
        assert len(redacting) == 1

    def test_get_logger_namespaces_under_gotime(self) -> None:
        log = get_logger("something")
        assert log.name == "gotime.something"
        already = get_logger("gotime.other")
        assert already.name == "gotime.other"


class TestProviderDoesNotLeakKey:
    """The real fire-drill: with httpx at DEBUG, nothing containing the key
    should appear in captured log output for any provider request."""

    @respx.mock
    def test_google_request_logs_are_clean(self, caplog: pytest.LogCaptureFixture) -> None:
        configure_logging(level=logging.DEBUG)
        caplog.set_level(logging.DEBUG, logger="gotime")
        caplog.set_level(logging.DEBUG, logger="httpx")

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
                                    "distance": {"value": 10000},
                                    "steps": [{}],
                                }
                            ]
                        }
                    ],
                },
            )
        )
        with GoogleProvider(api_key=FAKE_KEY) as p:
            p.directions(
                Waypoint(latitude=42.36, longitude=-71.06, label="A"),
                Waypoint(latitude=42.37, longitude=-71.10, label="B"),
            )

        all_output = "\n".join(r.getMessage() for r in caplog.records)
        assert FAKE_KEY not in all_output

    def test_provider_error_message_is_scrubbed(self) -> None:
        from gotime.providers.base import ProviderError

        err = ProviderError(f"google: failed for url ?key={FAKE_KEY}")
        assert FAKE_KEY not in str(err)
        assert REDACTED in str(err)
