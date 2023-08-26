#!/usr/bin/env python3

from shared import aobject

from datetime import datetime

# Type-hinting
from motor.motor_asyncio import AsyncIOMotorCollection, \
    AsyncIOMotorDatabase

# Errors
from pymongo.errors import DuplicateKeyError

class UserInformation(aobject):
    async def __init__(self, users_collection: AsyncIOMotorCollection):
        self.users: AsyncIOMotorCollection = users_collection

        await self._create_unique_index()

    # region Internal methods
    async def _create_unique_index(self):
        """Create geospatial index on users.info.geolocation for the collection if not exists.
        """
        await self.users.create_index([("info.geolocation", "2dsphere")])
    # endregion

    # region Test methods
    async def _calculate_geo_distance(self, id1: int, id2: int) -> int | None:
        """Calculate the distance between two users' geolocations.

        Args:
            id1 (int): User 1 Telegram ID.
            id2 (int): User 2 Telegram ID.

        # Raises:
        #     ValueError: _description_

        Returns:
            float: Distance in meters.
        """
        user1 = await self.get_geo(id1)
        user2 = await self.get_geo(id2)
        if user1 is None or user2 is None:
            return None
        return int((await self.users.aggregate([
            {
                "$geoNear": {
                    "near": {
                        "type": "Point",
                        "coordinates": [user1["lon"], user1["lat"]]
                    },
                    "distanceField": "dist.calculated",
                    "maxDistance": 100000,
                    "query": {
                        "id": id2
                    },
                    "includeLocs": "dist.location",
                    "spherical": True
                }
            }
        ]).to_list(1))[0]["dist"]["calculated"])
    # endregion

    async def get(self, id_: int) -> dict | None:
        """Get a user's information

        Args:
            id_ (int): User's Telegram ID.

        Returns:
            dict: User's information.
        """
        user = (await self.users.find_one(
            {"id": id_},
            {"info": 1}
        ))
        return user["info"] if "info" in user else None

    # region First name
    async def set_first_name(self, id_: int, first_name: str):
        """Add a user's first name.

        Args:
            id_ (int): User's Telegram ID.
            first_name (str): User's first name.
        """
        await self.users.update_one(
            {"id": id_},
            {"$set": {
                "info.first_name": first_name
            }}
        )

    async def get_first_name(self, id_: int) -> str:
        """Get a user's first name.

        Args:
            id_ (int): User's Telegram ID.

        Returns:
            str: User's first name.
        """
        info = await self.get(id_)
        if info is None:
            return None
        return info["first_name"] if "first_name" in info else None

    async def rm_first_name(self, id_: int):
        """Remove a user's first name.

        Args:
            id_ (int): User's Telegram ID.
        """
        await self.users.update_one(
            {"id": id_},
            {"$unset": {
                "info.first_name": ""
            }}
        )
    # endregion

    # region Last name
    async def set_last_name(self, id_: int, last_name: str):
        """Add a user's last name.

        Args:
            id_ (int): User's Telegram ID.
            last_name (str): User's last name.
        """
        await self.users.update_one(
            {"id": id_},
            {"$set": {
                "info.last_name": last_name
            }}
        )

    async def get_last_name(self, id_: int) -> str:
        """Get a user's last name.

        Args:
            id_ (int): User's Telegram ID.

        Returns:
            str: User's last name.
        """
        info = await self.get(id_)
        if info is None:
            return None
        return info["last_name"] if "last_name" in info else None

    async def rm_last_name(self, id_: int):
        """Remove a user's last name.

        Args:
            id_ (int): User's Telegram ID.
        """
        await self.users.update_one(
            {"id": id_},
            {"$unset": {
                "info.last_name": ""
            }}
        )
    # endregion

    # region Birthday
    async def set_birthday(self, id_: int, birthday: datetime):
        """Add a user's birthday.

        Args:
            id_ (int): User's Telegram ID.
            birthday (datetime): User's birthday. Always use UTC timezone (like `datetime.now(tz=timezone.utc)`).

        Raises:
            ValueError: Birthday must be timezone-aware.
        """
        if birthday.tzinfo is None:
            raise ValueError("birthday must be timezone-aware")
        await self.users.update_one(
            {"id": id_},
            {"$set": {
                "info.birthday": birthday
            }}
        )

    async def get_birthday(self, id_: int) -> datetime:
        """Get a user's birthday.

        Args:
            id_ (int): User's Telegram ID.

        Returns:
            datetime: User's birthday.
        """
        info = await self.get(id_)
        if info is None:
            return None
        return info["birthday"] if "birthday" in info else None

    async def rm_birthday(self, id_: int):
        """Remove a user's birthday.

        Args:
            id_ (int): User's Telegram ID.
        """
        await self.users.update_one(
            {"id": id_},
            {"$unset": {
                "info.birthday": ""
            }}
        )
    # endregion

    # region Bio
    async def set_bio(self, id_: int, bio: str):
        """Add a user's bio.

        Args:
            id_ (int): User's Telegram ID.
            bio (str): User's bio.
        """
        await self.users.update_one(
            {"id": id_},
            {"$set": {
                "info.bio": bio
            }}
        )

    async def get_bio(self, id_: int) -> int:
        """Get a user's bio.

        Args:
            id_ (int): User's Telegram ID.

        Returns:
            int: User's bio.
        """
        info = await self.get(id_)
        if info is None:
            return None
        return info["bio"] if "bio" in info else None

    async def rm_bio(self, id_: int):
        """Remove a user's bio.

        Args:
            id_ (int): User's Telegram ID.
        """
        await self.users.update_one(
            {"id": id_},
            {"$unset": {
                "info.bio": ""
            }}
        )
    # endregion

    # region Geolocation
    async def set_geo(self, id_: int, geolocation: dict[str, int]):
        """Add a user's geolocation in GeoJSON format.

        Args:
            id_ (int): User's Telegram ID.
            geo (dict): User's geolocation in format {"lon": 0.0, "lat": 0.0}.
        """
        await self.users.update_one(
            {"id": id_},
            {"$set": {
                "info.geolocation": {
                    "type": "Point",
                    "coordinates": [geolocation["lon"], geolocation["lat"]]
                }
            }}
        )

    async def get_geo(self, id_: int) -> dict:
        """Get a user's geolocation in GeoJSON format.

        Args:
            id_ (int): User's Telegram ID.

        Returns:
            dict: User's geolocation in format {"lon": 0.0, "lat": 0.0}.
        """
        info = await self.get(id_)
        if info is None:
            return None
        geolocation = info["geolocation"] if "geolocation" in info else None
        if geolocation is None:
            return None
        if "coordinates" not in geolocation:
            return None
        return {"lon": geolocation["coordinates"][0], "lat": geolocation["coordinates"][1]}

    async def rm_geo(self, id_: int):
        """Remove a user's geolocation.

        Args:
            id_ (int): User's Telegram ID.
        """
        await self.users.update_one(
            {"id": id_},
            {"$unset": {
                "info.geolocation": ""
            }}
        )
    # endregion
