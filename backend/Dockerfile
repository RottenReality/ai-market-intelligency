FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH" \
    MPLCONFIGDIR=/tmp/matplotlib \
    DB_PATH=/data/app.sqlite

WORKDIR /app

# Dependencies first (cached layer), then the application.
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project

# config/ includes the private company profile when it exists on the build machine
# (company.yaml / company.md are gitignored, never committed).
COPY app ./app
COPY config ./config
COPY data ./data

RUN useradd --create-home app && mkdir /data && chown app /data
USER app

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
