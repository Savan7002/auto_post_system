from app.platforms.base import BasePlatform
from app.schemas import PlatformResult


class TelegramPlatform(BasePlatform):
    """Post to a Telegram channel through a bot. The bot has to be an admin of the channel."""

    name = "Telegram"

    def is_configured(self) -> bool:
        return bool(self.settings.telegram_bot_token and self.settings.telegram_channel)

    async def publish(self, message: str) -> PlatformResult:
        # The Bot API takes the token in the URL path, not in a header.
        url = f"https://api.telegram.org/bot{self.settings.telegram_bot_token}/sendMessage"

        response = await self.client.post(
            url,
            json={"chat_id": self.settings.telegram_channel, "text": message},
        )
        response.raise_for_status()

        result = response.json()["result"]
        username = result["chat"].get("username")

        # Only public channels have a username, and t.me links need one.
        if username:
            return self._success(f"https://t.me/{username}/{result['message_id']}", public_access=True)
        return self._success(None, public_access=False)