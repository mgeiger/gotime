"""Typer-powered command-line interface for gotime.

Run ``gotime --help`` for the full command tree. Example:

.. code-block:: bash

    gotime providers list
    gotime query \\
        --origin 42.3554,-71.0654 \\
        --destination 42.3467,-71.0972 \\
        --provider google --provider tomtom
"""

from __future__ import annotations

import json
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from gotime import __version__
from gotime.config import load_settings
from gotime.models import Waypoint
from gotime.providers.base import ProviderError, VerificationResult
from gotime.providers.registry import available_providers
from gotime.services.query import query_providers
from gotime.services.verify import verify_keys

app = typer.Typer(
    name="gotime",
    help="Multi-provider driving-directions CLI.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)
providers_app = typer.Typer(help="Inspect registered routing providers.")
db_app = typer.Typer(help="Database utilities.")
app.add_typer(providers_app, name="providers")
app.add_typer(db_app, name="db")

console = Console()


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(__version__)
        raise typer.Exit()


@app.callback()
def _main(
    version: Annotated[
        bool,
        typer.Option("--version", callback=_version_callback, is_eager=True, help="Show version and exit."),
    ] = False,
) -> None:
    """gotime command-line entry point."""


def _parse_waypoint(value: str, *, label: str | None = None) -> Waypoint:
    try:
        lat_str, lon_str = value.split(",", 1)
        return Waypoint(latitude=float(lat_str), longitude=float(lon_str), label=label)
    except ValueError as exc:
        raise typer.BadParameter(f"expected 'lat,lon', got {value!r}") from exc


@providers_app.command("list")
def providers_list() -> None:
    """List all registered providers."""

    table = Table(title="gotime providers")
    table.add_column("Provider", style="cyan", no_wrap=True)
    table.add_column("Traffic?", style="green")
    settings = load_settings()
    for name in available_providers():
        key_present = "yes" if settings.api_key_for(name) else "no"
        table.add_row(name, f"key configured: {key_present}")
    console.print(table)


_STATUS_STYLE: dict[str, str] = {
    "ok": "green",
    "missing": "yellow",
    "rate_limited": "yellow",
    "invalid": "red",
    "unreachable": "red",
    "error": "red",
}
# Statuses that should *not* cause a non-zero exit code. ``missing`` and
# ``rate_limited`` still mean "credentials look fine" (no key configured, or
# key accepted but throttled), so they don't fail the gate.
_NON_FAILING = {"ok", "missing", "rate_limited"}


def _run_verify(providers: list[str], as_json: bool, timeout: float) -> None:
    """Shared implementation for `providers verify` and `verify-keys`."""

    settings = load_settings()
    chosen = [p.strip().lower() for p in providers] or available_providers()
    results = verify_keys(settings, chosen, timeout=timeout)

    if as_json:
        typer.echo(json.dumps([_result_to_dict(r) for r in results], indent=2))
    else:
        _render_verify_table(results)

    if any(r.status not in _NON_FAILING for r in results):
        raise typer.Exit(code=1)


def _result_to_dict(result: VerificationResult) -> dict[str, str | None]:
    return {"provider": result.provider, "status": result.status, "detail": result.detail}


def _render_verify_table(results: list[VerificationResult]) -> None:
    table = Table(title="gotime key verification")
    table.add_column("Provider", style="cyan", no_wrap=True)
    table.add_column("Status")
    table.add_column("Detail", overflow="fold")
    for r in results:
        style = _STATUS_STYLE.get(r.status, "white")
        table.add_row(r.provider, f"[{style}]{r.status}[/{style}]", r.detail or "")
    console.print(table)


@providers_app.command("verify")
def providers_verify(
    provider: Annotated[
        list[str],
        typer.Option("--provider", "-p", help="Provider name. Repeat to verify multiple. Default: all."),
    ] = [],  # noqa: B006  # Typer requires a literal default.
    as_json: Annotated[bool, typer.Option("--json", help="Emit JSON instead of a table.")] = False,
    timeout: Annotated[float, typer.Option("--timeout", help="Per-provider HTTP timeout in seconds.")] = 10.0,
) -> None:
    """Probe each provider's API to confirm its configured key is accepted.

    Exits non-zero if any provider returns ``invalid``, ``unreachable`` or
    ``error`` - suitable for use as a deploy gate.
    """

    _run_verify(provider, as_json=as_json, timeout=timeout)


@app.command("verify-keys")
def verify_keys_cmd(
    provider: Annotated[
        list[str],
        typer.Option("--provider", "-p", help="Provider name. Repeat to verify multiple. Default: all."),
    ] = [],  # noqa: B006  # Typer requires a literal default.
    as_json: Annotated[bool, typer.Option("--json", help="Emit JSON instead of a table.")] = False,
    timeout: Annotated[float, typer.Option("--timeout", help="Per-provider HTTP timeout in seconds.")] = 10.0,
) -> None:
    """Alias for ``gotime providers verify`` - same flags, same behaviour."""

    _run_verify(provider, as_json=as_json, timeout=timeout)


@db_app.command("info")
def db_info() -> None:
    """Show the resolved database URL (safe: never prints credentials)."""

    settings = load_settings()
    url = settings.database_url
    # Redact credentials for output.
    if "@" in url and "://" in url:
        scheme, rest = url.split("://", 1)
        creds, host = rest.split("@", 1)
        redacted = f"{scheme}://***@{host}"
    else:
        redacted = url
    console.print(f"[bold]database_url[/bold]: {redacted}")


@app.command("query")
def query(
    origin: Annotated[str, typer.Option(help="Origin as 'lat,lon'.")],
    destination: Annotated[str, typer.Option(help="Destination as 'lat,lon'.")],
    provider: Annotated[
        list[str],
        typer.Option("--provider", "-p", help="Provider name. Repeat to query multiple."),
    ] = [],  # noqa: B006  # Typer requires a literal default; list is re-built on each invocation.
    origin_label: Annotated[str | None, typer.Option(help="Friendly label for the origin.")] = None,
    destination_label: Annotated[str | None, typer.Option(help="Friendly label for the destination.")] = None,
    as_json: Annotated[bool, typer.Option("--json", help="Emit JSON instead of a table.")] = False,
) -> None:
    """Query one or more providers for a single origin/destination pair."""

    origin_wp = _parse_waypoint(origin, label=origin_label)
    dest_wp = _parse_waypoint(destination, label=destination_label)
    chosen = provider or available_providers()
    settings = load_settings()

    results = query_providers(origin_wp, dest_wp, chosen, settings)

    if as_json:
        payload: dict[str, object] = {}
        for name, value in results.items():
            if isinstance(value, ProviderError):
                payload[name] = {"error": str(value)}
            else:
                payload[name] = value.to_dict()
        typer.echo(json.dumps(payload, indent=2, default=str))
        return

    table = Table(title=f"{origin_wp.as_pair()} → {dest_wp.as_pair()}")
    table.add_column("Provider", style="cyan")
    table.add_column("Duration (min)", justify="right")
    table.add_column("In-traffic (min)", justify="right")
    table.add_column("Distance (mi)", justify="right")
    table.add_column("Notes")

    for name, value in results.items():
        if isinstance(value, ProviderError):
            table.add_row(name, "-", "-", "-", f"[red]{value}[/red]")
            continue
        table.add_row(
            name,
            f"{value.duration_minutes:.2f}",
            f"{value.duration_in_traffic_minutes:.2f}" if value.duration_in_traffic_minutes else "-",
            f"{value.distance_miles:.2f}",
            "ok",
        )
    console.print(table)
