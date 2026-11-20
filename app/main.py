import logging

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.config import Settings, get_settings
from app.schemas import PostRequest, PostResponse
from app.services.posting_service import PLATFORM_CLASSES, post_to_all_platforms

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger("posting_api")

app = FastAPI(
    title="Multi-Platform Posting API",
    description="Publishes one short message with a CTA link to several platforms at once.",
    version="1.0.0",
)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
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
    logger.info("Posting to %d platforms: %r", len(PLATFORM_CLASSES), payload.message)

    response = await post_to_all_platforms(payload.message, settings)

    for result in response.results:
        logger.info("  %-12s %-7s %s", result.platform, result.status, result.posted_url or result.error)
    return response


@app.get("/health", summary="Health check")
async def health(settings: Settings = Depends(get_settings)) -> dict:
    configured = {cls.name: cls(settings, None).is_configured() for cls in PLATFORM_CLASSES}
    return {"status": "ok", "platforms": configured}