from functools import lru_cache
from pydantic_settings import  BaseSettings, SettingsConfigDict

class Settings(BaseSettings):

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
    return  Settings()

