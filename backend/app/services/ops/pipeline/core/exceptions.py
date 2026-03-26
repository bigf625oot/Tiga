from typing import Optional, Dict, Any

# Try to import from app.core.exceptions, fallback to Exception if not found
try:
    from app.core.exceptions import AppException
except ImportError:
    class AppException(Exception):
        """Base exception for the application"""
        def __init__(self, message: str, status_code: int = 500, detail: Optional[str] = None):
            self.message = message
            self.status_code = status_code
            self.detail = detail
            super().__init__(message)

class PathwayException(AppException):
    """Base exception for Pathway service"""
    def __init__(
        self, 
        message: str, 
        status_code: int = 500, 
        detail: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, status_code=status_code, detail=detail)
        self.context = context or {}

class ConfigurationError(PathwayException):
    """Raised when configuration is invalid"""
    def __init__(self, message: str, detail: Optional[str] = None):
        super().__init__(message, status_code=400, detail=detail)

class ConnectorError(PathwayException):
    """Raised when connector fails"""
    def __init__(self, message: str, detail: Optional[str] = None):
        super().__init__(message, status_code=502, detail=detail)

class OperatorError(PathwayException):
    """Raised when operator fails"""
    def __init__(self, message: str, detail: Optional[str] = None):
        super().__init__(message, status_code=422, detail=detail)
