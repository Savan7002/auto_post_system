import logging

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.config import Settings, get_settings
from app.schemas import PostRequest, PostResponse
from app.services.posting_service import PLATFORM_CLASSES, post_to_all_platforms

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
# Telegram and Discord put secrets in the request URL, so keep httpx request logs out of INFO.
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger("posting_api")

app = FastAPI(
    title="Multi-Platform Posting API",
    description="Publishes one short message with a CTA link to several platforms at once.",
    version="1.0.0",
)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Replace FastAPI's verbose 422 body with a short field/message list."""
    errors = []
    for error in exc.errors():
        field = ".".join(str(part) for part in error["loc"] if part != "body") or "body"
        message = error["msg"].removeprefix("Value error, ")
        errors.append({"field": field, "message": message})

    logger.info("Rejected request: %s", errors)
    return JSONResponse(status_code=422, content={"detail": "Validation failed", "errors": errors})


@app.post("/posting", response_model=PostResponse, summary="Post a message to all platforms")
async def create_posting(
        payload: PostRequest,
        settings: Settings = Depends(get_settings),
) -> PostResponse:
    """Post the message everywhere.

    Returns 200 even if some platforms fail: the request itself worked, and each
    platform's status is in the results.
    """
    logger.info("Posting to %d platforms: %r", len(PLATFORM_CLASSES), payload.message)

    response = await post_to_all_platforms(payload.message, settings)

    for result in response.results:
        logger.info("  %-12s %-7s %s", result.platform, result.status, result.posted_url or result.error)
    return response


@app.get("/health", summary="Health check")
async def health(settings: Settings = Depends(get_settings)) -> dict:
    """Show which platforms have keys set. Handy to check before a demo."""
    # No HTTP client needed: is_configured() only looks at settings.
    configured = {cls.name: cls(settings, None).is_configured() for cls in PLATFORM_CLASSES}
    return {"status": "ok", "platforms": configured}