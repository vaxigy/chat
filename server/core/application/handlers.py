import logging
from dataclasses import dataclass

from core.domain.client import Client
from core.domain.room import Room, RoomManager, RoomRules
from core.domain.ports import ClientConnection
from core.domain.exceptions import (
    ClientDisconnected,
    RoomAllocationError,
    NoRoomWithID,
    RoomJoinError,
    NameInRoomOccupied,
)

from .io.incoming import RoomEntryRequest, parse_room_entry_payload
from .io.outgoing import create_json_payload
from .events import Events

from .exceptions import HandlerException, ValidationError


@dataclass
class HandlerContext:
    rooms: RoomManager
    logger: logging.Logger


async def receive_room_entry_request(
    conn: ClientConnection
) -> RoomEntryRequest:
    """
    Receive room entry request, validate it,
    and, on success, return `RoomEntryRequest` representation.
    
    Raises:
        HandlerException (with ClientDisconnected):
            If connection abruptly interrupts.
        HandlerException (with ValidationError):
            If initial data validation fails.
    """
    try:
        message = await conn.recv()
        return parse_room_entry_payload(message)
    
    except ClientDisconnected as e:
        raise HandlerException(e, 'Client disconnected') from e
    
    except ValidationError as e:
        raise HandlerException(e, 'Validation failed') from e
    
    except Exception as e:
        raise HandlerException(
            e, 'Unexpected exception (receive_room_entry_request handler)'
        ) from e


async def process_room_entry(
    ctx: HandlerContext,
    conn: ClientConnection,
    entry_request: RoomEntryRequest
) -> tuple[Client, Room]:
    """
    Attempt room entry for the given `conn`.
    
    Raises:
        HandlerException (with RoomAllocactionError):
            If cannot allocate a room.
        HandlerException (with RoomJoinError):
            If room entry fails.
    """
    try:
        if entry_request.room_rule == RoomRules.ID:
            room = ctx.rooms.allocate_room(
                RoomRules.ID,
                id=entry_request.room_id
            )
        else:
            room = ctx.rooms.allocate_room(entry_request.room_rule)
        
        client = Client(conn, entry_request.name)
        room.add(client)
        info_event_json = create_json_payload(
            Events.ROOM_INFO,
            room_id=room.id
        )
        await client.conn.send(info_event_json)
        
        return client, room
    
    except RoomAllocationError as e:
        raise HandlerException(e, 'Room allocation failed') from e
    
    except RoomJoinError as e:
        raise HandlerException(e, 'Room entry failed') from e
    
    except Exception as e:
        raise HandlerException(
            e, 'Unexpected exception (process_room_entry handler)'
        ) from e


async def handle_messaging(
    ctx: HandlerContext,
    client: Client,
    room: Room
) -> None:
    """
    Handle messaging for `client` in `room`.
    
    Raises:
        HandlerException (with ClientDisconnected):
            If the connection with the client is lost.
    """
    try:
        ctx.logger.info(f'Connection from {client} in room {room.id}')
        join_event_json = create_json_payload(
            Events.ROOM_JOIN,
            sender_name=client.name,
            online_count=len(room)
        )
        room.broadcast(join_event_json)
        
        async for message in client.conn:
            ctx.logger.info(
                f"Received '{message}' from {client} in room {room.id}; Broadcasting"
            )
            message_event_json = create_json_payload(
                Events.ROOM_MESSAGE,
                sender_name=client.name,
                message=message
            )
            room.broadcast(message_event_json)
    
    except ClientDisconnected as e:
        raise HandlerException(e, 'Client disconnected') from e
    
    except Exception as e:
        raise HandlerException(
            e, 'Unexpected exception (handle_messaging handler)'
        ) from e
    
    finally:
        leave_event_json = create_json_payload(
            Events.ROOM_LEAVE,
            sender_name=client.name,
            online_count=len(room) - 1
        )
        room.broadcast(leave_event_json)


async def report_error(
    conn: ClientConnection,
    error: HandlerException
) -> None:
    """
    Report `error` to `conn` if possible.
    """
    try:
        cause = error.origin_exc

        if isinstance(cause, ClientDisconnected):
            return
        elif isinstance(cause, ValidationError):
            message = 'JSON payload is invalid'
        elif isinstance(cause, NoRoomWithID):
            message = 'No room with ID found'
        elif isinstance(cause, NameInRoomOccupied):
            message = 'Name is occupied'
        else:
            message = 'Unknown error'
        
        error_event_json = create_json_payload(Events.ERROR, message=message)
        await conn.send(error_event_json)
    
    except Exception as e:
        raise HandlerException(
            e, 'Unexpected exception (report_error handler)'
        ) from e
