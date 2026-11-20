from abc import ABC, abstractmethod
from datetime import datetime, timezone

import httpx

from app.config import Settings
from app.schemas import PlatformResult


class BasePlatform(ABC):

    name: str = "Base"

    def __init__(self, settings: Settings, client: httpx.AsyncClient) -> None:

        self.settings = settings
        self.client = client

    @abstractmethod
    def is_configured(self) -> bool:
        ...

    @abstractmethod
    async def publish(self, message: str) -> PlatformResult:
        ...

    async def post(self, message: str) -> PlatformResult:
        if not self.is_configured():
            return self._failed("Not configured: add this platform's keys to .env")

        try:
            return await self.publish(message)

        except httpx.HTTPStatusError as exc:
            return self._failed(f"HTTP {exc.response.status_code}: {exc.response.text[:300]}")

        except httpx.TimeoutException:
            return self._failed(f"Timed out after {self.settings.request_timeout_seconds}s")

        except httpx.RequestError as exc:
            return self._failed(f"Network error: {exc}")

        except Exception as exc:
            return self._failed(f"Unexpected error: {exc}")

    def _success(self, posted_url: str | None, public_access: bool) -> PlatformResult:
        return PlatformResult(
            platform=self.name,
            status="success",
            posted_url=posted_url,
            public_access=public_access,
            posted_at=datetime.now(timezone.utc),
        )

    def _failed(self, error: str) -> PlatformResult:
        return PlatformResult(platform=self.name, status="failed", error=error)