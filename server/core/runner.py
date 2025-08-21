import websockets
import asyncio
import logging

from .client import Client, Room, RoomManager
from .handlers import (
    HandlerContext,
    handle_initial_stage,
    handle_entry,
    handle_messaging
)
from .exceptions import ValidationError, HandlerError
from .utils import format_addr

logging.getLogger('websockets').setLevel(logging.ERROR)


class ChatRunner:
    """
    Websocket-based chat server.
    """
    def __init__(
        self,
        host: str,
        port: int,
        logger: logging.Logger
    ) -> None:
        """
        Construct a chat server instance.
        
        Args:
            host (str): Server IP address.
            port (int): Port number to listen on.
        """
        self._host: str = host
        self._port: int = port
        
        self._logger: logging.Logger = logger
        self._rooms: RoomManager[Room[Client]] = RoomManager()
        
        self._ctx: HandlerContext = HandlerContext(
            rooms=self._rooms,
            logger=self._logger
        )
    
    async def _handle_client_connection(
        self,
        conn: websockets.ServerConnection
    ) -> None:
        """
        Central client connection handler.
        """
        addr = format_addr(conn.remote_address)
        self._logger.info(f'Connection attempt from {addr}')
        
        try:
            client_data = await handle_initial_stage(conn)
        except (HandlerError, ValidationError) as e:
            if e.__class__ == ValidationError:
                await conn.close(1008, str(e))
            self._logger.info(
                f'Connection for {addr} failed during initial validation; '
                f'Reason: {e}; Connection closed'
            )
            return
        
        try:
            client, room = await handle_entry(self._ctx, conn, client_data)
        except HandlerError as e:
            await conn.close(1008, str(e))
            self._logger.info(
                f'Rejecting further processing for {addr}; Reason: {str(e)}'
            )
            return
        
        try:
            await handle_messaging(self._ctx, client, room)
        except HandlerError as e:
            self._logger.error(
                f'Exception in messaging handler for {client}, room id: {room.id}:\n'
                f'  {e.args[0].__class__}: {e.args[0]}; Connection closed'
            )
        finally:
            await client.destroy()
    
    async def _main(self) -> None:
        """
        Private main entrypoint.
        """
        async with websockets.serve(
            self._handle_client_connection,
            self._host,
            self._port
        ) as server:
            self._logger.info(f'Server listening on {self._host}:{self._port}')
            await server.serve_forever()
    
    def run(self) -> None:
        """
        Public main entrypoint.
        """
        try:
            asyncio.run(self._main())
        except (KeyboardInterrupt, SystemExit):
            self._logger.info('Server shut down successfully')
