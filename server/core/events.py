import enum
import json

class Events(enum.StrEnum):
    """
    Server events.
    """
    JOIN = 'JOIN'
    MESSAGE = 'MESSAGE'
    LEAVE = 'LEAVE'


def get_event_json(event_type: str, **kwargs) -> str:
    """
    Return a JSON string for the specified event type.
    
    Args:
        event_type (str): Event type identifier.
        **kwargs: Additional keyword arguments to be included in the JSON payload.
    """
    if event_type not in Events:
        raise ValueError(
            f'{event_type} is not a recognized event identifier'
        )
    
    return json.dumps({'event_type': event_type, **kwargs})
