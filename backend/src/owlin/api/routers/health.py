import logging

from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from owlin.api.deps import SessionDep

router = APIRouter(tags=["health"])
logger = logging.getLogger(__name__)


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/db")
async def health_db(session: SessionDep) -> dict[str, str]:
    try:
        await session.execute(text("select 1"))
    except Exception:
        # Details stay in the log; the response must not leak connection info.
        logger.exception("Database health check failed")
        raise HTTPException(status_code=503, detail="Database unavailable") from None
    return {"status": "ok", "database": "ok"}
