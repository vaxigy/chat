import enum


class Events(enum.StrEnum):
    """
    Server events.
    """
    ERROR = 'ERROR'
    ROOM_JOIN = 'ROOM_JOIN'
    ROOM_MESSAGE = 'ROOM_MESSAGE'
    ROOM_LEAVE = 'ROOM_LEAVE'
    ROOM_INFO = 'ROOM_INFO'
