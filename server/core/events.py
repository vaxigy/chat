import enum
import json
from datetime import datetime
from typing import Self, Callable, TypeVar, Any


class Events(enum.StrEnum):
    """
    Server events.
    """
    JOIN = 'JOIN'
    MESSAGE = 'MESSAGE'
    LEAVE = 'LEAVE'


class BuilderKeys(enum.StrEnum):
    """
    Keys used across the payload builders.
    """
    SENDER_NAME = 'sender_name'
    ONLINE_COUNT = 'online_count'
    MESSAGE = 'message'


PayloadBuilderT = TypeVar('PayloadBuilderT', bound='JSONPayloadBuilder')

# Maps the event types to the payload builders
BUILDER_REGISTRY: dict[Events, type[PayloadBuilderT]] = {}


def update_builder_registry(
    *event_types: Events
) -> Callable[[type[PayloadBuilderT]], type[PayloadBuilderT]]:
    """
    Register a concrete builder for one or more event types in the builder registry.
    """
    def update(cls: type[PayloadBuilderT]) -> type[PayloadBuilderT]:
        for event_type in event_types:
            BUILDER_REGISTRY[event_type] = cls
        return cls
    return update


class JSONPayloadBuilder:
    """
    Base class for JSON payload builders.
    
    This class provides basic building methods, validation,
    and payload construction.
    
    Subclasses must define `_required_data_keys` and `_assembly_steps`.
    """
    # Implement in subclass
    _required_data_keys: list[BuilderKeys]
    _assembly_steps: list[str]
    
    def __init__(self, event_type: str, data: dict[str, Any]) -> None:
        """
        Initialize a new JSON payload builder.
        """
        self._validate_keys(data)
        
        self._event_type: str = event_type
        self._data: dict[str, Any] = data
        self._payload: dict = {}
    
    def _validate_keys(self, data: dict) -> None:
        """
        Ensure all keys are present in `data`.
        """
        missing = [
            key.value
            for key in self._required_data_keys
            if key not in data
        ]
        if missing:
            raise ValueError(
                f"Missing required keys: {missing}"
            )
    
    # Building methods (subclasses provide more specific methods)
    
    def add_event_type(self) -> Self:
        self._payload['event'] = self._event_type
        return self
    
    def add_timestamp(self) -> Self:
        self._payload['timestamp'] = datetime.now().strftime('%H:%M:%S')
        return self
    
    def add_sender(self) -> Self:
        self._payload['sender'] = {
            'name': self._data[BuilderKeys.SENDER_NAME]
        }
        return self
    
    # Final assemblers
    
    def assemble_payload(self) -> str:
        """
        Build the payload by executing all steps in `_assembly_steps`.
        """
        for step in self._assembly_steps:
            getattr(self, step)()
        return self.build_json()
    
    def build_json(self) -> str:
        """
        Serialize the constructed payload into a JSON string.
        """
        return json.dumps(self._payload)


@update_builder_registry(Events.JOIN, Events.LEAVE)
class MembershipChangeBuilder(JSONPayloadBuilder):
    """
    Concrete builder for membership change payload.
    """
    _required_data_keys = [BuilderKeys.SENDER_NAME, BuilderKeys.ONLINE_COUNT]
    _assembly_steps = [
        'add_event_type',
        'add_timestamp',
        'add_sender',
        'add_room_status'
    ]
    
    def add_room_status(self) -> Self:
        self._payload['room_status'] = {
            'online': self._data[BuilderKeys.ONLINE_COUNT]
        }
        return self


@update_builder_registry(Events.MESSAGE)
class MessageBuilder(JSONPayloadBuilder):
    """
    Concrete builder for message payload.
    """
    _required_data_keys = [BuilderKeys.SENDER_NAME, BuilderKeys.MESSAGE]
    _assembly_steps = [
        'add_event_type',
        'add_timestamp',
        'add_sender',
        'add_message'
    ]
    
    def add_message(self) -> Self:
        self._payload['message'] = self._data[BuilderKeys.MESSAGE]
        return self


def create_json_payload(event_type: Events, **data) -> str:
    """
    Create a JSON payload based on `event_type`.
    """
    builder_cls = BUILDER_REGISTRY.get(event_type, None)
    if builder_cls is None:
        raise ValueError(
            f'{event_type} is not a recognized event identifier'
        )
    builder = builder_cls(event_type, data)
    return builder.assemble_payload()
