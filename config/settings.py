from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    # Telegram
    bot_token: str
    webhook_url: str = ""
    allowed_user_ids: list[int] = []

    # Anthropic — API key is optional.
    # Priority: OAuth via ~/.claude/.credentials.json (Max subscription),
    # then ANTHROPIC_API_KEY as fallback.
    anthropic_api_key: str = ""

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/taskforce"
    database_url_sync: str = "postgresql+psycopg://postgres:postgres@localhost:5432/taskforce"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Brain
    brain_model: str = "claude-sonnet-4-6"
    brain_max_tokens: int = 8192

    # App
    debug: bool = False
    log_level: str = "INFO"

    @property
    def use_webhook(self) -> bool:
        return bool(self.webhook_url)


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
