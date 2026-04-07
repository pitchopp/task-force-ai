import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from config.settings import get_settings
from taskforce.agents.registry import registry
from taskforce.telegram.bot import create_bot, create_dispatcher

logger = logging.getLogger(__name__)

bot = create_bot()
dp = create_dispatcher()

# Will hold the compiled graph with checkpointer once lifespan starts
compiled_graph = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    global compiled_graph
    settings = get_settings()

    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )

    # Load agent configs
    registry.load()
    logger.info("Agent registry loaded: %s", registry.names)

    # Initialize LangGraph checkpointer and compile graph
    from taskforce.graph.checkpointer import get_checkpointer
    from taskforce.graph.workflow import compile_graph

    async with get_checkpointer() as checkpointer:
        compiled_graph = compile_graph(checkpointer=checkpointer)
        logger.info("LangGraph checkpointer ready")

        if settings.use_webhook:
            await bot.set_webhook(
                url=f"{settings.webhook_url}/webhook",
                drop_pending_updates=True,
            )
            logger.info("Webhook set to %s/webhook", settings.webhook_url)
        else:
            logger.info("Starting polling mode")
            asyncio.create_task(_run_polling())

        yield

        # Shutdown
        compiled_graph = None

    from taskforce.storage.redis_client import close_redis
    from taskforce.storage.database import dispose_engine

    await close_redis()
    await dispose_engine()

    if settings.use_webhook:
        await bot.delete_webhook()
    await bot.session.close()
    logger.info("TaskForce AI shut down")


async def _run_polling() -> None:
    await dp.start_polling(bot)


app = FastAPI(title="TaskForce AI", version="0.1.0", lifespan=lifespan)

from taskforce.api.routes import router as api_router  # noqa: E402

app.include_router(api_router)
