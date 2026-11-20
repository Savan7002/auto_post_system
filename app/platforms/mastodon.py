from app.platforms.base import BasePlatform
from app.schemas import PlatformResult


class MastodonPlatform(BasePlatform):
    """Publish a public status on Mastodon."""

    name = "Mastodon"

    def is_configured(self) -> bool:
        return bool(self.settings.mastodon_access_token)

    async def publish(self, message: str) -> PlatformResult:
        # Mastodon is federated, so the account's server comes from settings.
        base_url = self.settings.mastodon_base_url.rstrip("/")

        response = await self.client.post(
            f"{base_url}/api/v1/statuses",
            headers={"Authorization": f"Bearer {self.settings.mastodon_access_token}"},
            json={
                "status": message,
                "visibility": "public",
            },
        )
        response.raise_for_status()

        data = response.json()
        return self._success(
            posted_url=data.get("url"),
            public_access=data.get("visibility") == "public",
        )
