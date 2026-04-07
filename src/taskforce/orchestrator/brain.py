import logging

from claude_agent_sdk import (
    AgentDefinition,
    ClaudeAgentOptions,
    ResultMessage,
    query,
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


def _build_subagents() -> dict[str, AgentDefinition]:
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
    mapping = {
        "claude-opus-4-6": "opus",
        "claude-sonnet-4-6": "sonnet",
        "claude-haiku-4-5": "haiku",
    }
    return mapping.get(model, None)


def _format_history(messages) -> str:
    from langchain_core.messages import AIMessage, HumanMessage

    parts: list[str] = []
    for msg in messages[:-1]:
        if isinstance(msg, HumanMessage):
            parts.append(f"[Utilisateur]: {msg.content}")
        elif isinstance(msg, AIMessage):
            parts.append(f"[Assistant]: {msg.content}")

    return "\n".join(parts)


async def think(user_message: str, messages=None) -> str:
    settings = get_settings()
    subagents = _build_subagents()

    allowed_tools = ["WebSearch", "WebFetch"]
    if subagents:
        allowed_tools.append("Agent")

    # Build prompt with history
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
