"""Post a test message to a single platform, for debugging its keys and API calls."""

import asyncio
import sys

from pathlib import Path

# Running "python scripts/test_platform.py" puts scripts/ on the import path, not the
# project root, so "import app" would fail. Add the project root BEFORE importing app.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx

from app.config import get_settings
from app.platforms.telegram import TelegramPlatform
from app.platforms.mastodon import MastodonPlatform
from app.platforms.bluesky import BlueskyPlatform
from app.platforms.github_gist import GitHubGistPlatform
from app.platforms.devto import DevToPlatform
from app.platforms.discord import DiscordPlatform



PLATFORMS = {
    "telegram": TelegramPlatform,
    "mastodon": MastodonPlatform,
    "bluesky": BlueskyPlatform,
    "gist": GitHubGistPlatform,
    "devto": DevToPlatform,
    "discord": DiscordPlatform,
}


async def main(name: str) -> None:
    platform_class = PLATFORMS[name]
    async with httpx.AsyncClient(timeout=15) as client:
        result = await platform_class(get_settings(), client).post(
            "Testing my posting API https://example.com"
        )
        print(result)


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in PLATFORMS:
        print(f"Usage: python test_platform.py <{'|'.join(PLATFORMS)}>")
        sys.exit(1)
    asyncio.run(main(sys.argv[1]))