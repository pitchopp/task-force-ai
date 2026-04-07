import logging

from aiogram import Router
from aiogram.enums import ChatAction, ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message
from langchain_core.messages import HumanMessage

logger = logging.getLogger(__name__)

router = Router(name="main")


async def _send_markdown(message: Message, text: str) -> None:
    """Send a message as Markdown, fallback to plain text if Telegram rejects it."""
    for i in range(0, len(text), 4000):
        chunk = text[i : i + 4000]
        try:
            await message.answer(chunk, parse_mode=ParseMode.MARKDOWN)
        except Exception:
            await message.answer(chunk)


@router.message(CommandStart())
async def handle_start(message: Message) -> None:
    await message.answer(
        "TaskForce AI en ligne. Envoie-moi un message et je m'en occupe."
    )


@router.message()
async def handle_message(message: Message) -> None:
    if not message.text:
        await message.answer("Je ne peux traiter que les messages texte pour le moment.")
        return

    user_id = message.from_user.id if message.from_user else 0
    chat_id = message.chat.id
    thread_id = f"tg_{chat_id}"

    await message.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

    try:
        from taskforce.main import compiled_graph as graph

        if graph is None:
            await message.answer("Le systeme n'est pas encore pret. Reessaie dans quelques secondes.")
            return

        config = {"configurable": {"thread_id": thread_id}}

        result = await graph.ainvoke(
            {
                "messages": [HumanMessage(content=message.text)],
                "chat_id": chat_id,
                "user_id": user_id,
                "thread_id": thread_id,
                "response": "",
                "needs_approval": False,
                "approval_id": "",
                "approval_action": "",
                "approval_decision": "",
            },
            config=config,
        )

        response_text = result.get("response", "")
        if not response_text:
            response_text = "Traitement termine sans reponse."

        await _send_markdown(message, response_text)

    except Exception:
        logger.exception("Error processing message")
        await message.answer("Erreur lors du traitement. Verifie les logs.")
