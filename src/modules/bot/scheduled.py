#!/usr/bin/env python3

"""Bot recurring functions"""

from asyncio import sleep
from datetime import datetime
from aiogram.types import ContentType

from modules import replies
from modules.db import CoworkingStatus
from modules.coworking import Manager as CoworkingManager
from modules.bot.broadcast import BotBroadcastFunctions


class BotScheduledFunctions:
    """Bot scheduled functions."""

    def __init__(self, bot, db, log):
        """Initialize bot scheduled functions."""
        self.db = db
        self.bot = bot
        self.cwman = CoworkingManager(db)
        self.log = log
        self.broadcast = BotBroadcastFunctions(bot, db, log)

    async def coworking_status_checker(self, open_time: datetime, close_time: datetime, timeout: int = 120):
        """Check if the coworking space is closed after open_time and open after close_time"""
        # TODO: Remove the following line when open_time notifications is implemented
        # ~Consume~ Use open_time variable to avoid linter warnings
        _ = open_time
        while True:
            try:
                # Set open_time and close_time to current date
                timed = datetime.utcnow()
                current_time = int(timed.timestamp())
                # open_time_ts = int(open_time.replace(year=timed.year, month=timed.month, day=timed.day).timestamp())
                close_time_ts = int(close_time.replace(year=timed.year, month=timed.month, day=timed.day).timestamp())
                if current_time > close_time_ts and self.cwman.get_status() in [CoworkingStatus.open,
                                                                                CoworkingStatus.event_open,
                                                                                CoworkingStatus.temp_closed]:
                    if not self.cwman.notified_open_after_hours_today():
                        # Send broadcast to admins
                        self.log.debug("Sending broadcast to admins about coworking space being open after hours")
                        await self.broadcast.broadcast(replies.coworking_open_after_hours(),
                                                       "admins", ContentType.TEXT)
                    else:
                        self.log.debug(f"NOT sending broadcast to admins (closed after open time); \
{self.cwman.notified_closed_during_hours_today()=}")
                # Check if the coworking space is closed after open_time
                # elif current_time <= open_time_ts and coworking.get_status() == CoworkingStatus.closed:
                #     if not coworking.opened_today() and not coworking.notified_closed_during_hours_today():
                #         # Send broadcast to admins
                #         log.debug("Sending broadcast to admins about coworking space being closed during hours")
                #         await broadcast(replies.coworking_closed_during_hours(), scope="admins")
                # Sleep for the specified amount of time before running again
                await sleep(timeout)
            except Exception as exc:
                self.log.error(f"Error in coworking_status_checker: {exc}")
                await sleep(timeout)
