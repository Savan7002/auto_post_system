import asyncio

import httpx

from app.config import Settings
from app.platforms.base import BasePlatform
from app.platforms.bluesky import BlueskyPlatform
from app.platforms.devto import DevToPlatform
from app.platforms.discord import DiscordPlatform
from app.platforms.github_gist import GitHubGistPlatform
from app.platforms.mastodon import MastodonPlatform
from app.platforms.telegram import TelegramPlatform
from app.schemas import PlatformResult, PostResponse

# To add a platform, write its class and list it here. Nothing else needs to change.
PLATFORM_CLASSES: list[type[BasePlatform]] = [
    TelegramPlatform,
    MastodonPlatform,
    BlueskyPlatform,
    GitHubGistPlatform,
    DevToPlatform,
    DiscordPlatform,
]


async def post_to_all_platforms(message: str, settings: Settings) -> PostResponse:
    """Post to every platform at once and collect one result per platform."""
    async with httpx.AsyncClient(
            timeout=settings.request_timeout_seconds,
            headers={"User-Agent": "MultiPlatformPostingAPI/1.0"},
    ) as client:
        platforms = [platform_class(settings, client) for platform_class in PLATFORM_CLASSES]

        # Run all platforms concurrently, so the total time is the slowest one, not the sum.
        # post() shouldn't raise, but return_exceptions=True keeps one surprise from cancelling the rest.
        outcomes = await asyncio.gather(
            *(platform.post(message) for platform in platforms),
            return_exceptions=True,
        )

    # gather keeps the input order, so zip pairs each outcome with its platform.
    results: list[PlatformResult] = []
    for platform, outcome in zip(platforms, outcomes):
        if isinstance(outcome, BaseException):
            results.append(platform._failed(f"Unhandled error: {outcome!r}"))
        else:
            results.append(outcome)

    succeeded = sum(1 for result in results if result.status == "success")
    return PostResponse(
        message=message,
        total_platforms=len(results),
        succeeded=succeeded,
        failed=len(results) - succeeded,
        results=results,
    )