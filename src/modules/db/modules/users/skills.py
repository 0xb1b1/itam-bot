#!/usr/bin/env python3

from shared import aobject

# Type-hinting
from motor.motor_asyncio import AsyncIOMotorCollection, \
    AsyncIOMotorDatabase

# Errors
from pymongo.errors import DuplicateKeyError

class UserSkills(aobject):
    async def __init__(self, users_collection: AsyncIOMotorCollection):
        self.users: AsyncIOMotorCollection = users_collection

    async def add(self, id_: int, skill_name: str, skill_level: int = 0):
        """Adds a new skill to a user.

        Args:
            id_ (int): User's Telegram ID.
            skill_name (str): Skill name.
            skill_level (int): Skill proficiency level.
        """
        await self.users.update_one(
            {"id": id_},
            {"$set": {
                f"skills.{skill_name}": skill_level
            }}
        )

    async def rm(self, id_: int, skill_name: str):
        """Removes a skill from a user.

        Args:
            id_ (int): User's Telegram ID.
            skill_name (str): Skill name.
        """
        await self.users.update_one(
            {"id": id_},
            {"$unset": {
                f"skills.{skill_name}": ""
            }}
        )

    async def set_level(self, id_: int, skill_name: str, skill_level: int):
        """Set a certain skill level for a user's skill.

        Args:
            id_ (int): User's Telegram ID.
            skill_name (str): Skill name to mutate.
            skill_level (int): New skill level for `skill_name`.

        # Raises:
        #     RuntimeError: _description_
        """
        await self.users.update_one(
            {"id": id_},
            {"$set": {
                f"skills.{skill_name}": skill_level
            }}
        )

    async def get_skill(self, id_: int, skill_name: str) -> dict | None:
        """Get a user's skill informaton.

        Args:
            id_ (int): User's Telegram ID.
            skill_name (str): Skill name to get information about.

        Returns:
            dict | None: Skill information if found, None otherwise.
        """
        skill_info = (await self.users.find_one(
            {"id": id_},
            {"skills": {skill_name: 1}}
        ))['skills']
        return skill_info if skill_info != {} else None
