from app.platforms.base import BasePlatform
from app.schemas import PlatformResult


class TelegramPlatform(BasePlatform):
    name = "Telegram"

    def is_configured(self) -> bool:
        return bool(self.settings.telegram_bot_token and self.settings.telegram_channel)

    async def publish(self, message: str) -> PlatformResult:
        url = f"https://api.telegram.org/bot{self.settings.telegram_bot_token}/sendMessage"

        response = await self.client.post(
            url,
            json={"chat_id": self.settings.telegram_channel, "text": message},
        )
        response.raise_for_status()

        result = response.json()["result"]
        username = result["chat"].get("username")

        if username:
            return self._success(f"https://t.me/{username}/{result['message_id']}", public_access=True)
        return self._success(None, public_access=False)