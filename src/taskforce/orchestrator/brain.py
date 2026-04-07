import logging
from typing import Any

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    PermissionResultAllow,
    TextBlock,
    ToolPermissionContext,
    ToolUseBlock,
)

from config.settings import get_settings
from taskforce.agents.registry import registry

logger = logging.getLogger(__name__)

BRAIN_SYSTEM_PROMPT = """\
Tu es le "bras droit" de l'utilisateur dans le systeme TaskForce AI.
Tu es un orchestrateur : tu ne fais PAS le travail toi-meme sauf pour les questions triviales \
(salutations, questions simples de culture generale, clarifications).

## Ton role
1. Comprendre l'intention de l'utilisateur.
2. Si un agent specialise peut traiter la demande, delegue-lui via l'outil Agent \
et informe l'utilisateur de la delegation (ex: "Je confie ca a l'agent X...").
3. Si AUCUN agent ne correspond, propose a l'utilisateur d'en creer un. \
Decris quel agent serait utile, ses capacites, et demande validation. \
Si l'utilisateur valide, appelle l'outil flag_capability_gap.
4. Ne reponds directement que pour les demandes triviales qui ne necessitent pas d'agent.

## Regles
- Reponds toujours en francais sauf si l'utilisateur parle dans une autre langue.
- Sois concis et actionnable.
- Quand tu delegues, dis clairement a qui et pourquoi.
- Quand tu proposes un nouvel agent, sois precis sur ce qu'il ferait.

## Agents disponibles
{available_agents}
"""


def _build_system_prompt() -> str:
    agents = registry.all()
    if not agents:
        agents_desc = (
            "Aucun agent specialise disponible pour le moment. "
            "Si la demande necessite un traitement specifique, "
            "propose a l'utilisateur de creer un agent adapte."
        )
    else:
        lines = []
        for name, config in agents.items():
            caps = ", ".join(config.capabilities) if config.capabilities else "general"
            lines.append(f"- **{name}** ({caps}): {config.description}")
        agents_desc = "\n".join(lines)

    return BRAIN_SYSTEM_PROMPT.format(available_agents=agents_desc)


def _format_history(messages) -> str:
    from langchain_core.messages import AIMessage, HumanMessage

    parts: list[str] = []
    for msg in messages[:-1]:
        if isinstance(msg, HumanMessage):
            parts.append(f"[Utilisateur]: {msg.content}")
        elif isinstance(msg, AIMessage):
            parts.append(f"[Assistant]: {msg.content}")

    return "\n".join(parts)


async def _auto_approve_tool(
    tool_name: str,
    tool_input: dict[str, Any],
    context: ToolPermissionContext,
) -> PermissionResultAllow:
    """Auto-approve all tool calls. Needed because bypassPermissions is blocked as root in Docker."""
    return PermissionResultAllow()


async def think(user_message: str, messages=None) -> str:
    settings = get_settings()

    prompt = user_message
    if messages and len(messages) > 1:
        history = _format_history(messages)
        prompt = f"Historique de la conversation:\n{history}\n\nNouveau message de l'utilisateur:\n{user_message}"

    options = ClaudeAgentOptions(
        system_prompt=_build_system_prompt(),
        model=settings.brain_model,
        permission_mode="default",
        can_use_tool=_auto_approve_tool,
    )

    full_response = ""
    last_final_text = ""

    async with ClaudeSDKClient(options=options) as client:
        await client.query(prompt)
        async for message in client.receive_response():
            if not isinstance(message, AssistantMessage):
                continue

            text_parts = [
                block.text for block in message.content if isinstance(block, TextBlock)
            ]
            tool_uses = [
                block for block in message.content if isinstance(block, ToolUseBlock)
            ]
            chunk = "".join(text_parts).strip()

            if chunk:
                full_response += ("\n\n" if full_response else "") + chunk

            if tool_uses:
                for tool in tool_uses:
                    logger.info("agent tool: %s input=%r", tool.name, tool.input)
                continue

            if chunk:
                last_final_text = chunk

    return last_final_text or full_response or "Je n'ai pas pu traiter cette demande."
