class AppError(Exception):
    """Base for intentional API errors."""

    status_code = 500
    code = "INTERNAL_ERROR"
    message = "Something went wrong."

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.message
        super().__init__(self.message)


class InvalidRequestError(AppError):
    status_code = 422
    code = "INVALID_REQUEST"
    message = "The request is not valid."


class ForecastNotFoundError(AppError):
    status_code = 404
    code = "FORECAST_NOT_FOUND"
    message = "No forecast was published before this time."


class ProviderUnavailableError(AppError):
    status_code = 503
    code = "PROVIDER_UNAVAILABLE"
    message = "The wind data provider is not responding right now."
