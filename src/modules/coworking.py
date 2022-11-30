#!/usr/bin/env python3

"""Coworking status manager"""
# region Imports
# endregion

class Manager:
    def __init__(self, db):
        self.db = db

    def get_status(self) -> bool:
        return self.db.get_coworking_status()

    def toggle_status(self, uid) -> bool:
        return self.db.toggle_coworking_status(uid)

    def open(self, uid) -> bool:
        return self.db.set_coworking_status(True, uid)

    def close(self, uid) -> bool:
        return self.db.set_coworking_status(False, uid)

    def get_log(self) -> list:
        return self.db.get_coworking_log()

    def get_log_str(self) -> str:
        return self.db.get_coworking_log_str()
