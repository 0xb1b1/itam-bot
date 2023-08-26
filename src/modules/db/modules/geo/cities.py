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


class Cities(aobject):
    async def __init__(self, cities_collection: AsyncIOMotorCollection):
        self.cities: AsyncIOMotorCollection = cities_collection

        await self._create_geo_index()
        await self._create_unique_index()

    # region Internal methods
    async def _create_geo_index(self):
        """Create geospatial index on geolocation for the collection if not exists.
        """
        await self.cities.create_index([("geolocation", "2dsphere")])

    async def _create_unique_index(self):
        """Create unique index on name, district and subject for the collection if not exists.
        """
        await self.cities.create_index([("name", 1),
                                        ("district", 1),
                                        ("subject", 1)], unique=True)
    # endregion

    async def add(self,
                  name: str,
                  location: dict[str, int],
                  district: str,
                  subject: str,
                  country: str,
                  population: int):
        """Add a city.

        Args:
            location (dict[str, int]): City's location.
            name (str): City's name.
            district (str): City's district.
            subject (str): City's subject.
            population (int): City's population.
        """
        await self.cities.insert_one({
            "name": name,
            "geolocation": {
                "type": "Point",
                "coordinates": [float(location["lon"]), float(location["lat"])]
            },
            "district": district,
            "subject": subject,
            "country": country,
            "population": population
        })

    async def get(self, name: str) -> dict | None:
        """Get a city by name.

        Args:
            name (str): City's name.

        Returns:
            dict | None: City's data.
        """
        return await self.cities.find_one({"name": name})

    async def find_nearest(self, location: dict[str, int]) -> dict | None:
        """Find the nearest city.

        Args:
            location (dict[str, int]): Location to search from.

        Returns:
            dict | None: City's data.
        """
        return await self.cities.aggregate([
            {
                "$geoNear": {
                    "near": {
                        "type": "Point",
                        "coordinates": [location["lon"], location["lat"]]
                    },
                    "distanceField": "dist.calculated",
                    "maxDistance": 100000,
                    "includeLocs": "dist.location",
                    "spherical": True
                }
            }
        ]).to_list(1)
