from app.platforms.base import BasePlatform
from app.schemas import PlatformResult


class DiscordPlatform(BasePlatform):
    """Send the message to a Discord channel via webhook."""

    name = "Discord"

    def is_configured(self) -> bool:
        return bool(self.settings.discord_webhook_url)

    async def publish(self, message: str) -> PlatformResult:
        webhook_url = self.settings.discord_webhook_url

        # Without wait=true Discord replies 204 with no body, and we need the message id.
        response = await self.client.post(
            webhook_url,
            params={"wait": "true"},
            json={"content": message},
        )
        response.raise_for_status()
        msg = response.json()

        # The message reply has no guild_id, but the webhook's own details do.
        info = await self.client.get(webhook_url)
        info.raise_for_status()
        guild_id = info.json().get("guild_id")

        posted_url = (
            f"https://discord.com/channels/{guild_id}/{msg['channel_id']}/{msg['id']}"
            if guild_id else None
        )
        # Only members of the server can open the link.
        return self._success(posted_url, public_access=False)