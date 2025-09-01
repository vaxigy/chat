from abc import ABC, abstractmethod
from typing import Iterable


class ClientConnection(ABC):
    @property
    @abstractmethod
    def remote_address(self) -> tuple:
        """
        Return the connection address as a tuple.
        """
    
    @abstractmethod
    async def close(self) -> None:
        """
        Close the connection.
        """
    
    @abstractmethod
    async def send(self, message: str) -> None:
        """
        Send a message.
        
        Raises:
            ClientDisconnected: If client has disconnected.
        """
    
    @abstractmethod
    async def recv(self) -> str:
        """
        Receive a message.
        
        Raises:
            ClientDisconnected: If client has disconnected.
        """


class Broadcaster(ABC):
    @abstractmethod
    def broadcast(
        self,
        conns: Iterable[ClientConnection],
        message: str
    ) -> None:
        """
        Broadcast a message to the provided connections.
        """


class IDGenerator(ABC):
    @abstractmethod
    def generate_id(self) -> str:
        """
        Generate a random id.
        """
