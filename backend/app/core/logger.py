import logging
import sys

from app.core.config import settings


def setup_logging():
    logging.basicConfig(
        level=settings.LOG_LEVEL,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    # Prevent duplicate logs from uvicorn
    logging.getLogger("uvicorn.access").handlers = []


logger = logging.getLogger("tiga")
