from aiogram.types import Update
from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/webhook")
async def telegram_webhook(request: Request) -> dict[str, bool]:
    from taskforce.main import bot, dp

    update = Update.model_validate(await request.json(), context={"bot": bot})
    await dp.feed_update(bot, update)
    return {"ok": True}
