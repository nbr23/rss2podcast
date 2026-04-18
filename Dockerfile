FROM python:3.14-slim AS base

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libxml2 libxslt1.1 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY src ./src

FROM base AS test
RUN uv sync --group test
COPY tests ./tests

FROM base AS production
RUN uv sync --no-dev

VOLUME ["/data"]
ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["uv", "run", "rss2podcast"]
