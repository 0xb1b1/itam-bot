#!/usr/bin/env python3


"""Models for SQLAlchemy."""
import enum
from datetime import datetime
# from sqlalchemy import ForeignKey
from sqlalchemy import Column, Integer, BigInteger, Boolean, Text, Date, DateTime, JSON, TypeDecorator
from sqlalchemy.orm import declarative_base  # , relationship

Base = declarative_base()


# region Enums
class GroupType(enum.IntEnum):
    """Group types."""
    admins = 1
    # club_admins = 2
    users = 3


class Skill(enum.IntEnum):
    """Skill types, >1 allowed."""
    backend = 0
    frontend = 1
    devops = 2
    analytics = 3
    infosec = 4
    mobile_dev = 5
    design = 6
    robotics = 7
    gamedev = 8
    machine_learning = 9

    def __str__(self):
        return self.name.capitalize().replace('_', ' ')


class CoworkingStatus(enum.IntEnum):
    """Coworking statuses."""
    open = 1
    event_open = 2
    temp_closed = 3
    closed = 4
    event_closed = 5
# endregion


# region Custom column types
class IntEnum(TypeDecorator):
    """
    Enables passing in a Python enum and storing the enum's *value* in the db.

    The default would have stored the enum's *name* (ie the string).
    """
    impl = Integer
    cache_ok: bool = True

    def __init__(self, enumtype, *args, **kwargs):
        super(IntEnum, self).__init__(*args, **kwargs)
        self._enumtype = enumtype

    def process_bind_param(self, value, dialect):
        if isinstance(value, int):
            return value

        return value.value

    def process_result_value(self, value, dialect):
        return self._enumtype(value)
# endregion


class User(Base):
    """Admin model for SQLAlchemy."""
    __tablename__ = 'users'
    uid = Column(BigInteger,
                 primary_key=True,
                 autoincrement=False)
    uname = Column(Text, default=None)
    first_name = Column(Text)
    last_name = Column(Text, default=None)
    gid = Column(IntEnum(GroupType), default=GroupType.users)


class UserData(Base):
    """User data model for SQLAlchemy."""
    __tablename__ = 'user_data'
    uid = Column(BigInteger, primary_key=True)
    bio = Column(Text)
    resume = Column(Text)
    birthday = Column(Date)
    phone = Column(BigInteger)
    email = Column(Text)


class UserSkill(Base):
    """User skills model for SQLAlchemy.

    Multiple skills per uid are allowed."""
    __tablename__ = 'user_skills'
    id = Column(BigInteger, primary_key=True)
    uid = Column(BigInteger)
    skill = Column(IntEnum(Skill), default=None)


class Group(Base):
    """Group model for SQLAlchemy."""
    __tablename__ = 'groups'
    gid = Column(BigInteger,
                 primary_key=True,
                 autoincrement=False)
    name = Column(Text)
    gtype = Column(IntEnum(GroupType))


class Coworking(Base):
    """Coworking status model for SQLAlchemy."""
    __tablename__ = 'coworking_status'
    id = Column(BigInteger, primary_key=True)
    uid = Column(BigInteger)
    time = Column(DateTime, default=datetime.utcnow)
    status = Column(IntEnum(CoworkingStatus))
    temp_delta = Column(Integer, default=None)


class CoworkingTrustedUser(Base):
    """Coworking trusted users model for SQLAlchemy."""
    __tablename__ = 'coworking_trusted_users'
    uid = Column(BigInteger, primary_key=True, nullable=False)
    admin_uid = Column(BigInteger, nullable=False)
    time = Column(DateTime, default=datetime.utcnow, nullable=False)


class AdminCoworkingNotification(Base):
    """Admin coworking notifications model for SQLAlchemy."""
    __tablename__ = 'admin_coworking_notifications'
    id = Column(BigInteger, primary_key=True)
    status_id = Column(BigInteger)


class ChatSettings(Base):
    """ChatSettings model for SQLAlchemy."""
    __tablename__ = 'chat_settings'
    cid = Column(BigInteger, primary_key=True)
    notifications_enabled = Column(Boolean, default=False)
    plaintext_answers_enabled = Column(Boolean, default=False)


yandex_internship_flow_json = {
    'day_1': {
        'msg_1': False,
        'msg_2': False,
        'msg_3': False
    },
    'day_2': {
        'msg_1': False,
        'msg_2': False,
        'msg_3': False,
        'msg_4': False
    },
    'day_3': {
        'msg_1': False,
        'msg_2': False,
        'msg_3': False,
        'msg_4': False
    },
    'day_4': {
        'msg_1': False,
        'msg_2': False,
        'msg_3': False,
        'msg_4': False
    },
    'day_5': {
        'msg_1': False,
        'msg_2': False,
        'msg_3': False
    },
}


class YandexInternshipUser(Base):
    """
    Yandex Internship User (bot skill) model for SQLAlchemy.

    `flow_json` is a dict that contains information about whether the user received a message or not.
    """
    __tablename__ = 'skill_yandex_internship_users'
    uid = Column(BigInteger, primary_key=True)
    ts = Column(DateTime, default=datetime.utcnow, nullable=False)
    agreed = Column(Boolean, nullable=False)
    is_notified_later = Column(Boolean, default=False, nullable=False)
    is_registered = Column(Boolean, default=False, nullable=False)
    registered_notified_stage = Column(Integer, default=0, nullable=False)  # 0, 1, 2
    registered_notified_last_ts = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_registered_confirmed = Column(Boolean, default=False, nullable=False)
    is_flow_activated = Column(Boolean, default=False, nullable=False)
    flow_last_ts = Column(DateTime, default=datetime.utcnow, nullable=False)
    flow_json = Column(JSON, default=yandex_internship_flow_json, nullable=False)

    def __repr__(self):
        return f'<YandexInternshipUser {self.uid=}, {self.ts=}, {self.agreed=}, {self.is_notified_later=}, \
{self.is_registered=}, {self.registered_notified_stage=}, {self.registered_notified_last_ts=}, \
{self.is_registered_confirmed}, {self.is_flow_activated=}, {self.flow_last_ts=}, {self.flow_json=}>'
