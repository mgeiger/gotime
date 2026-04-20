"""Live API-key validation helpers.

Each provider's :meth:`BaseProvider.verify` makes a small probe request
and reports one of:

* ``ok``          - key is valid and accepted
* ``missing``     - no key configured for that provider
* ``invalid``     - key rejected (HTTP 401/403 or Google REQUEST_DENIED)
* ``rate_limited`` - HTTP 429; key is valid, just throttled
* ``unreachable`` - network failure, DNS, TLS, or 5xx from upstream
* ``error``       - everything else, usually a malformed response

These helpers are also available under :func:`gotime.verify_keys`. The CLI
wrappers in :mod:`gotime.cli` format the results as a Rich table or JSON.
"""

from __future__ import annotations

from collections.abc import Iterable

from gotime.config import Settings
from gotime.providers.base import BaseProvider, VerificationResult
from gotime.providers.registry import available_providers, get_provider


def verify_keys(
    settings: Settings,
    providers: Iterable[str] | None = None,
    *,
    timeout: float = 10.0,
    client_factory: type[BaseProvider] | None = None,
) -> list[VerificationResult]:
    """Probe every configured provider and return one result per request.

    ``providers`` defaults to every registered adapter. Providers without a
    configured key are reported as ``missing`` without issuing a network
    request.

    ``client_factory`` is only useful for tests that need to inject a stub
    provider class (same escape hatch as :func:`gotime.query_providers`).
    """

    names = list(providers) if providers is not None else available_providers()
    results: list[VerificationResult] = []
    for name in names:
        key = settings.api_key_for(name)
        if key is None:
            results.append(VerificationResult(name, "missing", "no API key configured"))
            continue
        try:
            provider_cls = client_factory or get_provider(name)
        except KeyError as exc:
            results.append(VerificationResult(name, "error", str(exc)))
            continue

        try:
            with provider_cls(api_key=key, timeout=timeout) as provider:
                results.append(provider.verify())
        except Exception as exc:  # pragma: no cover - defensive
            results.append(VerificationResult(name, "error", f"unexpected: {exc!r}"))
    return results
