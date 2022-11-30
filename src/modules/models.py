"""Models for SQLAlchemy"""
import enum
from datetime import datetime
from sqlalchemy import Column, Integer, BigInteger, Boolean, Text, Date, Enum, DateTime, TypeDecorator
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

# region Enums
class GroupType(enum.IntEnum):
    """Group types"""
    itam_hq = 1
    club_admins = 2
    users = 3
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
    """Admin model for SQLAlchemy"""
    __tablename__ = 'admins'
    uid = Column(BigInteger,
                 primary_key=True,
                 autoincrement=False)
    name = Column(Text)
    gid = Column(IntEnum(GroupType), default=GroupType.users)

class Group(Base):
    """Group model for SQLAlchemy"""
    __tablename__ = 'groups'
    gid = Column(BigInteger,
                 primary_key=True,
                 autoincrement=False)
    name = Column(Text)
    gtype = Column(IntEnum(GroupType))

class Coworking(Base):
    """Coworking status model for SQLAlchemy"""
    __tablename__ = 'coworking_status'
    id = Column(BigInteger,
                primary_key=True)    # Unique event ID
    uid = Column(BigInteger)         # User ID
    time = Column(DateTime)          # Time of the event
    status = Column(Boolean)         # Coworking status

class UserData(Base):
    """User data model for SQLAlchemy"""
    __tablename__ = 'user_data'
    uid = Column(BigInteger, primary_key=True)
    bio = Column(Text)
    resume = Column(Text)
    birthday = Column(Date)
    phone = Column(Text)
    email = Column(Text)

class SuperChats(Base):
    """SuperChats model for SQLAlchemy"""
    __tablename__ = 'superchats'
    cid = Column(BigInteger, primary_key=True)  # Chat ID
    notifications_enabled = Column(Boolean, default=False)    # Coworking notifications
    plaintext_answers_enabled = Column(Boolean, default=False)  # Message answers (answer to regular messages from users)
