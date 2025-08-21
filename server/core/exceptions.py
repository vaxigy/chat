class ServerException(Exception):
    """
    Base class for all server exceptions.
    """


class ValidationError(ServerException):
    """
    Raised when validation fails.
    """


class HandlerError(ServerException):
    """
    Raised when an error occurs in a handler.
    """
