import logging

from aiogram import Router
from aiogram.types import CallbackQuery

from taskforce.orchestrator.approval import submit_decision

logger = logging.getLogger(__name__)

router = Router(name="callbacks")


@router.callback_query(lambda c: c.data and c.data.startswith("approve_"))
async def handle_approve(query: CallbackQuery) -> None:
    approval_id = query.data.removeprefix("approve_")  # type: ignore[union-attr]
    ok = await submit_decision(approval_id, "approved")

    if ok:
        await query.message.edit_text("Approved. Executing...")  # type: ignore[union-attr]
    else:
        await query.message.edit_text("Approval request expired.")  # type: ignore[union-attr]
    await query.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("deny_"))
async def handle_deny(query: CallbackQuery) -> None:
    approval_id = query.data.removeprefix("deny_")  # type: ignore[union-attr]
    ok = await submit_decision(approval_id, "denied")

    if ok:
        await query.message.edit_text("Denied. Action cancelled.")  # type: ignore[union-attr]
    else:
        await query.message.edit_text("Approval request expired.")  # type: ignore[union-attr]
    await query.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("create_agent_"))
async def handle_create_agent(query: CallbackQuery) -> None:
    """Handle 'Create Agent' button from evolution suggestions."""
    agent_data = query.data.removeprefix("create_agent_")  # type: ignore[union-attr]

    from taskforce.agents.evolution import create_agent_from_suggestion

    config = create_agent_from_suggestion(
        name=agent_data,
        description=f"Agent specialise: {agent_data}",
        system_prompt=f"Tu es un agent specialise dans le domaine: {agent_data}. Aide l'utilisateur au mieux.",
    )

    if config:
        await query.message.edit_text(f"Agent '{config.name}' cree et disponible.")  # type: ignore[union-attr]
    else:
        await query.message.edit_text(f"L'agent '{agent_data}' existe deja.")  # type: ignore[union-attr]
    await query.answer()
