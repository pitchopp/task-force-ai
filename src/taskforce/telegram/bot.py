from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config.settings import get_settings
from taskforce.telegram.callbacks import router as callbacks_router
from taskforce.telegram.handlers import router as main_router
from taskforce.telegram.middleware import AuthMiddleware


def create_dispatcher() -> Dispatcher:
    settings = get_settings()
    dp = Dispatcher()
    dp.update.outer_middleware(AuthMiddleware(settings.allowed_user_ids))
    dp.include_router(callbacks_router)
    dp.include_router(main_router)
    return dp


def create_bot() -> Bot:
    settings = get_settings()
    return Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
