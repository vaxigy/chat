import json

from .client import RoomRules
from .exceptions import ValidationError


# Payload schemas for each room rule
ROOM_RULES_SCHEMAS = {
    RoomRules.CREATE: {'name': str, 'room_rule': str},
    RoomRules.RANDOM: {'name': str, 'room_rule': str},
    RoomRules.ID: {'name': str, 'room_rule': str, 'room_id': str}
}


def parse_initial_data(data: str) -> dict:
    try:
        data = json.loads(data)
    except json.JSONDecodeError:
        raise ValidationError('Malformed JSON payload') from None
    
    if not isinstance(data, dict):
        raise ValidationError('Not a JSON object')
    
    if 'room_rule' not in data:
        raise ValidationError("'room_rule' key missing")
    
    if data['room_rule'] not in RoomRules:
        raise ValidationError("Invalid value for 'room_rule' key")
    
    schema = ROOM_RULES_SCHEMAS[data['room_rule']]
    
    for key, type in schema.items():
        if key not in data:
            raise ValidationError(f"'{key}' key missing")
        
        if not isinstance(data[key], type):
            raise ValidationError(
                f"Expected '{type.__name__}' type for '{key}' key, "
                f"got '{data[key].__class__.__name__}'"
            )
    
    return data
