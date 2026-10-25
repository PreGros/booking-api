class AppError(Exception):
    status_code = 500
    detail = "Internal error"


class NotFoundError(AppError):
    status_code = 404


class ConflictError(AppError):
    status_code = 409


class ResourceNotFound(NotFoundError):
    detail = "Resource not found"


class BookingNotFound(NotFoundError):
    detail = "Booking not found"


class ResourceAlreadyExists(ConflictError):
    detail = "A resource with this name already exists"


class BookingConflict(ConflictError):
    detail = "Resource is already booked for that time range"
