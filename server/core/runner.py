import websockets
from websockets.exceptions import ConnectionClosedOK

import asyncio
import logging
from http import HTTPStatus

from .client import Client, ClientList
from .events import Events, get_event_json

from .config import LOGGER_CONFIG

from typing import Coroutine

logging.basicConfig(**LOGGER_CONFIG)
logging.getLogger('websockets').setLevel(logging.ERROR)


def format_addr(addr: tuple):
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
        
        self._clients: ClientList[Client] = ClientList()
    
    async def _validate_initial_request(
        self,
        conn: websockets.ServerConnection,
        request: websockets.http11.Request
    ) -> Coroutine[None, None, None]:
        """
        Validate the client connection request.
        """
        addr = format_addr(conn.remote_address)
        name = request.headers.get('name', None)
        
        if name is None:
            reason = 'no name sent'
            
            logging.info(f'Rejecting {addr} from connection; Reason: {reason}')
            
            return websockets.Response(
                HTTPStatus.BAD_REQUEST, reason, websockets.Headers()
            )
        if self._clients.has_name(name):
            reason = 'name occupied'
            
            logging.info(f'Rejecting {addr} from connection; Reason: {reason}')
            
            return websockets.Response(
                HTTPStatus.FORBIDDEN, reason, websockets.Headers()
            )
        
        logging.info(f'Connection for {addr} approved')
        
        return None
    
    async def _handle_client_connection(
        self,
        conn: websockets.ServerConnection
    ) -> Coroutine[None, None, None]:
        """
        Handle the client connection.
        """
        try:
            client = Client(
                conn=conn,
                name=conn.request.headers['name'],
            )
            self._clients.add(client)
            
            logging.info(f'Connection from {client}')
            
            join_event_json = get_event_json(
                Events.JOIN,
                sender=client.name
            )
            self._clients.broadcast(join_event_json)

            async for message in client.conn:
                logging.info(f'Received "{message}" from {client}; Broadcasting')
                
                message_event_json = get_event_json(
                    Events.MESSAGE,
                    sender=client.name,
                    message=message
                )
                self._clients.broadcast(message_event_json)
        
        except ConnectionClosedOK:
            logging.info(f'Connection for {client} closed gracefully')
        
        except Exception as e:
            logging.error(
                f'Exception in {client} handler: '
                f'{e.__class__}: {str(e) or None}; Connection closed'
            )
        
        finally:
            leave_event_json = get_event_json(
                Events.LEAVE,
                sender=client.name
            )
            self._clients.broadcast(leave_event_json)
            
            logging.info(f'{client} disconnected')
            
            await client.destroy()
    
    async def _main(self) -> Coroutine[None, None, None]:
        """
        Private main entrypoint.
        """
        async with websockets.serve(
            self._handle_client_connection,
            self._host,
            self._port,
            process_request=self._validate_initial_request
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
