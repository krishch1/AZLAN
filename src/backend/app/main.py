import logging

from fastapi import FastAPI
from sqlalchemy import text

from backend.app.core.config import settings
from backend.app.db.session import async_session_factory

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(
    title="AZLAN",
    version="0.1.0",
    debug=settings.DEBUG,
)


@app.get("/api/v1/health")
async def health() -> dict[str, str]:
    """Health check endpoint.

    Verifies the service is running and performs a minimal database connectivity
    check (SELECT 1). Does not expose database credentials or connection details.
    """
    response: dict[str, str] = {
        "status": "ok",
        "service": "azlan-api",
        "database": "unknown",
    }

    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
        response["database"] = "ok"
    except Exception:
        logger.debug("Database connectivity check failed", exc_info=True)
        response["database"] = "unavailable"

    return response
