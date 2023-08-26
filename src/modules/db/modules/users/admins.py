#!/usr/bin/env python3

from enum import Enum

from shared import aobject

# Type-hinting
from motor.motor_asyncio import AsyncIOMotorCollection, \
    AsyncIOMotorDatabase

# Errors
from pymongo.errors import DuplicateKeyError


class UserAdmins(aobject):
    async def __init__(self, users_obj,
                       admins_collection: AsyncIOMotorCollection):
        self.users = users_obj
        self.admins: AsyncIOMotorCollection = admins_collection

        await self._create_unique_index()

    # region Internal methods
    async def _create_unique_index(self):
        """Create unique index for the collection if not exists.

        Raises:
            DuplicateKeyError: A duplicate of a admin (same id) already exists.
        """
        try:
            await self.admins.create_index("id", unique=True)
        except DuplicateKeyError:
            raise RuntimeError("Duplicate keys in collection 'admins'! Unable to create unique index.")
    # endregion

    async def add(self, id_: int,):
        """Adds a new admin with no scopes.

        Args:
            id_ (int): Admin's Telegram ID.

        Raises:
            ValueError: User does not exist in the database.
            DuplicateKeyError: Another admin with the same id already exists.
        """
        if not await self.users.exists(id_):
            raise ValueError("User does not exist in the database!")

        # avoid RuntimeError: dictionary changed size during iteration
        await self.admins.insert_one({
            "id": id_,
            # loop through all arguments and add them to the dict
            "scopes": {
                "supervision": False,
                "broadcasting": False,
                "analytics": False
            }
        })

    async def get(self, id_: int) -> dict | None:
        """Get an admin's permissions

        Args:
            id_ (int): Admin's Telegram ID.

        Returns:
            dict | None: Admin's scopes. If not an admin, returns None.
        """
        admin = (await self.admins.find_one(
            {"id": id_},
            {"scopes": 1}
        ))
        return admin["scopes"] if admin is not None and "scopes" in admin else None

    async def get_all_ids(self) -> list[int]:
        """Get all admins' Telegram IDs.

        Returns:
            list[int]: List of admins' Telegram IDs.
        """
        return [admin["id"] async for admin in self.admins.find({}, {"id": 1})]

    async def exists(self, id_: int) -> bool:
        """Check if an admin exists.

        Args:
            id_ (int): Admin's Telegram ID.

        Returns:
            bool: True if admin exists, False otherwise.
        """
        return await self.admins.count_documents({"id": id_}) > 0

    async def rm(self, id_: int):
        """Remove an admin.

        Args:
            id_ (int): Admin's Telegram ID.
        """
        await self.admins.delete_one({"id": id_})

    # region Scopes
    async def set_supervision(self, id_: int, is_enabled: bool):
        """Set supervision scope for an admin.

        Args:
            id_ (int): Admin's Telegram ID.
            is_enabled (bool): Supervision scope state for the admin.
        """
        await self.admins.update_one(
            {"id": id_},
            {"$set": {
                "scopes.supervisor": is_enabled
            }}
        )

    async def set_broadcasting(self, id_: int, is_enabled: bool):
        """Set broadcasting scope for an admin.

        Args:
            id_ (int): Admin's Telegram ID.
            is_enabled (bool): Broadcasting scope state for the admin.
        """
        await self.admins.update_one(
            {"id": id_},
            {"$set": {
                "scopes.broadcasting": is_enabled
            }}
        )

    async def set_analytics(self, id_: int, is_enabled: bool):
        """Set analytics scope for an admin.

        Args:
            id_ (int): Admin's Telegram ID.
            is_enabled (bool): Analytics scope state for the admin.
        """
        await self.admins.update_one(
            {"id": id_},
            {"$set": {
                "scopes.analytics": is_enabled
            }}
        )
    # endregion
