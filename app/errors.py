class AppError(Exception):
    status_code = 500
    detail = "Internal error"

    def __init__(self, headers: dict[str, str] | None = None) -> None:
        super().__init__(self.detail)
        self.headers = headers


class AuthenticationError(AppError):
    status_code = 401

    def __init__(self, headers: dict[str, str] | None = None) -> None:
        super().__init__(headers or {"WWW-Authenticate": "Bearer"})


class ForbiddenError(AppError):
    status_code = 403


class NotFoundError(AppError):
    status_code = 404


class ConflictError(AppError):
    status_code = 409


class RateLimitError(AppError):
    status_code = 429


class EmailAlreadyRegistered(ConflictError):
    detail = "A user with this email already exists"


class InvalidCredentials(AuthenticationError):
    detail = "Incorrect email or password"


class InvalidToken(AuthenticationError):
    detail = "Invalid or expired token"


class InsufficientPermissions(ForbiddenError):
    detail = "Not enough permissions"


class ResourceNotFound(NotFoundError):
    detail = "Resource not found"


class BookingNotFound(NotFoundError):
    detail = "Booking not found"


class ResourceAlreadyExists(ConflictError):
    detail = "A resource with this name already exists"


class BookingConflict(ConflictError):
    detail = "Resource is already booked for that time range"


class RateLimitExceeded(RateLimitError):
    detail = "Too many requests"
