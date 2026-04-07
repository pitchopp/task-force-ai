import logging
from typing import Any

from claude_agent_sdk import (
    AgentDefinition,
    ClaudeAgentOptions,
    AssistantMessage,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
    query,
)

from config.settings import get_settings
from taskforce.agents.registry import registry

logger = logging.getLogger(__name__)

BRAIN_SYSTEM_PROMPT = """\
Tu es le "bras droit" de l'utilisateur dans le systeme TaskForce AI.
Ton role est de comprendre ses instructions, planifier l'execution, et repondre de maniere claire et utile.

## Regles
1. Reponds toujours en francais sauf si l'utilisateur parle dans une autre langue.
2. Pour les questions simples, reponds directement.
3. Pour les taches complexes, decompose-les et explique ton approche.
4. Si tu ne peux pas accomplir une tache avec tes capacites actuelles, dis-le clairement \
et suggere quel type d'agent specialise pourrait aider.
5. Sois concis et actionnable dans tes reponses.

## Agents disponibles
{available_agents}
"""


def _build_system_prompt() -> str:
    """Build the brain's system prompt with current agent registry info."""
    agents = registry.all()
    if not agents:
        agents_desc = "Aucun agent specialise disponible pour le moment."
    else:
        lines = []
        for name, config in agents.items():
            lines.append(f"- **{name}**: {config.description}")
        agents_desc = "\n".join(lines)

    return BRAIN_SYSTEM_PROMPT.format(available_agents=agents_desc)


def _build_subagents() -> dict[str, AgentDefinition]:
    """Convert registry configs to Claude Agent SDK AgentDefinitions."""
    agents: dict[str, AgentDefinition] = {}
    for name, config in registry.all().items():
        agents[name] = AgentDefinition(
            description=config.description,
            prompt=config.system_prompt,
            tools=config.tools or None,
            model=_map_model(config.model),
        )
    return agents


def _map_model(model: str) -> str | None:
    """Map model config string to SDK model hint."""
    mapping = {
        "claude-opus-4-6": "opus",
        "claude-sonnet-4-6": "sonnet",
        "claude-haiku-4-5": "haiku",
    }
    return mapping.get(model, None)


def _format_history(messages) -> str:
    """Format LangGraph message history into a prompt for the SDK."""
    from langchain_core.messages import HumanMessage, AIMessage

    parts: list[str] = []
    for msg in messages[:-1]:  # All except the last (current) message
        if isinstance(msg, HumanMessage):
            parts.append(f"[Utilisateur]: {msg.content}")
        elif isinstance(msg, AIMessage):
            parts.append(f"[Assistant]: {msg.content}")

    return "\n".join(parts)


async def think(user_message: str, messages=None) -> str:
    """
    Process a user message through the Brain agent using Claude Agent SDK.
    Includes conversation history for continuity.
    """
    settings = get_settings()
    subagents = _build_subagents()

    allowed_tools = ["WebSearch", "WebFetch"]
    if subagents:
        allowed_tools.append("Agent")

    # Build prompt with history for conversation continuity
    prompt = user_message
    if messages and len(messages) > 1:
        history = _format_history(messages)
        prompt = f"Historique de la conversation:\n{history}\n\nNouveau message de l'utilisateur:\n{user_message}"

    options = ClaudeAgentOptions(
        system_prompt=_build_system_prompt(),
        model=settings.brain_model,
        allowed_tools=allowed_tools,
        agents=subagents if subagents else None,
        permission_mode="bypassPermissions",
    )

    result_text = ""

    async for message in query(prompt=prompt, options=options):
        if isinstance(message, ResultMessage):
            if message.subtype == "success" and message.result:
                result_text = message.result

    return result_text or "Je n'ai pas pu traiter cette demande."
