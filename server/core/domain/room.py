import enum
from typing import Iterator

from .client import Client
from .ports import Broadcaster, IDGenerator
from .exceptions import (
    InactiveClientJoinAttempt,
    NameInRoomOccupied,
    NoRoomWithID,
    InvalidRoomRule,
    NoRoomsAvailable
)


class RoomRules(enum.StrEnum):
    CREATE = 'CREATE'
    RANDOM = 'RANDOM'
    ID = 'ID'


class Room:
    """
    Client container.
    
    It guarantees that only active clients
    are in the room at any given moment.
    """
    
    def __init__(self, id: str, broadcaster: Broadcaster) -> None:
        """
        Construct a Room instance.
        """
        self._id: str = id
        self._broadcaster: Broadcaster = broadcaster
        self._clients: set[Client] = set()
    
    def __repr__(self) -> str:
        return f'Room(id={self._id}, clients_count={len(self._clients)})'
    
    @property
    def id(self) -> str:
        return self._id
    
    def add(self, client: Client) -> None:
        """
        Add `client` to the room.

        Args:
            client (Client): Client to add.
        
        Raises:
            RoomJoinError (subclasses): If failed to add the client.
        """
        if not client.is_active:
            raise InactiveClientJoinAttempt('Cannot add an inactive client')
        if self.has_name(client.name):
            raise NameInRoomOccupied(f"'{client.name}' name is occupied")
        
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
        self._broadcaster.broadcast(
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
    def __init__(
        self,
        broadcaster: Broadcaster,
        id_generator: IDGenerator
    ) -> None:
        self._broadcaster: Broadcaster = broadcaster
        self._id_generator: IDGenerator = id_generator
        self._rooms_by_id: dict[str, Room] = {}
    
    def create_room(self) -> Room:
        """
        Create a new room and add it to the manager.
        
        Returns:
            Created room.
        """
        room_id = self._generate_room_id()
        room = Room(room_id, self._broadcaster)
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
            NoRoomsAvailable: If no rooms present.
        """
        rooms = self._rooms_by_id.values()
        if not rooms:
            raise NoRoomsAvailable('No rooms to choose from')
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
            NoRoomWithID: If no room with `id` is found.
        """
        if not self.has_id(id):
            raise NoRoomWithID("'id' is not used by any room")
        return self._rooms_by_id[id]
    
    def allocate_room(self, room_rule: str | RoomRules, **options) -> Room:
        """
        Allocate a room according to `room_rule`.
        
        Depending on a rule, it may choose
        an available room or create a new one.
        
        Args:
            room_rule (Union[str, RoomRules]): Allocation rule.
            options: Options specific to a room rule.
        
        Returns:
            Allocated room object.
        
        Raises:
            InvalidRoomRule: If `room_rule` is invalid.
            Others: Room rule specific exceptions.
        """
        match room_rule:
            case RoomRules.CREATE:
                room = self.create_room()
            case RoomRules.RANDOM:
                try:
                    room = self.choose_least()
                except NoRoomsAvailable:
                    room = self.create_room()
            case RoomRules.ID:
                room = self.select_by_id(options['id'])
            case _:
                raise InvalidRoomRule(f"'room_rule' must be in {RoomRules}")
        return room
