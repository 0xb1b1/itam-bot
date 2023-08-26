#!/usr/bin/env python3

import config
from shared import aobject

from datetime import datetime, timezone
from enum import Enum

# Type-hinting
from motor.motor_asyncio import AsyncIOMotorCollection, \
    AsyncIOMotorDatabase

# Errors
from pymongo.errors import DuplicateKeyError

# Collection schema
# ! TODO: Check if _id in mongo is able to be referenced in another collection
# space:
# {
#    "name": str,
#    "location": str,
#    "description": str,
#    "capacity": int,
#    "states": [{
#        "state": str,
#        "timestamp": datetime,
#        "user_id": int
#        "delta": Optional[int]
#    }]
# }

class SpaceStates(Enum):
    """Space states enum."""
    OPEN = "open"
    CLOSED = "closed"
    OCCUPIED = "occupied"
    TEMPORARILY_CLOSED = "temporarily_closed"

class Spaces(aobject):
    async def __init__(self, spaces_collection: AsyncIOMotorCollection):
        self.spaces: AsyncIOMotorCollection = spaces_collection

    # region Internal methods
    async def _create_unique_index(self):
        """Create unique index for the collection if not exists.

        Raises:
            DuplicateKeyError: A duplicate of a space (same name) already exists.
        """
        try:
            await self.users.create_index("name", unique=True)
        except DuplicateKeyError:
            raise RuntimeError("Duplicate keys in collection 'spaces'! Unable to create unique index.")

    async def _get_indexes(self):
        """Get all indexes of the collection.

        Returns:
            str: collection indexes.
        """
        return await self.spaces.index_information()
    # endregion

    async def get_all(self) -> list:
        """Get all spaces.

        Returns:
            list: List of spaces.
        """
        return await self.spaces.find().to_list(None)

    async def get(self, name: str) -> dict | None:
        """Get a space.

        Args:
            name (str): Space's name.

        Returns:
            dict: Space's information.
        """
        return await self.spaces.find_one({"name": name})

    async def exists(self, name: str) -> bool:
        """Check if a space exists.

        Args:
            name (str): Space's name.

        Returns:
            bool: True if space exists, False otherwise.
        """
        return await self.spaces.count_documents({"name": name}) > 0

    # region Spaces
    async def add(self, name: str, location: str, description: str, capacity: int):
        """Adds a new space to the database.

        Args:
            name (str): Space's name.
            location (str): Space's location.
            description (str): Space's description.
            capacity (int): Space's capacity.

        Raises:
            DuplicateKeyError: Another space with the same name already exists.
        """
        await self.spaces.insert_one({
            "name": name,
            "location": location,
            "description": description,
            "capacity": capacity,
            "supervisors": [],
            "states": []
        })

    async def rm(self, name: str):
        """Remove a space.

        Args:
            name (str): Space's name.
        """
        await self.spaces.delete_one({"name": name})
    # endregion

    # region Add supervisor
    async def add_supervisor(self, space_name: str, user_id: int):
        """Add a new supervisor to a space.

        Args:
            space_name (str): Space's name.
            user_id (int): User's Telegram ID.
        """
        await self.spaces.update_one(
            {"name": space_name},
            {"$push": {
                "supervisors": user_id
            }}
        )

    async def is_supervisor(self, space_name: str, user_id: int) -> bool:
        """Check if a user is a supervisor of a space.

        Args:
            space_name (str): Space's name.
            user_id (int): User's Telegram ID.

        Returns:
            bool: True if user is a supervisor, False otherwise.
        """
        return await self.spaces.count_documents({"name": space_name, "supervisors": user_id}) > 0

    async def get_supervisors(self, space_name: str) -> list:
        """Get all supervisors of a space.

        Args:
            space_name (str): Space's name.

        Returns:
            list: List of supervisors' Telegram IDs.
        """
        space = await self.spaces.find_one({"name": space_name})
        return space["supervisors"] if "supervisors" in space else []

    async def rm_supervisor(self, space_name: str, user_id: int):
        """Remove a supervisor from a space.

        Args:
            space_name (str): Space's name.
            user_id (int): User's Telegram ID.
        """
        await self.spaces.update_one(
            {"name": space_name},
            {"$pull": {
                "supervisors": user_id
            }}
        )
    # endregion

    # region States
    async def add_state(self, space_name: str, state: SpaceStates, user_id: int, delta: int = None):
        """Add a new state to a space.

        Args:
            name (str): Space's name.
            state (SpaceStates): Space's new state.
            user_id (int): User's Telegram ID.
            delta (int, optional): State's delta. Defaults to None.

        Raises:
            RuntimeError: User is not a supervisor of the space.
            ValueError: Space does not exist.
        """
        # Check if the space exists
        if not await self.exists(space_name):
            raise ValueError("Space does not exist!")

        # Check is the user is a supervisor
        if not await self.is_supervisor(space_name, user_id):
            raise RuntimeError("User is not a supervisor of the space!")

        timestamp = datetime.now(tz=timezone.utc)
        if delta is not None:
            await self.spaces.update_one(
                {"name": space_name},
                {"$push": {
                    "states": {
                        "state": state,
                        "timestamp": timestamp,
                        "user_id": user_id,
                        "delta": delta
                    }
                }}
            )
        else:
            await self.spaces.update_one(
                {"name": space_name},
                {"$push": {
                    "states": {
                        "state": state,
                        "timestamp": timestamp,
                        "user_id": user_id
                    }
                }}
            )

    async def get_state(self, space_name: str) -> dict | None:
        """Get a space's current (last) state.

        Args:
            space_name (str): Space's name.

        Returns:
            dict: Space's current (last) state.
        """
        # Get last state from space's subdocument
        space = await self.spaces.find_one(
            {"name": space_name},
            {"states": {"$slice": -1}}
        )
        if space is None:
            return None
        # return space["states"][0] if "states" in space and len(space["states"]) > 0 else None
        # convert state into SpaceStates enum
        state = space["states"][0] if "states" in space and len(space["states"]) > 0 else None
        if state is None:
            return None
        state["state"] = SpaceStates(state["state"])
        return state

    async def rm_last_state(self, space_name: str):
        """Remove a space's last state.

        Args:
            space_name (str): Space's name.
        """
        await self.spaces.update_one(
            {"name": space_name},
            {"$pop": {
                "states": 1
            }}
        )
    # endregion
