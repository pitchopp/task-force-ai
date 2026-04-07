FROM python:3.14-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files first for better caching
COPY pyproject.toml uv.lock* ./

# Install dependencies
RUN uv sync --no-dev --frozen

# Copy source
COPY config/ config/
COPY src/ src/
COPY alembic/ alembic/
COPY alembic.ini ./

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "taskforce.main:app", "--host", "0.0.0.0", "--port", "8000"]
