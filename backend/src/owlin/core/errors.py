class AppError(Exception):
    """An expected failure that is reported to the client as a JSON `detail` message."""

    status_code = 400

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class InvalidRequestError(AppError):
    status_code = 422


class NotFoundError(AppError):
    status_code = 404


class ConflictError(AppError):
    status_code = 409


class UpstreamError(AppError):
    """A service we depend on (Supabase Storage) failed."""

    status_code = 502
