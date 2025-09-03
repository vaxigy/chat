import logging
import websockets
from typing import Iterable, Callable, Awaitable, AsyncIterator
from abc import abstractmethod

from core.domain.ports import ClientConnection, Broadcaster
from core.domain.exceptions import ClientDisconnected

from core.application.ports import RealTimeServer

logging.getLogger('websockets').setLevel(logging.CRITICAL)


class ClientConnectionExtended(ClientConnection):
    """
    Infrastructure-only extension of the domain's `ClientConnection`.
    """
    
    @abstractmethod
    def raw(self) -> websockets.ServerConnection:
        """
        Get the underlying connection object.
        """


class WebSocketConnection(ClientConnectionExtended):
    def __init__(
        self,
        conn: websockets.ServerConnection
    ) -> None:
        self._conn = conn
    
    @property
    def remote_address(self) -> tuple[str, int]:
        return self._conn.remote_address
    
    async def send(self, message: str) -> None:
        try:
            await self._conn.send(message)
        except websockets.ConnectionClosed:
            raise ClientDisconnected(
                'Connection closed'
            ) from None
    
    async def recv(self) -> str:
        try:
            return await self._conn.recv()
        except websockets.ConnectionClosed:
            raise ClientDisconnected(
                'Connection closed'
            ) from None
    
    async def close(self, code: int = 1000, reason: str = '') -> None:
        await self._conn.close(code, reason)
    
    async def __aiter__(self) -> AsyncIterator[str]:
        while True:
            yield await self.recv()
    
    def raw(self) -> websockets.ServerConnection:
        return self._conn


class WebSocketBroadcaster(Broadcaster):
    @staticmethod
    def broadcast(
        conns: Iterable[ClientConnectionExtended],
        message: str
    ) -> None:
        websockets.broadcast((conn.raw() for conn in conns), message)


class WebSocketServer(RealTimeServer):
    def __init__(self) -> None:
        self._handler: Callable[
            [ClientConnection], Awaitable[None]
        ] | None = None
        self._server: websockets.Server | None = None
    
    async def serve(
        self,
        handler: Callable[
            [ClientConnection], Awaitable[None]
        ],
        host: str,
        port: int,
    ) -> None:
        self._handler = handler
        self._server = await websockets.serve(
            self._handler_wrap,
            host,
            port
        )
        await self._server.serve_forever()
    
    async def close(self) -> None:
        if self._server is not None:
            self._server.close()
            self._handler = self._server = None
    
    async def _handler_wrap(
        self,
        conn: websockets.ServerConnection
    ) -> Awaitable[None]:
        conn_wrap = WebSocketConnection(conn)
        await self._handler(conn_wrap)
