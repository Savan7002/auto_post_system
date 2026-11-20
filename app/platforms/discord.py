from app.platforms.base import BasePlatform
from app.schemas import PlatformResult


class DiscordPlatform(BasePlatform):

    name = "Discord"

    def is_configured(self) -> bool:
        return bool(self.settings.discord_webhook_url)

    async def publish(self, message: str) -> PlatformResult:
        webhook_url = self.settings.discord_webhook_url

        response = await self.client.post(
            webhook_url,
            params={"wait": "true"},
            json={"content": message},
        )
        response.raise_for_status()
        msg = response.json()

        info = await self.client.get(webhook_url)
        info.raise_for_status()
        guild_id = info.json().get("guild_id")

        posted_url = (
            f"https://discord.com/channels/{guild_id}/{msg['channel_id']}/{msg['id']}"
            if guild_id else None
        )
        return self._success(posted_url, public_access=False)