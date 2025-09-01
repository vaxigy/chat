class DomainException(Exception):
    """
    Base class for domain-level exceptions.
    """


class ClientDisconnected(DomainException):
    """
    Raised when interacting with a disconnected client connection.
    """


# Room exceptions


class RoomException(DomainException):
    """
    Base class for all room exceptions.
    """


class RoomJoinError(RoomException):
    """
    Base class for join exceptions.
    """


class NameInRoomOccupied(RoomJoinError):
    """
    Raised when a client's name is already in use.
    """


class InactiveClientJoinAttempt(RoomJoinError):
    """
    Raised for joins with inactive clients.
    """


# RoomManager exceptions


class RoomManagerException(DomainException):
    """
    Base class for all room manager exceptions.
    """


class RoomAllocationError(RoomManagerException):
    """
    Base class for room allocation exceptions.
    """


class NoRoomWithID(RoomAllocationError):
    """
    Raised when no room with the provided ID is found.
    """


class InvalidRoomRule(RoomAllocationError):
    """
    Raised when a passed room rule is invalid.
    """


class NoRoomsAvailable(RoomManagerException):
    """
    Raised when no rooms are available.
    """
