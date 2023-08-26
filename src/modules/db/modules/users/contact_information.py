#!/usr/bin/env python3

from shared import aobject

# Type-hinting
from motor.motor_asyncio import AsyncIOMotorCollection, \
    AsyncIOMotorDatabase

# Errors
from pymongo.errors import DuplicateKeyError

class UserContactInformation(aobject):
    async def __init__(self, users_collection: AsyncIOMotorCollection):
        self.users: AsyncIOMotorCollection = users_collection

    async def get(self, user_id: int) -> dict | None:
        """Get a user's contact info.

        Args:
            user_id (int): User's Telegram ID.

        Returns:
            dict: User's contact info.
        """
        user = (await self.users.find_one(
            {"id": user_id},
            {"contact_info": 1}
        ))
        return user["contact_info"] if "contact_info" in user else None

    async def set_phone_number(self, user_id: int, phone_number: str):
        """Add a user's phone number.

        Args:
            user_id (int): User's Telegram ID.
            phone_number (str): User's phone number.
        """
        await self.users.update_one(
            {"id": user_id},
            {"$set": {
                "contact_info.phone_number": phone_number
            }}
        )

    async def get_phone_number(self, user_id: int) -> int:
        """Get a user's phone number.

        Args:
            user_id (int): User's Telegram ID.

        Returns:
            int: User's phone number.
        """
        contact_info = await self.get(user_id)
        if contact_info is None:
            return None
        return contact_info["phone_number"] if "phone_number" in contact_info else None

    async def rm_phone_number(self, user_id: int):
        """Remove a user's phone number.

        Args:
            user_id (int): User's Telegram ID.
        """
        await self.users.update_one(
            {"id": user_id},
            {"$unset": {
                "contact_info.phone_number": ""
            }}
        )

    async def set_email(self, user_id: int, email: str):
        """Add a user's email.

        Args:
            user_id (int): User's Telegram ID.
            email (str): User's email.
        """
        await self.users.update_one(
            {"id": user_id},
            {"$set": {
                "contact_info.email": email
            }}
        )

    async def get_email(self, user_id: int) -> str:
        """Get a user's email.

        Args:
            user_id (int): User's Telegram ID.

        Returns:
            str: User's email.
        """
        contact_info = await self.get(user_id)
        if contact_info is None:
            return None
        return contact_info["email"] if "email" in contact_info else None

    async def rm_email(self, user_id: int):
        """Remove a user's email.

        Args:
            user_id (int): User's Telegram ID.
        """
        await self.users.update_one(
            {"id": user_id},
            {"$unset": {
                "contact_info.email": ""
            }}
        )
