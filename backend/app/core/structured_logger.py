import logging
import time
import uuid
import traceback
import contextlib
from typing import Optional, Any, Dict

class StructuredLogger:
    def __init__(self, logger: logging.Logger, defaults: Dict[str, Any] = None):
        self.logger = logger
        self.defaults = defaults or {}

    def _format_extra(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Merge defaults with provided kwargs"""
        extra = self.defaults.copy()
        extra.update(kwargs)
        return extra

    def debug(self, msg: str, **kwargs):
        self.logger.debug(msg, extra=self._format_extra(kwargs))

    def info(self, msg: str, **kwargs):
        self.logger.info(msg, extra=self._format_extra(kwargs))

    def warning(self, msg: str, **kwargs):
        self.logger.warning(msg, extra=self._format_extra(kwargs))

    def error(self, msg: str, **kwargs):
        self.logger.error(msg, extra=self._format_extra(kwargs))

    @contextlib.contextmanager
    def context(self, stage: str, **kwargs):
        """
        Context manager for logging a stage of execution.
        Logs entry and exit, duration, and any exceptions.
        """
        start_time = time.time()
        ctx_kwargs = self._format_extra(kwargs)
        ctx_kwargs['stage'] = stage
        
        # Log entry (optional, maybe debug level)
        self.logger.debug(f"Starting stage: {stage}", extra=ctx_kwargs)
        
        try:
            yield
            # Log success
            duration = (time.time() - start_time) * 1000
            ctx_kwargs['duration_ms'] = round(duration, 2)
            self.logger.info(f"Completed stage: {stage}", extra=ctx_kwargs)
        except Exception as e:
            # Log failure
            duration = (time.time() - start_time) * 1000
            ctx_kwargs['duration_ms'] = round(duration, 2)
            ctx_kwargs['error_stack'] = traceback.format_exc()
            ctx_kwargs['error'] = str(e)
            self.logger.error(f"Failed stage: {stage}", extra=ctx_kwargs)
            raise

def get_structured_logger(name: str, **defaults) -> StructuredLogger:
    return StructuredLogger(logging.getLogger(name), defaults)
