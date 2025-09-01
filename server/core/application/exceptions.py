class ApplicationException(Exception):
    """
    Base class for application-level exceptions.
    """


class HandlerException(ApplicationException):
    """
    Raised when an exception occurs in a handler.
    
    Attributes:
        origin_exc: Origin exception instance.
        origin_type: Origin exception type.
        msg: Message from a handler.
    """
    def __init__(self, origin: BaseException, msg: str = '') -> None:
        self.origin_exc = origin
        self.origin_type = origin.__class__
        self.msg = msg
    
    def __str__(self) -> str:
        return (
            'HandlerException('
            'origin={}, '
            'origin_args={}, '
            'handler_message={}'
            ')'
        ).format(
            self.origin_type.__name__,
            self.origin_exc.args, # What if no args?
            repr(self.msg)
        )


class ValidationError(ApplicationException):
    """
    Base class for input validation exceptions.
    """


class MalformedPayloadError(ValidationError):
    """
    Raised when a payload structure is malformed.
    """


class TypeMismatchError(ValidationError):
    """
    Raised when the type of a value is not what expected.
    """


class MissingKeyError(ValidationError):
    """
    Raised when a payload misses a specific key.
    """


class UnexpectedValueError(ValidationError):
    """
    Raised when a value in a payload is not what expected.
    """
