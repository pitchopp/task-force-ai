import logging
from pathlib import Path

from taskforce.agents.factory import AGENTS_DIR, AgentConfig, generate_agent_yaml, load_agent_config
from taskforce.agents.registry import registry

logger = logging.getLogger(__name__)


def create_agent_from_suggestion(
    name: str,
    description: str,
    system_prompt: str,
    tools: list[str] | None = None,
    model: str = "claude-sonnet-4-6",
    risk_level: str = "low",
    capabilities: list[str] | None = None,
) -> AgentConfig | None:
    """Create a new agent YAML config file and register it in the registry."""
    slug = name.lower().replace(" ", "-").replace("_", "-")
    path = AGENTS_DIR / f"{slug}.yaml"

    if path.exists():
        logger.warning("Agent config already exists: %s", path)
        return None

    yaml_content = generate_agent_yaml(
        name=slug,
        description=description,
        system_prompt=system_prompt,
        tools=tools,
        model=model,
        risk_level=risk_level,
        capabilities=capabilities,
    )

    AGENTS_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml_content)
    logger.info("Created agent config: %s", path)

    config = load_agent_config(path)
    if config:
        registry.register(config)
    return config
