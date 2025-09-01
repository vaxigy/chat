from typing import Callable, Self, Any

from .ports import ClientConnection


class Client:
    """
    Connected client.
    """
    def __init__(
        self,
        conn: ClientConnection,
        name: str,
    ) -> None:
        """
        Construct a client from `conn`.
        
        Args:
            conn (ClientConnection): Client connection.
            name (str): Name identifier.
        """
        self._conn: ClientConnection = conn
        self._name: str = name
        self._on_destroy_callbacks: list[Callable[[Self], Any]] = []
        self._is_active: bool = True
    
    def __repr__(self) -> str:
        return f'Client(name={self._name}, addr={self._conn.remote_address})'
    
    @property
    def conn(self) -> ClientConnection:
        return self._conn
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def is_active(self) -> bool:
        return self._is_active
    
    def register_on_destroy(
        self,
        callback: Callable[[Self], Any]
    ) -> None:
        """
        Subscribe `callback` to the client destroy event.
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
            snapshot = list(self._on_destroy_callbacks)
            for callback in snapshot:
                callback(self)
            
            await self._conn.close()
            self.__dict__.clear()
            
            self._is_active = False
