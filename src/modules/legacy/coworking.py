#!/usr/bin/env python3

"""Coworking status manager."""
# region Imports
# from modules.models import CoworkingStatus  #! TODO: redo for mongo

from modules.db.db import ITAMBotAsyncMongoDB
# endregion


class Manager:
    """Coworking management class."""

    def __init__(self, db):
        """Initialize coworking manager."""
        self.db: ITAMBotAsyncMongoDB = db

    # region Get status
    def get_status(self) -> CoworkingStatus:
        """Get coworking status."""
        return self.db.get_coworking_status()

    def get_delta(self) -> int:
        """
        Get coworking status delta in minutes.

        Coworking status delta is the period of time in minutes \
        designated for the coworking status by an admin \
        that shows how long a coworking status will be active.
        """
        return self.db.get_coworking_delta()
    # endregion

    # region Mutate status
    def open(self, uid: int) -> CoworkingStatus:
        """Mutate coworking status to open."""
        return self.db.set_coworking_status(CoworkingStatus.open, uid)

    def close(self, uid: int) -> CoworkingStatus:
        """Mutate coworking status to closed."""
        return self.db.set_coworking_status(CoworkingStatus.closed, uid)

    def temp_close(self, uid: int, delta_mins: int = 15) -> CoworkingStatus:
        """Mutate coworking status to temporarily closed."""
        return self.db.set_coworking_status(CoworkingStatus.temp_closed,
                                            uid, delta_mins=delta_mins)

    def event_open(self, uid: int) -> CoworkingStatus:
        """Mutate coworking status to event open."""
        return self.db.set_coworking_status(CoworkingStatus.event_open, uid)

    def event_close(self, uid: int) -> CoworkingStatus:
        """Mutate coworking status to event closed."""
        return self.db.set_coworking_status(CoworkingStatus.event_closed, uid)
    # endregion

    # region Logs
    def get_log(self) -> list:
        """Get coworking status log."""
        return self.db.get_coworking_log()

    def get_log_str(self) -> str:
        """Get coworking status log as a string."""
        return self.db.get_coworking_log_str()

    def trim_log(self, limit: int = 10) -> None:
        """
        Trim coworking status log to a specified limit.

        Defaults to 10 entries.
        """
        return self.db.trim_coworking_status_log(limit)
    # endregion

    # region Notifications
    def notified_closed_during_hours_today(self) -> bool:
        """Check if admins have been notified about the \
        coworking space being closed during hours today."""
        return self.db.coworking_notified_admin_closed_during_hours_today()

    def notified_open_after_hours_today(self) -> bool:
        """Check if admins have been notified about the \
        coworking space being open after hours today."""
        return self.db.coworking_notified_admin_open_after_hours_today()
    # endregion

    # region User trust
    def is_trusted(self, user_id: int) -> bool:
        """Check if a user is trusted."""
        return self.db.is_coworking_user_trusted(user_id)

    def add_trusted_user(self, user_id: int, admin_id: int) -> bool:
        """Add a user to the trusted users list."""
        return self.db.coworking_trusted_user_add(user_id, admin_id)

    def del_trusted_user(self, user_id: int) -> None:
        """Remove a user from the trusted users list."""
        return self.db.coworking_trusted_user_del(user_id)

    def get_trusted_user_admin_uid(self, user_id: int) -> int:
        """TODO: Check if this is used."""
        return self.db.coworking_trusted_user_get_admin_uid(user_id)
    # endregion

    # region Information
    def opened_today(self) -> bool:
        """Check if the coworking space has been opened today."""
        return self.db.coworking_opened_today()

    def is_responsible(self, uid: int) -> bool:
        """Check if a user is responsible for the coworking space."""
        return self.db.get_coworking_responsible() == uid

    def get_responsible_uname(self) -> str:
        """Get the username of the user responsible for the coworking space."""
        return self.db.get_coworking_responsible_uname()

    def get_responsible_uid(self) -> int:
        """Get the user ID of the user responsible for the coworking space."""
        return self.db.get_coworking_responsible()
    # endregion

    # region Location
    location = {'lat': 55.727252,
                'lon': 37.607302}
    # endregion
