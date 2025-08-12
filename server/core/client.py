import websockets

from typing import (
    Iterator,
    Callable,
    Self,
    Any
)


class Client:
    """
    Connected client.
    """
    def __init__(
        self,
        conn: websockets.ServerConnection,
        name: str,
    ) -> None:
        """
        Construct a client from the socket connection `conn`.
        
        Args:
            conn (websockets.ServerConnection): Client connection.
            name (str): Name identifier.
        """
        self._conn: websockets.ServerConnection = conn
        self._name: str = name
        self._on_destroy_callbacks: list[Callable[[Self], Any]] = []
        self._is_active: bool = True
    
    def __repr__(self) -> str:
        return f'Client(name={self._name}, addr={self._conn.remote_address})'
    
    @property
    def conn(self):
        return self._conn
    
    @property
    def name(self):
        return self._name
    
    @property
    def is_active(self):
        return self._is_active
    
    def register_on_destroy(
        self,
        callback: Callable[[Self], Any]
    ) -> None:
        """
        Subscribe `callback` on the client destroy event.
        """
        self._on_destroy_callbacks.append(callback)
    
    def unregister_on_destroy(
        self,
        callback: Callable[[Self], Any]
    ) -> None:
        """
        Unsubscribe `callback` from the destroy event.
        
        Raises:
            ValueError: If `callback` is not subscribed.
        """
        if callback in self._on_destroy_callbacks:
            self._on_destroy_callbacks.remove(callback)
        else:
            raise ValueError("'callback' is not subscribed")
    
    async def destroy(self) -> None:
        """
        Activate the destroy event.
        
        This will close the connection, and make the object unusable.
        """
        if self._is_active:
            # It's important to notify subscribers
            # before destruction, so they can operate
            # on the object while it's still active.
            snapshot = list(self._on_destroy_callbacks)
            for callback in snapshot:
                callback(self)
            
            await self._conn.close()
            self.__dict__.clear()
            
            self._is_active = False


class ClientList:
    """
    Client container.
    
    It guarantees that only active clients
    are in the list at any given moment.
    """
    
    def __init__(self) -> None:
        """
        Construct a ClientList instance.
        """
        self._clients: set[Client] = set()
    
    def __repr__(self) -> str:
        return f'ClientList(clients_count={len(self)})'
    
    def add(self, client: Client) -> None:
        """
        Add `client` to the list.

        Args:
            client (Client): Client to add.
        
        Raises:
            ValueError: If `client` is inactive.
        """
        if not client.is_active:
            raise ValueError('Cannot add an inactive client')
        
        self._clients.add(client)
        client.register_on_destroy(self.remove)
    
    def remove(self, client: Client) -> None:
        """
        Remove `client` from the list.
        
        Args:
            client (Client): Client to remove.
        
        Raises:
            ValueError: If `client` is not in the list.
        """
        if client in self._clients:
            self._clients.remove(client)
            client.unregister_on_destroy(self.remove)
        else:
            raise ValueError("'client' is not in the list")
    
    def broadcast(self, message: str) -> None:
        """
        Broadcast `message` to all clients.

        Args:
            message (str): Message to broadcast.
        """
        websockets.broadcast(
            (client.conn for client in self._clients),
            message
        )
    
    def has_name(self, name: str) -> bool:
        """
        Check if a client with `name` is present.
        """
        return any(client.name == name for client in self._clients)
    
    def __iter__(self) -> Iterator[Client]:
        return iter(self._clients)
    
    def __len__(self) -> int:
        return len(self._clients)
