import websockets
import asyncio
import json
import logging

from websockets.exceptions import ConnectionClosed, ConnectionClosedOK
from json.decoder import JSONDecodeError
from .exceptions import InitialValidationFailed, MessageLoopError

from .client import Client, Room, RoomManager, RoomRules
from .events import Events, create_json_payload
from .config import LOGGER_CONFIG

logging.basicConfig(**LOGGER_CONFIG)
logging.getLogger('websockets').setLevel(logging.ERROR)


def format_addr(addr: tuple[str, int]) -> str:
    return '{}:{}'.format(*addr)


class ChatRunner:
    """
    Websocket-based chat server.
    """
    def __init__(
        self,
        host: str,
        port: int
    ) -> None:
        """
        Construct a chat server instance.
        
        Args:
            host (str): Server IP address.
            port (int): Port number to listen on.
        """
        self._host: str = host
        self._port: int = port
        
        self._rooms: RoomManager[Room[Client]] = RoomManager()
    
    async def _handle_initial(
        self,
        conn: websockets.ServerConnection
    ) -> dict:
        """
        Handler responsible for processing and
        validating the initial connection stage.
        
        Returns:
            Dictionary containing initial data.
        
        Raises:
            InitialValidationFailed: If something went wrong.
        """
        try:
            message = await conn.recv()
            
            client_data = json.loads(message)
            if not isinstance(client_data, dict):
                raise ValueError('JSON payload is not a JSON object')
            
            required_keys = ['name', 'room_rule']
            for key in required_keys:
                if key not in client_data:
                    raise ValueError(f"'{key}' key missing")
            
            for key, value in client_data.items():
                if not isinstance(value, str):
                    raise ValueError(f"Non-string type for '{key}'")
            
            if client_data['room_rule'] not in RoomRules:
                raise ValueError("Invalid value for 'room_rule' key")
            
            return client_data
        
        except ConnectionClosed as e:
            raise InitialValidationFailed('Connection closed') from e
        
        except JSONDecodeError as e:
            await conn.close(1008, 'Malformed JSON payload')
            raise InitialValidationFailed('Malformed JSON payload') from e
        
        except ValueError as e:
            await conn.close(1008, str(e))
            raise InitialValidationFailed(str(e)) from None
    
    async def _handle_message_loop(
        self,
        client: Client,
        room: Room
    ) -> None:
        """
        Handler responsible for the client message loop.
        """
        try:
            async for message in client.conn:
                logging.info(
                    f"Received '{message}' from {client} in room {room.id}; Broadcasting"
                )
                message_event_json = create_json_payload(
                    Events.MESSAGE,
                    sender_name=client.name,
                    message=message
                )
                room.broadcast(message_event_json)
        except ConnectionClosedOK:
            logging.info(f'Connection for {client} in {room.id} closed gracefully')
        except Exception as e:
            raise MessageLoopError(e, str(e) or None) from e
    
    async def _handle_client_connection(
        self,
        conn: websockets.ServerConnection
    ) -> None:
        """
        Central client connection handler.
        """
        addr = format_addr(conn.remote_address)
        logging.info(f'Connection attempt from {addr}')
        
        try:
            client_data = await self._handle_initial(conn)
        except InitialValidationFailed as e:
            logging.info(
                f'Connection for {addr} failed during initial validation; '
                f'Reason: {e}'
            )
            return
        
        client = Client(
            conn=conn,
            name=client_data['name']
        )
        room = self._rooms.allocate_room(client_data['room_rule'])
        if room.has_name(client.name):
            logging.info(
                f'Rejecting further processing for {client}; '
                f'Provided name in room {room.id} is occupied'
            )
            await conn.close(1008, 'Name occupied')
            return
        room.add(client)
        logging.info(f'Connection from {client} in room {room.id}')
        
        try:
            join_event_json = create_json_payload(
                Events.JOIN,
                sender_name=client.name,
                online_count=len(room)
            )
            room.broadcast(join_event_json)
            
            await self._handle_message_loop(client, room)
        except MessageLoopError as e:
            logging.error(
                f'Exception in message loop for {client}, room id: {room.id}:\n'
                f'  {e.args[0].__class__}: {e.args[1]}; Connection closed'
            )
        finally:
            await client.destroy()
            leave_event_json = create_json_payload(
                Events.LEAVE,
                sender_name=client_data['name'],
                online_count=len(room)
            )
            room.broadcast(leave_event_json)
    
    async def _main(self) -> None:
        """
        Private main entrypoint.
        """
        async with websockets.serve(
            self._handle_client_connection,
            self._host,
            self._port
        ) as server:
            logging.info(f'Server listening on {self._host}:{self._port}')
            await server.serve_forever()
    
    def run(self) -> None:
        """
        Public main entrypoint.
        """
        try:
            asyncio.run(self._main())
        except (KeyboardInterrupt, SystemExit):
            logging.info('Server shut down successfully')
