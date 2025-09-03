from abc import ABC, abstractmethod
from typing import Callable, Awaitable

from core.domain.ports import ClientConnection


class RealTimeServer(ABC):
    @abstractmethod
    async def serve(
        self,
        handler: Callable[
            [ClientConnection], Awaitable[None]
        ],
        host: str,
        port: int
    ) -> None:
        """
        Start serving.
        """
    
    @abstractmethod
    async def close(self) -> None:
        """
        Close the server.
        
        If the server is not active, do nothing.
        """
