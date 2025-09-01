import json
from dataclasses import dataclass

from core.domain.room import RoomRules

from ..exceptions import (
    MalformedPayloadError,
    TypeMismatchError,
    MissingKeyError,
    UnexpectedValueError
)


@dataclass
class RoomEntryRequest:
    """
    Representation for the room entry request.
    """
    name: str
    room_rule: str
    room_id: str | None = None
    
    def __post_init__(self):
        if self.room_rule == RoomRules.ID and self.room_id is None:
            raise ValueError(
                "'room_id' field is required for ID rule"
            )


BASE_SCHEMAS = {
    'ROOM_ENTRY': {'name': str, 'room_rule': str}
}


ROOM_ENTRY_SCHEMAS = {
    RoomRules.CREATE: {**BASE_SCHEMAS['ROOM_ENTRY']},
    RoomRules.RANDOM: {**BASE_SCHEMAS['ROOM_ENTRY']},
    RoomRules.ID: {**BASE_SCHEMAS['ROOM_ENTRY'], 'room_id': str}
}


def _format_path(path: list[str]) -> str:
    return '.'.join(path) or 'ROOT'


def _validate_against_schema(data: dict, schema: dict, path=None) -> None:
    if path is None:
        path = []
    
    if not isinstance(data, dict):
        raise TypeMismatchError(
            path, dict,
            f"Expected JSON object at '{_format_path(path)}' path"
        )
    
    for key, expected in schema.items():
        current_path = path + [key]
        
        if key not in data:
            raise MissingKeyError(
                path, key,
                f"'{key}' key missing at '{_format_path(path)}' path"
            )
        
        if isinstance(expected, dict):
            _validate_against_schema(data[key], expected, current_path)
        elif not isinstance(data[key], expected):
            raise TypeMismatchError(
                current_path, expected,
                f"Exptected '{expected.__name__}' type for '{key}' key "
                f"at '{_format_path(path)}' path, got '{data[key].__class__.__name__}'"
            )


def parse_room_entry_payload(payload: str) -> RoomEntryRequest:
    """
    Accept a raw room entry payload, validate it,
    and, on success, transform it to `RoomEntryRequest`.
    
    Raises:
        ValidationError: If validation fails.
    """
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        raise MalformedPayloadError('Malformed JSON payload') from None
    
    if not isinstance(data, dict):
        raise TypeMismatchError('ROOT', dict, 'Not a JSON object')
    
    base_schema = BASE_SCHEMAS['ROOM_ENTRY']
    _validate_against_schema(data, base_schema)
    
    if data['room_rule'] not in ROOM_ENTRY_SCHEMAS:
        raise UnexpectedValueError('Invalid room rule.')
    
    schema = ROOM_ENTRY_SCHEMAS[data['room_rule']]
    _validate_against_schema(data, schema)
    
    return RoomEntryRequest(**data)
