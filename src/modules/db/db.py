#!/usr/bin/env python3

import asyncio
from shared import aobject
from motor.motor_asyncio import AsyncIOMotorClient
from .modules.users.users import Users
from .modules.spaces.spaces import Spaces
from .modules.geo.cities import Cities

# Type-hinting
from motor.motor_asyncio import AsyncIOMotorCollection, \
    AsyncIOMotorDatabase

# Errors
from pymongo.errors import DuplicateKeyError


class ITAMBotAsyncMongoDB(aobject):
    async def __init__(self, client: AsyncIOMotorClient, db_name: str):
        # self.client: AsyncIOMotorClient = client
        self.db: AsyncIOMotorDatabase = client[db_name]
        self.user: Users = await Users(self.db.users,
                                       self.db.admins)
        self.space: Spaces = await Spaces(self.db.spaces)
        self.city: Cities = await Cities(self.db.cities)
