from app.platforms.base import BasePlatform
from app.schemas import PlatformResult


class GitHubGistPlatform(BasePlatform):

    name = "GitHub Gist"

    def is_configured(self) -> bool:
        return bool(self.settings.github_token)

    async def publish(self, message: str) -> PlatformResult:
        response = await self.client.post(
            "https://api.github.com/gists",
            headers={
                "Authorization": f"Bearer {self.settings.github_token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "MultiPlatformPostingAPI",
            },
            json={
                "description": "Posted by Multi-Platform Posting API",
                "public": True,
                "files": {"message.md": {"content": message}},
            },
        )
        response.raise_for_status()

        data = response.json()
        return self._success(
            posted_url=data["html_url"],
            public_access=bool(data.get("public")),
        )