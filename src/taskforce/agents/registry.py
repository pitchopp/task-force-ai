import logging
from pathlib import Path

from taskforce.agents.factory import AgentConfig, AGENTS_DIR, load_all_configs

logger = logging.getLogger(__name__)


class AgentRegistry:
    """Holds all loaded agent configs and provides lookup."""

    def __init__(self) -> None:
        self._agents: dict[str, AgentConfig] = {}

    def load(self, agents_dir: Path = AGENTS_DIR) -> None:
        """Load all agent configs from disk."""
        self._agents.clear()
        for config in load_all_configs(agents_dir):
            self._agents[config.name] = config
        logger.info("Registry loaded %d agents: %s", len(self._agents), list(self._agents.keys()))

    def register(self, config: AgentConfig) -> None:
        """Register a single agent config (e.g. from evolution)."""
        self._agents[config.name] = config
        logger.info("Registered agent: %s", config.name)

    def get(self, name: str) -> AgentConfig | None:
        return self._agents.get(name)

    def all(self) -> dict[str, AgentConfig]:
        return dict(self._agents)

    def find_by_capability(self, capability: str) -> list[AgentConfig]:
        return [a for a in self._agents.values() if capability in a.capabilities]

    @property
    def names(self) -> list[str]:
        return list(self._agents.keys())


# Singleton
registry = AgentRegistry()
