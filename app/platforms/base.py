from abc import ABC, abstractmethod
from datetime import datetime, timezone

import httpx

from app.config import Settings
from app.schemas import PlatformResult


class BasePlatform(ABC):
    """Shared base for every platform.

    Subclasses only implement publish() and can let errors propagate;
    post() turns them into a failed result.
    """

    name: str = "Base"

    def __init__(self, settings: Settings, client: httpx.AsyncClient) -> None:

        self.settings = settings
        self.client = client

    @abstractmethod
    def is_configured(self) -> bool:
        ...

    @abstractmethod
    async def publish(self, message: str) -> PlatformResult:
        """Send the message to the platform. Only the happy path; raising is fine."""

    async def post(self, message: str) -> PlatformResult:
        """Post safely. Errors come back as a failed result, so one platform can't break the others."""
        try:
            # Inside the try so a bug in a subclass's is_configured() also becomes a failed result.
            if not self.is_configured():
                return self._failed("Not configured: add this platform's keys to .env")

            return await self.publish(message)

        except httpx.HTTPStatusError as exc:
            # Pull out the API's own error text when there is one; it's clearer than raw JSON.
            try:
                body = exc.response.json()
                detail = body.get("message") or body.get("description") or body.get("error") or body
            except ValueError:
                detail = exc.response.text[:300]
            return self._failed(f"HTTP {exc.response.status_code}: {detail}")

        except httpx.TimeoutException:
            return self._failed(f"Timed out after {self.settings.request_timeout_seconds}s")

        except httpx.RequestError as exc:
            return self._failed(f"Network error: {exc}")

        # Last on purpose, so the specific httpx errors above get their clearer messages first.
        # Catches things like a KeyError when an API reply has an unexpected shape.
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