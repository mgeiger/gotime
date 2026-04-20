"""Base protocol for routing providers."""

from __future__ import annotations

import abc
import time
from dataclasses import dataclass
from typing import Any, Literal

import httpx

from gotime.logging import get_logger, httpx_request_hook, redact
from gotime.models import TripResult, Waypoint

_log = get_logger("providers")


class ProviderError(RuntimeError):
    """Raised when a provider fails to return a usable route.

    The ``__str__`` representation is always scrubbed of credentials so an
    error that escapes to a user-facing surface cannot leak an API key via
    (e.g.) an uncaught-exception traceback printed into a log.
    """

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(redact(message))
        # HTTP status code when the error originated from a transport-level
        # failure. ``None`` for semantic errors (e.g. Google's 200 +
        # ``status: REQUEST_DENIED``), which callers classify via the
        # message body.
        self.status_code = status_code


VerificationStatus = Literal["ok", "missing", "invalid", "rate_limited", "unreachable", "error"]


@dataclass(frozen=True, slots=True)
class VerificationResult:
    """Outcome of a single provider key validation probe."""

    provider: str
    status: VerificationStatus
    detail: str | None = None


# Short, deterministic probe pair (~1.1 km in downtown San Francisco) used
# by :meth:`BaseProvider.verify`. Small radius keeps the API bill minimal.
_PROBE_ORIGIN = Waypoint(latitude=37.7749, longitude=-122.4194, label="gotime-verify-origin")
_PROBE_DESTINATION = Waypoint(latitude=37.7849, longitude=-122.4094, label="gotime-verify-destination")


# Substrings typically found in provider error messages when a key is
# rejected as unauthenticated or unauthorized. Matched case-insensitively.
_INVALID_KEY_MARKERS = (
    "request_denied",  # Google
    "api key",
    "apikey",
    "unauthorized",
    "unauthenticated",
    "invalid key",
    "invalid_key",
    "not authorized",
    "forbidden",
    "invalid authentication",
    "invalid credentials",
)


class BaseProvider(abc.ABC):
    """Common base class shared by every provider adapter."""

    #: Short machine-friendly identifier (``"google"``, ``"bing"`` …).
    name: str = ""

    #: Whether the provider can return a separate *duration-in-traffic* value.
    supports_traffic: bool = False

    def __init__(self, api_key: str, client: httpx.Client | None = None, timeout: float = 10.0) -> None:
        if not api_key:
            raise ProviderError(f"{self.name or type(self).__name__} requires an API key")
        self.api_key = api_key
        self._timeout = timeout
        self._owns_client = client is None
        self._client = client or httpx.Client(
            timeout=timeout,
            event_hooks={"request": [httpx_request_hook]},
        )

    # ---- lifecycle ---------------------------------------------------------
    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> BaseProvider:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    # ---- public API --------------------------------------------------------
    @abc.abstractmethod
    def directions(self, origin: Waypoint, destination: Waypoint) -> TripResult:
        """Return a normalized :class:`TripResult` for the requested trip."""

    def verify(self) -> VerificationResult:
        """Issue a minimal probe request to check the current API key.

        The default implementation performs a short SF-based route query via
        :meth:`directions` and classifies the outcome. Providers with a
        dedicated "ping" or account endpoint may override this to avoid
        burning a directions quota.
        """

        try:
            self.directions(_PROBE_ORIGIN, _PROBE_DESTINATION)
        except ProviderError as exc:
            return _classify_provider_error(self.name, exc)
        except (httpx.TimeoutException, httpx.RequestError) as exc:
            return VerificationResult(self.name, "unreachable", str(exc))
        except Exception as exc:  # pragma: no cover - defense in depth
            return VerificationResult(self.name, "error", f"unexpected: {exc!r}")
        return VerificationResult(self.name, "ok")

    # ---- helpers -----------------------------------------------------------
    def _get_json(self, url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        t0 = time.perf_counter()
        try:
            response = self._client.get(url, params=params)
        except httpx.HTTPError as exc:
            raise ProviderError(f"{self.name}: HTTP transport error: {exc}") from exc

        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        _log.info(
            "%s %s %s status=%d elapsed=%.1fms",
            self.name,
            response.request.method,
            response.url.host,
            response.status_code,
            elapsed_ms,
        )

        if response.status_code >= 400:
            raise ProviderError(
                f"{self.name}: HTTP {response.status_code}: {response.text[:200]}",
                status_code=response.status_code,
            )

        try:
            return response.json()
        except ValueError as exc:
            raise ProviderError(f"{self.name}: response was not valid JSON") from exc


def _classify_provider_error(provider: str, exc: ProviderError) -> VerificationResult:
    """Map a :class:`ProviderError` into a :class:`VerificationResult`."""

    detail = str(exc)
    status = exc.status_code
    lowered = detail.lower()

    if status == 429 or "rate" in lowered and "limit" in lowered:
        return VerificationResult(provider, "rate_limited", detail)
    if status in (401, 403):
        return VerificationResult(provider, "invalid", detail)
    if any(marker in lowered for marker in _INVALID_KEY_MARKERS):
        # e.g. Google returns HTTP 200 with ``status: REQUEST_DENIED`` when
        # the key is wrong; HERE and TomTom surface ``Unauthorized`` text.
        return VerificationResult(provider, "invalid", detail)
    if status is not None and 500 <= status < 600:
        return VerificationResult(provider, "unreachable", detail)
    if "transport error" in lowered:
        return VerificationResult(provider, "unreachable", detail)
    return VerificationResult(provider, "error", detail)
