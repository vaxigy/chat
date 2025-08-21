import websockets
import logging
from dataclasses import dataclass

from .client import Client, Room, RoomManager
from .events import Events, create_json_payload
from .validators import parse_initial_data

from websockets.exceptions import ConnectionClosed, ConnectionClosedOK
from .exceptions import HandlerError


@dataclass
class HandlerContext:
    rooms: RoomManager
    logger: logging.Logger


async def handle_initial_stage(
    conn: websockets.ServerConnection
) -> dict:
    """
    Handler responsible for processing and
    validating the initial connection stage.
    
    Returns:
        Dictionary containing initial data.
    
    Raises:
        HandlerError: If connection closed.
        ValidationError: If validation failed.
    """
    try:
        message = await conn.recv()
    except ConnectionClosed as e:
        raise HandlerError('Connection closed') from e
    
    return parse_initial_data(message)


async def handle_entry(
    ctx: HandlerContext,
    conn: websockets.ServerConnection,
    client_data: dict
) -> tuple[Client, Room]:
    """
    Handler responsible for the client entry.
    """
    room = ctx.rooms.allocate_room(client_data['room_rule'])
    if room.has_name(client_data['name']):
        raise HandlerError(f'Provided name in room {room.id} is occupied')
    
    client = Client(conn, client_data['name'])
    room.add(client)
    return client, room


async def handle_messaging(
    ctx: HandlerContext,
    client: Client,
    room: Room
) -> None:
    """
    Handler responsible for the client message exchange.
    """
    try:
        ctx.logger.info(f'Connection from {client} in room {room.id}')
        join_event_json = create_json_payload(
            Events.JOIN,
            sender_name=client.name,
            online_count=len(room)
        )
        room.broadcast(join_event_json)
        
        async for message in client.conn:
            ctx.logger.info(
                f"Received '{message}' from {client} in room {room.id}; Broadcasting"
            )
            message_event_json = create_json_payload(
                Events.MESSAGE,
                sender_name=client.name,
                message=message
            )
            room.broadcast(message_event_json)
    except ConnectionClosedOK:
        ctx.logger.info(f'Connection for {client} in {room.id} closed gracefully')
    except Exception as e:
        raise HandlerError(e) from e
    finally:
        leave_event_json = create_json_payload(
            Events.LEAVE,
            sender_name=client.name,
            online_count=len(room) - 1
        )
        room.broadcast(leave_event_json)
