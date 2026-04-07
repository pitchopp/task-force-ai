import logging
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel

logger = logging.getLogger(__name__)

AGENTS_DIR = Path(__file__).resolve().parents[3] / "config" / "agents"


class AgentConfig(BaseModel):
    name: str
    description: str
    system_prompt: str
    tools: list[str] = []
    model: str = "claude-sonnet-4-6"
    risk_level: str = "low"
    max_turns: int = 30
    capabilities: list[str] = []
    limitations: list[str] = []


def load_agent_config(path: Path) -> AgentConfig | None:
    """Load a single agent config from a YAML file."""
    try:
        data: dict[str, Any] = yaml.safe_load(path.read_text())
        return AgentConfig(**data)
    except Exception:
        logger.exception("Failed to load agent config from %s", path)
        return None


def load_all_configs(agents_dir: Path = AGENTS_DIR) -> list[AgentConfig]:
    """Load all agent configs from the agents directory, skipping templates."""
    configs: list[AgentConfig] = []
    if not agents_dir.exists():
        logger.warning("Agents directory not found: %s", agents_dir)
        return configs

    for path in sorted(agents_dir.glob("*.yaml")):
        if path.name.startswith("_"):
            continue
        config = load_agent_config(path)
        if config:
            configs.append(config)
            logger.info("Loaded agent config: %s", config.name)

    return configs


def generate_agent_yaml(
    name: str,
    description: str,
    system_prompt: str,
    tools: list[str] | None = None,
    model: str = "claude-sonnet-4-6",
    risk_level: str = "low",
    capabilities: list[str] | None = None,
) -> str:
    """Generate a YAML string for a new agent config."""
    config = {
        "name": name,
        "description": description,
        "system_prompt": system_prompt,
        "tools": tools or ["Read", "Glob", "Grep"],
        "model": model,
        "risk_level": risk_level,
        "max_turns": 30,
        "capabilities": capabilities or [],
        "limitations": [],
    }
    return yaml.dump(config, default_flow_style=False, allow_unicode=True, sort_keys=False)
