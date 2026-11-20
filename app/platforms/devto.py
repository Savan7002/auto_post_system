from app.platforms.base import BasePlatform
from app.schemas import PlatformResult, extract_links

TITLE_MAX_LENGTH = 60


class DevToPlatform(BasePlatform):
    """Publish the message as a short dev.to article."""

    name = "Dev.to"

    def is_configured(self) -> bool:
        return bool(self.settings.devto_api_key)

    @staticmethod
    def _make_title(message: str) -> str:
        """dev.to requires a title, so build one from the message text minus the link."""
        text = message
        for link in extract_links(message):
            text = text.replace(link, "")
        text = " ".join(text.split())
        if len(text) > TITLE_MAX_LENGTH:
            text = text[: TITLE_MAX_LENGTH - 3].rstrip() + "..."
        return text or "Update"

    async def publish(self, message: str) -> PlatformResult:
        response = await self.client.post(
            "https://dev.to/api/articles",
            headers={"api-key": self.settings.devto_api_key},
            json={
                "article": {
                    "title": self._make_title(message),
                    "body_markdown": message,
                    "published": True,
                }
            },
        )
        response.raise_for_status()

        data = response.json()
        return self._success(posted_url=data.get("url"), public_access=True)