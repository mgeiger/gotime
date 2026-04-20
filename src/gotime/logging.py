"""Logging helpers for gotime with automatic secret redaction.

Every provider passes its API key as a query-string parameter on the outgoing
HTTPS request. If a downstream operator raises ``httpx`` (or this package's own
loggers) to DEBUG level, the raw request URL - key and all - can otherwise land
in logs, tickets, CI output, and observability backends. This module centralises
the redaction so callers never have to think about it.

Public API::

    from gotime.logging import configure_logging, get_logger, redact

The belt-and-braces guarantee is provided by two layers:

1. A :class:`RedactingFilter` attached to every gotime/httpx logger, so records
   get scrubbed before they reach a handler.
2. A monkey-patch of :meth:`logging.LogRecord.getMessage` installed by
   :func:`configure_logging`, so *any* record consumed through the standard
   API - including pytest's ``caplog`` handler - is sanitised on read.

Both layers are idempotent; calling :func:`configure_logging` more than once
is safe and costs nothing.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Iterable

__all__ = [
    "REDACTED",
    "RedactingFilter",
    "configure_logging",
    "get_logger",
    "httpx_request_hook",
    "redact",
]

REDACTED = "***REDACTED***"  # noqa: S105 - placeholder, not a real secret

# Query-string parameters any of the supported providers use to carry secrets.
# Adding a new provider only requires extending this list if it uses a
# previously unseen parameter name.
_SECRET_PARAM_NAMES = (
    "key",
    "apiKey",
    "api_key",
    "access_token",
    "subscription-key",
    "subscription_key",
)

_PARAM_PATTERN = re.compile(
    r"(?i)(?P<name>\b(?:" + "|".join(re.escape(n) for n in _SECRET_PARAM_NAMES) + r"))=(?P<val>[^&\s\"'<>]+)"
)

_BEARER_PATTERN = re.compile(r"(?i)(?P<scheme>Bearer|Basic)\s+(?P<val>[A-Za-z0-9\-\._~+/=]+=*)")

_HEADER_PATTERN = re.compile(
    r"(?i)(?P<name>authorization|x-api-key|ocp-apim-subscription-key)\s*[:=]\s*(?P<val>[^\s,;\"'<>]+)"
)


def redact(text: object) -> str:
    """Return a copy of *text* with any embedded credentials replaced.

    Matches URL-style ``?key=...`` pairs, bare ``Authorization: Bearer xxx``
    / ``Basic xxx`` forms, and common custom header shapes. Idempotent: running
    the result through :func:`redact` again is a no-op.
    """

    if text is None:
        return ""
    s = str(text)
    s = _PARAM_PATTERN.sub(lambda m: f"{m.group('name')}={REDACTED}", s)
    s = _BEARER_PATTERN.sub(lambda m: f"{m.group('scheme')} {REDACTED}", s)
    s = _HEADER_PATTERN.sub(lambda m: f"{m.group('name')}={REDACTED}", s)
    return s


class RedactingFilter(logging.Filter):
    """Logging filter that rewrites record messages through :func:`redact`."""

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: A003 - logging API
        try:
            rendered = record.getMessage()
        except Exception:  # pragma: no cover - extremely defensive
            rendered = str(record.msg)
        record.msg = redact(rendered)
        record.args = ()
        return True


def httpx_request_hook(request) -> None:  # type: ignore[no-untyped-def]
    """``httpx`` event hook that emits a sanitised DEBUG log line per request.

    Attach via ``httpx.Client(event_hooks={"request": [httpx_request_hook]})``.
    The hook never logs the raw URL; it logs scheme+host+path plus the sorted
    parameter *names* only (values are stripped wholesale).
    """

    url = request.url
    safe_params = sorted(set(url.params))
    safe = f"{url.scheme}://{url.host}{url.path}?{','.join(safe_params)}"
    get_logger("httpx").debug("request %s %s", request.method, safe)


_CONFIGURED = False
_ORIGINAL_GET_MESSAGE: object | None = None


def _install_record_patch() -> None:
    """Monkey-patch :meth:`logging.LogRecord.getMessage` to always redact."""

    global _ORIGINAL_GET_MESSAGE
    if _ORIGINAL_GET_MESSAGE is not None:
        return

    original = logging.LogRecord.getMessage

    def _patched(self: logging.LogRecord) -> str:
        return redact(original(self))

    _ORIGINAL_GET_MESSAGE = original
    logging.LogRecord.getMessage = _patched  # type: ignore[method-assign]


def configure_logging(level: int = logging.INFO, extra_loggers: Iterable[str] = ()) -> None:
    """Install the redacting filter on gotime + httpx + any extra loggers.

    Also installs a process-wide :class:`logging.LogRecord.getMessage` wrapper
    so alternate handlers (pytest's ``caplog``, uvicorn's default handler,
    anything that reads ``record.getMessage()`` directly) also see the scrubbed
    payload. Idempotent.
    """

    global _CONFIGURED
    if not _CONFIGURED:
        logging.basicConfig(
            level=level,
            format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        )
        _install_record_patch()
        _CONFIGURED = True

    redacting = RedactingFilter()
    for name in ("gotime", "httpx", "httpcore", *extra_loggers):
        logger = logging.getLogger(name)
        if not any(isinstance(f, RedactingFilter) for f in logger.filters):
            logger.addFilter(redacting)


def get_logger(name: str) -> logging.Logger:
    """Return a gotime logger with the redacting filter guaranteed-attached."""

    full = name if name.startswith("gotime") else f"gotime.{name}"
    logger = logging.getLogger(full)
    if not any(isinstance(f, RedactingFilter) for f in logger.filters):
        logger.addFilter(RedactingFilter())
    return logger
