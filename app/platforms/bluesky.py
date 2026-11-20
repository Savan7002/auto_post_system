from datetime import datetime, timezone

from app.platforms.base import BasePlatform
from app.schemas import PlatformResult, extract_links


class BlueskyPlatform(BasePlatform):
    """Post to Bluesky over the AT Protocol, using an app password."""

    name = "Bluesky"
    service = "https://bsky.social"

    def is_configured(self) -> bool:
        return bool(self.settings.bluesky_handle and self.settings.bluesky_app_password)

    async def _login(self) -> dict:
        """Get a session; its accessJwt and did are needed to create the post."""
        response = await self.client.post(
            f"{self.service}/xrpc/com.atproto.server.createSession",
            json={
                "identifier": self.settings.bluesky_handle,
                "password": self.settings.bluesky_app_password,
            },
        )
        response.raise_for_status()
        return response.json()

    @staticmethod
    def _link_facets(message: str) -> list[dict]:
        """Mark the link as clickable. Bluesky doesn't auto-link URLs in plain text."""
        links = extract_links(message)
        if not links:
            return []
        link = links[0]
        # Facet offsets count UTF-8 bytes, not characters, so an emoji before the link counts as 4.
        byte_start = len(message[: message.index(link)].encode("utf-8"))
        byte_end = byte_start + len(link.encode("utf-8"))
        return [{
            "index": {"byteStart": byte_start, "byteEnd": byte_end},
            "features": [{"$type": "app.bsky.richtext.facet#link", "uri": link}],
        }]

    async def publish(self, message: str) -> PlatformResult:
        session = await self._login()

        response = await self.client.post(
            f"{self.service}/xrpc/com.atproto.repo.createRecord",
            headers={"Authorization": f"Bearer {session['accessJwt']}"},
            json={
                "repo": session["did"],
                "collection": "app.bsky.feed.post",
                "record": {
                    "$type": "app.bsky.feed.post",
                    "text": message,
                    "createdAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    "facets": self._link_facets(message),
                },
            },
        )
        response.raise_for_status()

        # The reply has an at://did/app.bsky.feed.post/<id> URI; its last part goes in the bsky.app link.
        post_id = response.json()["uri"].rsplit("/", 1)[-1]
        web_url = f"https://bsky.app/profile/{self.settings.bluesky_handle}/post/{post_id}"
        return self._success(web_url, public_access=True)