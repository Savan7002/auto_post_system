import re
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, HttpUrl, TypeAdapter, field_validator, ValidationError

MAX_MESSAGE_LENGTH = 200

URL_PATTERN = re.compile(r"https?://[^\s]+")

TRAILING_PUNCTUATION = ".,!?;:)]}'\""

_url_checker = TypeAdapter(HttpUrl)


def extract_links(text: str) -> list[str]:
    """Find http(s) links in the text.

    Trailing punctuation is dropped so "see https://x.com." doesn't pick up the period.
    """
    return [link.rstrip(TRAILING_PUNCTUATION) for link in URL_PATTERN.findall(text)]


class PostRequest(BaseModel):
    """Request body. There's no platforms field on purpose: the server decides where to post."""

    message: str = Field(
        ...,
        min_length=1,
        max_length=MAX_MESSAGE_LENGTH,
        description="Text to post, max 200 characters, with exactly one CTA URL.",
        examples=["Learn Python in 30 days! https://www.python.org/"],
    )

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        """Require exactly one link, and make sure it's a valid URL with a real domain."""

        value = value.strip()
        if not value:
            raise ValueError("Message cannot be empty or only spaces.")

        links = extract_links(value)

        if len(links) == 0:
            raise ValueError("Message must contain exactly one CTA link (http:// or https://). No link was found.")
        if len(links) > 1:
            raise ValueError(f"Message must contain exactly one CTA link, but {len(links)} were found: {', '.join(links)}")

        try:
            _url_checker.validate_python(links[0])
        except ValidationError:
            raise ValueError(f"The CTA link is not a valid URL: {links[0]}")

        # HttpUrl accepts hosts like "http://localhost", which isn't a usable CTA.
        host = links[0].split("://", 1)[1].split("/", 1)[0]
        if "." not in host:
            raise ValueError(f"The CTA link is not a valid domain: {links[0]}")

        return value


class PlatformResult(BaseModel):
    platform: str
    status: Literal["success", "failed"]
    posted_url: str | None = None
    public_access: bool = False
    posted_at: datetime | None = None
    error: str | None = None


class PostResponse(BaseModel):
    message: str
    total_platforms: int
    succeeded: int
    failed: int
    results: list[PlatformResult]
