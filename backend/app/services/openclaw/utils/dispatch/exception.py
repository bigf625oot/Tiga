import enum

class DispatchErrorType(enum.Enum):
    WS_TIMEOUT = "WS_TIMEOUT"
    WS_NOT_CONNECTED = "WS_NOT_CONNECTED"
    HTTP_TIMEOUT = "HTTP_TIMEOUT"
    HTTP_4XX = "HTTP_4XX"
    HTTP_5XX = "HTTP_5XX"
    NODE_OFFLINE = "NODE_OFFLINE"
    UNKNOWN = "UNKNOWN"

class DispatchException(Exception):
    def __init__(self, error_type: DispatchErrorType, message: str):
        self.error_type = error_type
        self.message = message
        super().__init__(message)

class DispatchPhase(enum.Enum):
    NODE_CHECK = "NODE_CHECK"
    WS_SEND = "WS_SEND"
    WS_ACK = "WS_ACK"
    HTTP_SEND = "HTTP_SEND"
    HTTP_RESP = "HTTP_RESP"
