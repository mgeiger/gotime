# syntax=docker/dockerfile:1.7

FROM python:3.13-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY pyproject.toml README.md LICENSE CHANGELOG.md ./
COPY src ./src
COPY tests ./tests

RUN pip install --upgrade pip && pip install --editable ".[dev]"

CMD ["pytest"]
