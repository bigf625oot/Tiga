import enum


class DispatchErrorType(enum.Enum):
    WS_TIMEOUT = "WS_TIMEOUT"
    WS_NOT_CONNECTED = "WS_NOT_CONNECTED"
    HTTP_TIMEOUT = "HTTP_TIMEOUT"
    HTTP_4XX = "HTTP_4XX"
    HTTP_5XX = "HTTP_5XX"
    NODE_OFFLINE = "NODE_OFFLINE"
    ROUTING_MISSING = "ROUTING_MISSING"
    ROUTING_INVALID = "ROUTING_INVALID"
    ROUTING_FORBIDDEN = "ROUTING_FORBIDDEN"
    UNKNOWN = "UNKNOWN"


class DispatchException(Exception):
    def __init__(
        self,
        error_type: DispatchErrorType,
        message: str,
        *,
        http_status: int = 500,
        error_code: str = "OPENCLAW_DISPATCH_ERROR",
    ):
        self.error_type = error_type
        self.message = message
        self.http_status = http_status
        self.error_code = error_code
        super().__init__(message)


class DispatchPhase(enum.Enum):
    NODE_CHECK = "NODE_CHECK"
    WS_SEND = "WS_SEND"
    WS_ACK = "WS_ACK"
    HTTP_SEND = "HTTP_SEND"
    HTTP_RESP = "HTTP_RESP"


class TaskParsingError(Exception):
    def __init__(
        self,
        raw_response: str,
        validation_error: str,
        retry_count: int = 0,
    ):
        self.raw_response = raw_response
        self.validation_error = validation_error
        self.retry_count = retry_count
        super().__init__(
            f"Task parsing failed after {retry_count} retries. "
            f"Error: {validation_error}"
        )
