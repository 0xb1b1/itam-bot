#!/usr/bin/env python3

"""Coworking status manager"""
# region Imports
from modules.models import CoworkingStatus
# endregion

class Manager:
    def __init__(self, db):
        self.db = db

    def get_status(self) -> CoworkingStatus:
        return self.db.get_coworking_status()

    def get_delta(self) -> int:
        return self.db.get_coworking_delta()

    def toggle_status(self, uid: int) -> CoworkingStatus:
        return self.db.toggle_coworking_status(uid)

    def open(self, uid: int) -> CoworkingStatus:
        return self.db.set_coworking_status(CoworkingStatus.open, uid)

    def close(self, uid: int) -> CoworkingStatus:
        return self.db.set_coworking_status(CoworkingStatus.closed, uid)

    def temp_close(self, uid: int, delta_mins: int = 15) -> CoworkingStatus:
        return self.db.set_coworking_status(CoworkingStatus.temp_closed, uid, delta_mins=delta_mins)

    def event_open(self, uid: int) -> CoworkingStatus:
        return self.db.set_coworking_status(CoworkingStatus.event_open, uid)

    def get_log(self) -> list:
        return self.db.get_coworking_log()

    def get_log_str(self) -> str:
        return self.db.get_coworking_log_str()

    def trim_log(self, limit: int = 10) -> None:
        return self.db.trim_coworking_status_log(limit)

    def notified_closed_during_hours_today(self) -> bool:
        return self.db.coworking_notified_admin_closed_during_hours_today()

    def notified_open_after_hours_today(self) -> bool:
        return self.db.coworking_notified_admin_open_after_hours_today()

    def opened_today(self) -> bool:
        return self.db.coworking_opened_today()

    def is_responsible(self, uid: int) -> bool:
        return self.db.get_coworking_responsible() == uid