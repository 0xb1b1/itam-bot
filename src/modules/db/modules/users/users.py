#!/usr/bin/env python3

from shared import aobject
from .skills import UserSkills
from .information import UserInformation
from .contact_information import UserContactInformation
from .admins import UserAdmins

# Type-hinting
from motor.motor_asyncio import AsyncIOMotorCollection, \
    AsyncIOMotorDatabase

# Errors
from pymongo.errors import DuplicateKeyError

class Users(aobject):
    async def __init__(self,
                       users_collection: AsyncIOMotorCollection,
                       admins_collection: AsyncIOMotorCollection):
        self.users: AsyncIOMotorCollection = users_collection

        await self._create_unique_index()

        self.skill = await UserSkills(self.users)
        self.contact = await UserContactInformation(self.users)
        self.info = await UserInformation(self.users)
        self.admin = await UserAdmins(self, admins_collection)

    # region Internal methods
    async def _create_unique_index(self):
        """Create unique index for the collection if not exists.

        Raises:
            RuntimeError: A duplicate of a user (same id) already exists.
        """
        try:
            await self.users.create_index("id", unique=True)
        except DuplicateKeyError:
            raise RuntimeError("Duplicate keys in collection 'users'! Unable to create unique index.")

    async def _get_indexes(self):
        """Get all indexes of the collection.

        Returns:
            str: collection indexes.
        """
        return await self.users.index_information()
    # endregion

    async def add(self, id_: int,
                  username: str = None,
                  first_name: str = None,
                  last_name: str = None):
        """Adds a new user to the database.

        Args:
            id_ (int): User's Telegram ID.
            first_name (str, optional): User's first name. Defaults to None.
            last_name (str, optional): User's last name. Defaults to None.

        Raises:
            DuplicateKeyError: Another user with the same id already exists.
        """
        info = {}
        if first_name is not None:
            info["first_name"] = first_name
        if last_name is not None:
            info["last_name"] = last_name
        await self.users.insert_one({
            "id": id_,
            "username": username,
            "info": info,  # Other user's information
            "contact_info": {},  # phone_number, email, etc.
            "skills": {},  # Each skill contains skill name (name) and skill proficiency level (level)
        })

    async def exists(self, id_: int) -> bool:
        """Check if a user exists.

        Args:
            id_ (int): User's Telegram ID.

        Returns:
            bool: True if user exists, False otherwise.
        """
        return await self.users.count_documents({"id": id_}) > 0

    async def rm(self, id_: int):
        """Remove a user's skill.

        Args:
            id_ (int): User's Telegram ID.
        """
        await self.users.delete_one({"id": id_})

    async def get(self, id_: int) -> dict:
        """Get a user's information.

        Args:
            id_ (int): User's Telegram ID.

        Returns:
            dict: User's information.
        """
        return await self.users.find_one({"id": id_})

    async def get_all_ids(self) -> list:
        """Get all users' ids.

        Returns:
            list: List of users' ids.
        """
        return [user["id"] async for user in self.users.find({}, {"id": 1})]
