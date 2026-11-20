from functools import lru_cache
from pydantic_settings import  BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """API keys and options, read from the environment or .env.

    Any key left unset just means that platform is skipped.
    """

    model_config = SettingsConfigDict(env_file=".env",extra = "ignore")


    request_timeout_seconds: float = 15.0

    telegram_bot_token: str | None = None
    telegram_channel: str | None = None

    mastodon_base_url: str = "https://mastodon.social"
    mastodon_access_token: str | None = None

    bluesky_handle: str | None = None
    bluesky_app_password: str | None = None

    github_token: str | None = None
    devto_api_key: str | None = None

    discord_webhook_url: str | None = None


def get_settings() -> Settings:
    """Load settings. Used as a FastAPI dependency so tests can override it."""
    return  Settings()

