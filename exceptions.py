class TelegramBotError(Exception):
    def __init__(self, error_message: str) -> None:
        self.error_message = error_message


class APICallError(TelegramBotError):
    """Raised when an API call fails."""


class MissingDataInResponse(TelegramBotError):
    """Raised when data is missing and response is valid."""


class ParseStatusError(TelegramBotError):
    """Raised when there is an error parsing the status of a homework."""
