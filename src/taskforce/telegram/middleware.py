import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseMiddleware):
    """Reject updates from users not in the allowed list."""

    def __init__(self, allowed_user_ids: list[int]) -> None:
        self.allowed_user_ids = set(allowed_user_ids)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not self.allowed_user_ids:
            return await handler(event, data)

        user_id: int | None = None
        if isinstance(event, Update):
            if event.message and event.message.from_user:
                user_id = event.message.from_user.id
            elif event.callback_query and event.callback_query.from_user:
                user_id = event.callback_query.from_user.id

        if user_id is not None and user_id not in self.allowed_user_ids:
            logger.warning("Unauthorized access attempt from user_id=%d", user_id)
            return None

        return await handler(event, data)
