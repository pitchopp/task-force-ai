from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from config.settings import get_settings


@asynccontextmanager
async def get_checkpointer() -> AsyncIterator[AsyncPostgresSaver]:
    """Yield a PostgreSQL checkpointer as an async context manager."""
    settings = get_settings()
    # psycopg expects plain postgresql:// URL (not the +psycopg SQLAlchemy dialect)
    conn_string = settings.database_url_sync.replace("+psycopg", "")
    async with AsyncPostgresSaver.from_conn_string(conn_string) as checkpointer:
        await checkpointer.setup()
        yield checkpointer
