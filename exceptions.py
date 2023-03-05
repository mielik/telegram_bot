class TelegramException(Exception):
    def __init__(self, error_message: str) -> None:
        self.error_message = error_message


class APICallFail(TelegramException):
    """Raised when an API call fails."""


class NoResponseException(TelegramException):
    """Raised when no response is received from the API."""


class ParseStatusError(TelegramException):
    """Raised when there is an error parsing the status of a homework."""
