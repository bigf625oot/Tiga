from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from app.core.logger import logger


async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"message": "Internal Server Error", "detail": str(exc)},
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    # Log warning for 4xx errors if needed, or just return response
    if exc.status_code >= 500:
        logger.error(f"HTTP Exception: {exc.detail}", exc_info=True)
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail},
    )
