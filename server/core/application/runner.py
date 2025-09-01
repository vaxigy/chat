import asyncio
import logging

from core.domain.client import Client
from core.domain.room import Room, RoomManager

from core.infrastructure.adapters.websocket import (
    WebSocketServer,
    WebSocketConnection,
    WebSocketBroadcaster
)
from core.infrastructure.adapters.word_id import WordIDGenerator

from .handlers import (
    HandlerContext,
    receive_room_entry_request,
    process_room_entry,
    handle_messaging,
    report_error
)
from .utils import format_addr
from .exceptions import HandlerException


class ChatRunner:
    """
    Chat runner.
    
    This class serves as the primary entry point
    for running the chat system.
    It sets up the necessary infrastructure
    and manages client connections at runtime.
    """
    def __init__(
        self,
        host: str,
        port: int,
        logger: logging.Logger
    ) -> None:
        """
        Construct a chat runner instance.
        
        Args:
            host (str): Server IP address.
            port (int): Port number to listen on.
        """
        self._host: str = host
        self._port: int = port
        
        self._logger: logging.Logger = logger
        
        self._rooms: RoomManager[Room[Client]] = RoomManager(
            WebSocketBroadcaster(),
            WordIDGenerator()
        )
        
        self._ctx: HandlerContext = HandlerContext(
            rooms=self._rooms,
            logger=self._logger
        )
    
    async def _handle_client_connection(
        self,
        conn: WebSocketConnection
    ) -> None:
        """
        Central handler that orchestrates the client lifecycle.
        """
        addr = format_addr(conn.remote_address)
        self._logger.info(f'Connection attempt from {addr}')
        
        try:
            room_entry_request = await receive_room_entry_request(conn)
        except HandlerException as e:
            self._logger.info(
                f'Initial connection stage for {addr} failed. Reason:\n  {e}'
            )
            await report_error(conn, e)
            await conn.close()
            return
        
        try:
            client, room = await process_room_entry(
                self._ctx,
                conn,
                room_entry_request
            )
        except HandlerException as e:
            self._logger.info(
                f'Room entry for {addr} rejected. Reason:\n  {e}'
            )
            await report_error(conn, e)
            await conn.close()
            return
        
        try:
            await handle_messaging(self._ctx, client, room)
        except HandlerException as e:
            self._logger.info(
                f'Messaging closed for {client} in room {room}. Reason:\n  {e}'
            )
            await report_error(conn, e)
        finally:
            await client.destroy()
    
    async def _main(self) -> None:
        """
        Private main entrypoint.
        """
        try:
            server = WebSocketServer(self._handle_client_connection)
            self._logger.info(f'Server listening on {self._host}:{self._port}')
            await server.serve(
                self._host,
                self._port
            )
        finally:
            await server.close()
    
    def run(self) -> None:
        """
        Public main entrypoint.
        """
        try:
            asyncio.run(self._main())
        except (KeyboardInterrupt, SystemExit):
            self._logger.info('Server shut down successfully')
