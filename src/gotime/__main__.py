"""Entry point for ``python -m gotime``."""

from gotime.cli import app


def main() -> None:
    app()


if __name__ == "__main__":  # pragma: no cover - exercised via CLI tests
    main()
