FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv

# System dependencies:
# - ripgrep       : used by the SDK's Grep tool
# - curl, gnupg   : for NodeSource installer
# - nodejs         : required by Claude Agent SDK (spawns Claude Code CLI)
RUN apt-get update && apt-get install -y --no-install-recommends \
        ripgrep \
        curl \
        ca-certificates \
        gnupg \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key \
        | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main" \
        > /etc/apt/sources.list.d/nodesource.list \
    && apt-get update && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install Claude Code CLI globally (required runtime for the Agent SDK)
RUN npm install -g @anthropic-ai/claude-code

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Install Python deps
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

# Install the project
COPY config/ config/
COPY src/ src/
COPY alembic/ alembic/
COPY alembic.ini ./
RUN uv sync --frozen --no-dev

ENV PATH="/opt/venv/bin:$PATH"

# Claude auth: mount OAuth credentials at /root/.claude/.credentials.json
# via Dokploy File Mount to use Claude Max/Pro subscription.

EXPOSE 8000

CMD ["uvicorn", "taskforce.main:app", "--host", "0.0.0.0", "--port", "8000"]
