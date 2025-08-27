import websockets
import enum
from .word_id import WordIDGenerator
from typing import (
    Iterator,
    Callable,
    Self,
    Any
)


class RoomRules(enum.StrEnum):
    CREATE = 'CREATE'
    RANDOM = 'RANDOM'
    ID = 'ID'


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


class Room:
    """
    Client container.
    
    It guarantees that only active clients
    are in the room at any given moment.
    """
    
    def __init__(self, id: str) -> None:
        """
        Construct a Room instance.
        """
        self._id: str = id
        self._clients: set[Client] = set()
    
    def __repr__(self) -> str:
        return f'Room(id={self._id}, clients_count={len(self._clients)})'
    
    @property
    def id(self):
        return self._id
    
    def add(self, client: Client) -> None:
        """
        Add `client` to the room.

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
        Remove `client` from the room.
        
        Args:
            client (Client): Client to remove.
        
        Raises:
            ValueError: If `client` is not in the room.
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


class RoomManager:
    def __init__(self) -> None:
        self._id_generator: WordIDGenerator = WordIDGenerator()
        self._rooms_by_id: dict[str, Room] = {}
    
    def create_room(self) -> Room:
        """
        Create a new room and add it to the manager.
        
        Returns:
            Created room.
        """
        room_id = self._generate_room_id()
        room = Room(room_id)
        self._rooms_by_id[room_id] = room
        return room
    
    def _generate_room_id(self, max_retries=1000) -> str:
        """
        Generate a unique ID that is not occupied by any room.
        
        Args:
            max_retries (int): Number of generation attempts.
        """
        retries = 0
        while retries < max_retries:
            id = self._id_generator.generate_id()
            if id not in self._rooms_by_id:
                return id
            retries += 1
        raise ValueError(
            f'Failed to generate a unique'
            f'ID after {max_retries} retries.'
        )
    
    def choose_least(self) -> Room:
        """
        Choose a room with minimum number of connections.
        
        Returns:
            The least occupied room.
        
        Raises:
            IndexError: If no rooms present.
        """
        rooms = self._rooms_by_id.values()
        if not rooms:
            raise IndexError('No rooms to choose from')
        return min(rooms, key=len)
    
    def has_id(self, id: str) -> bool:
        """
        Whether `id` is occupied by any room.
        """
        return id in self._rooms_by_id
    
    def select_by_id(self, id: str) -> Room:
        """
        Select a room by `id`.
        
        Raises:
            KeyError: If no room with `id` found.
        """
        if not self.has_id(id):
            raise KeyError("'id' is not used by any room")
        return self._rooms_by_id[id]
    
    def allocate_room(self, room_rule: str | RoomRules, **options) -> Room:
        """
        Allocate a room according to `room_rule`.
        
        Depending on a rule, it may choose
        an available room or create a new one.
        
        Args:
            room_rule (str): Allocation rule.
            options: Options specific to a room rule.
        
        Returns:
            Allocated room object.
        
        Raises:
            ValueError: If `room_rule` is invalid.
            Others: Room rule specific exceptions.
        """
        match room_rule:
            case RoomRules.CREATE:
                room = self.create_room()
            case RoomRules.RANDOM:
                try:
                    room = self.choose_least()
                except IndexError:
                    room = self.create_room()
            case RoomRules.ID:
                room = self.select_by_id(options['id'])
            case _:
                raise ValueError(f"'room_rule' must be in {RoomRules}")
        return room
