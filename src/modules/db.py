#!/usr/bin/env python3
# region Dependencies
from datetime import date, datetime, timedelta
from os import getenv
from time import sleep
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from typing import List, Tuple, Union
from sqlalchemy.exc import OperationalError as sqlalchemyOpError
from psycopg2 import OperationalError as psycopg2OpError
# endregion

# region Local imports
from modules.models import CoworkingStatus, CoworkingTrustedUser, GroupType, Skill
from modules.models import Base, User, UserData, UserSkill, Group, ChatSettings, \
    Coworking, AdminCoworkingNotification
# endregion


class DBManager:
    def __init__(self, log):
        self.pg_user = getenv('PG_USER')
        self.pg_pass = getenv('PG_PASS')
        self.pg_host = getenv('PG_HOST')
        self.pg_port = getenv('PG_PORT')
        self.pg_db = getenv('PG_DB')
        self.log = log
        connected = False
        while not connected:
            try:
                self._connect()
            except (sqlalchemyOpError, psycopg2OpError):
                sleep(2)
            else:
                connected = True
        self._update_db()
        self.admin_groups = [GroupType.admins]

    def __del__(self):
        """Close the database connection when the object is destroyed"""
        self._close()

    # region Connection setup
    def _connect(self) -> None:
        """Connect to the postgresql database"""
        self.engine = create_engine(f'postgresql+psycopg2://{self.pg_user}:{self.pg_pass}@{self.pg_host}:{self.pg_port}\
/{self.pg_db}',
                                    pool_pre_ping=True)
        Base.metadata.bind = self.engine
        db_session = sessionmaker(bind=self.engine)
        self.session = db_session()

    def _close(self) -> None:
        """Closes the database connection"""
        self.session.close_all()

    # def _recreate_tables(self) -> None:  # Important: Do not use in production!
    #     """Removes and recreates all tables in DB"""
    #     Base.metadata.drop_all(self.engine)
    #     Base.metadata.create_all(self.engine)

    def _update_db(self) -> None:
        """Create the database structure if it doesn't exist (update)"""
        # Create the tables if they don't exist
        Base.metadata.create_all(self.engine)
        # !Create the default groups if they don't exist
        # Create ITAM admins group
        if not self.session.query(Group).filter(Group.gtype == GroupType.admins).first():
            self.add_group(gid=GroupType.admins, name='ITAM Headquarters', gtype=GroupType.admins)
        # Add the default admin from ENV if they don't exist
        if not self.session.query(User).filter(User.uid == getenv('DEFAULT_ADMIN_UID')).first():
            self.add_admin(uid=int(getenv('DEFAULT_ADMIN_UID')),
                           uname=getenv('DEFAULT_ADMIN_USERNAME'),
                           first_name=getenv('DEFAULT_ADMIN_FNAME'),
                           gid=GroupType.admins)
        self.__update_groups()
        # Create the first coworking status if it doesn't exist
        if not self.session.query(Coworking).first():
            self.set_coworking_status(CoworkingStatus.closed, int(getenv('DEFAULT_ADMIN_UID', "")))

    def __update_groups(self) -> None:
        """Create groups from the models in the database"""
        for group in GroupType:
            if not self.session.query(Group).filter(Group.gtype == group).first():
                self.add_group(gid=group, name=group.name, gtype=group)
    # endregion

    # region User management
    def user_exists(self, uid: int) -> bool:
        """Check if a user exists in the database"""
        return self.session.query(User).filter(User.uid == uid).first() is not None

    def add_regular_user(self, uid: int, uname: str, first_name: str, last_name: str) -> None:
        """Add a regular user of type `user` to the database"""
        if self.user_exists(uid):
            return
        user = User(uid=uid, uname=uname, first_name=first_name, last_name=last_name, gid=GroupType.users)
        self.session.add(user)
        self.session.commit()
        userdata = UserData(uid=uid)
        self.session.add(userdata)
        self.session.commit()

    def add_admin(self, uid: int, uname: str, first_name: str, gid: int):
        """Add an admin to the database"""
        admin = User(uid=uid, uname=uname, first_name=first_name, gid=gid)
        self.session.add(admin)
        self.session.commit()
        userdata = UserData(uid=uid)
        self.session.add(userdata)
        self.session.commit()

    def get_group_name(self, gid: int) -> str | None:
        """Get the name of a group from its ID"""
        group = self.session.query(Group).filter(Group.gid == gid).first()
        try:
            name = group.name
        except AttributeError:
            return None
        return name

    def get_uname(self, uid: int) -> str:
        return self.session.query(User).filter(User.uid == uid).first().uname

    def set_uname(self, uid: int, uname: str) -> None:
        """Set the username of a user"""
        self.session.query(User).filter(User.uid == uid).first().uname = uname
        self.session.commit()

    def is_uname_set(self, uid: int) -> bool:
        """Check if the uid has an uname set"""
        user = self.session.query(User).filter(User.uid == uid).first()
        if user is None:
            return False
        return user.uname is not None

    def does_user_exist(self, uid: int) -> bool:
        """Check if a user exists in the database"""
        return self.session.query(User).filter(User.uid == uid).first() is not None

    def is_admin(self, uid: int) -> bool:
        """Check if a user is in the admins list"""
        user = self.session.query(User).filter(User.uid == uid).first()
        if user is not None:
            group = self.session.query(Group).filter(Group.gid == user.gid).first()
            if group is not None:
                return group.gtype in self.admin_groups
        return False
    # endregion

    # region Group management
    def set_user_group(self, uid: int, gid: int):
        """Set the group id of an admin"""
        self.session.query(User).filter(User.uid == uid).first().gid = gid
        self.session.commit()

    def get_groups_and_ids(self) -> str:  # TODO: Change to List[Group]
        """Get a string list of group names and their respective IDs"""
        groups = self.session.query(Group).all()
        return "\n".join([f"{g.gid}. {g.name}" for g in groups])

    def get_groups_and_ids_as_dict_namekey(self) -> dict:
        """Get a dictionary of group names and their respective IDs"""
        groups_raw = self.session.query(Group).all()
        groups = {}
        for group in groups_raw:
            groups[group.name] = {
                "gid": group.gid
            }
        return groups

    def add_group(self, gid: int, name: str, gtype: GroupType):
        group = Group(gid=gid, name=name, gtype=gtype)
        self.session.add(group)
        self.session.commit()

    def get_groups(self, gtype: GroupType = None) -> List[Group]:  # TODO: FIX!
        """Get a string list of group names of a given type"""
        if gtype is not None:
            groups = self.session.query(Group).filter(Group.gtype == gtype).all()
        else:
            groups = self.session.query(Group).all()
        return groups
    # endregion

    # region Chat management
    def get_group_chats(self) -> List[int]:
        """Get a list of Telegram group chats from ChatSettings table"""
        chats = self.session.query(ChatSettings).filter(ChatSettings.cid < 0).all()
        return [c.cid for c in chats]
    # endregion

    # region Admin statistics
    def get_users_str(self, gid: int = None) -> str:
        """Get a string list of users of a given group"""
        if gid is not None:
            users = self.session.query(User).filter(User.gid == gid).all()
            return "\n".join([f"{i+1}. {u.first_name} [{u.uid}]" for i, u in enumerate(users)])
        else:
            users = self.session.query(User).all()
            return "\n".join([f"{i+1}. {u.first_name} [{u.uid}]" for i, u in enumerate(users)])

    def get_users_verbose_str(self) -> str:
        """Get a string list of users and their groups"""
        users = self.session.query(User).all()
        return "\n".join([f"{i+1}. [{u.first_name} {u.last_name if u.last_name else ''}] \
@{u.uname if u.uname else '—'} [{u.uid}] ({self.get_group_name(u.gid)})" for i, u in enumerate(users)])

    def get_users(self) -> List[User]:
        """Get a list of users."""
        return self.session.query(User).all()

    def get_users_data(self) -> List[UserData]:
        """Get a list of users data."""
        return self.session.query(UserData).all()

    def get_users_full(self) -> List[Tuple[User, UserData, List[UserSkill]]]:
        """Get a list of users and their data (including UserSkill list)"""
        users = self.session.query(User).all()
        users_data = self.session.query(UserData).all()
        users_skills = self.session.query(UserSkill).all()
        return [(u, ud, [us for us in users_skills if us.uid == u.uid])
                for u in users for ud in users_data if u.uid == ud.uid]

    def get_admins(self) -> List[User]:
        """Get a list of admins"""
        return self.session.query(User).filter(User.gid == GroupType.admins).all()

    def get_coworking_log(self) -> List[Coworking]:
        return self.session.query(Coworking).all()

    def get_coworking_log_str(self) -> str:
        return "\n".join([f"""{i+1}. {c.time} - {c.uid} - \
{'open' if c.status == CoworkingStatus.open
        else ('event_open' if CoworkingStatus.event_open
              else ('temp_closed' if CoworkingStatus.temp_closed
                    else 'closed'))}""" for i, c in enumerate(self.get_coworking_log())])

    def get_user_count(self) -> int:
        """Get the current amount of users in the database"""
        return self.session.query(User).count()

    def get_admin_count(self) -> int:
        """Get the current amount of admins in the database"""
        return self.session.query(User).filter(User.gid == GroupType.admins).count()

    def get_stats(self) -> dict:
        """Get a dict of all stats"""
        return {
            "users": self.get_user_count(),
            "admins": self.get_admin_count(),
            "coworking_status": self.get_coworking_status(),
            "coworking_log_count": len(self.get_coworking_log()),
            "coworking_notifications": self.get_coworking_notification_enabled_count()
        }
    # endregion

    # region User data getters
    def get_user_data(self, uid: int) -> dict | None:
        """Get information about a user"""
        main = self.session.query(User).filter(User.uid == uid).first()
        aux = self.session.query(UserData).filter(UserData.uid == uid).first()
        skills = self.session.query(UserSkill).filter(UserSkill.uid == uid).all()
        if main is None:
            return None
        return {
            "uid": main.uid,
            "uname": main.uname,
            "first_name": main.first_name,
            "last_name": main.last_name,
            "gname": self.get_group_name(main.gid),
            "phone": aux.phone if aux else None,
            "email": aux.email if aux else None,
            "birthday": aux.birthday if aux else None,
            "skills": [s.skill for s in skills]
        }

    def get_user_data_bio(self, uid: int) -> str | None:
        """Get the bio of a user"""
        user = (self.session.query(UserData)
                .filter(UserData.uid == uid)
                .first())
        return user.bio if user else "Био не установлено"

    def get_user_data_resume(self, uid: int) -> str:
        """Get the resume of a user"""
        user = (self.session.query(UserData)
                .filter(UserData.uid == uid)
                .first())
        return user.resume if user else "Резюме не установлено"
    # endregion

    # region User data setters
    def set_user_data_name(self, uid: int,
                           first_name: str,
                           last_name: str) -> Tuple[str, str]:
        """Set first and last names of a user"""
        user = self.session.query(User).filter(User.uid == uid).first()
        if user is None:
            raise AttributeError("User not found")
        user.first_name = first_name
        user.last_name = last_name
        self.session.commit()
        return first_name, last_name

    def set_user_first_name(self, uid: int, first_name: str) -> str:
        """Set the first name of a user"""
        user = self.session.query(User).filter(User.uid == uid).first()
        if user is None:
            raise AttributeError("User not found")
        user.first_name = first_name
        self.session.commit()
        return first_name

    def set_user_last_name(self, uid: int, last_name: str) -> str:
        """Set the last name of a user"""
        user = self.session.query(User).filter(User.uid == uid).first()
        if user is None:
            raise AttributeError("User not found")
        user.last_name = last_name
        self.session.commit()
        return last_name

    def set_user_birthday(self, uid: int, birthday: date) -> date:
        user = (self.session.query(UserData)
                .filter(UserData.uid == uid)
                .first())
        if user is None:
            raise AttributeError("User not found")
        user.birthday = birthday
        self.session.commit()
        return birthday

    def set_user_email(self, uid: int, email: str) -> str:
        # Check if at least one @ or . appears in the email
        if "@" not in email or "." not in email:
            raise ValueError("Incorrect email format")
        user = self.session.query(UserData).filter(UserData.uid == uid).first()
        if user is None:
            raise AttributeError("User not found")
        user.email = email
        self.session.commit()
        return email

    def set_user_phone(self, uid: int, phone: int) -> int:
        if not 5 < len(str(phone)) < 20 or str(phone)[0] == '-':
            raise ValueError("Incorrect phone format")
        # Check if phone is of type int
        int(phone)
        user = (self.session.query(UserData)
                .filter(UserData.uid == uid)
                .first())
        if user is None:
            raise AttributeError("User not found")
        user.phone = phone
        self.session.commit()
        return phone

    def skill_exists(self, uid: int, skill: Skill) -> bool:
        """Check if a skill exists for a user"""
        return (self.session.query(UserSkill)
                .filter(UserSkill.uid == uid,
                        UserSkill.skill == skill)
                .first()) is not None

    def add_user_skills(self,
                        uid: int,
                        skills: Union[Skill, List[Skill]]) -> None:
        """Add skills to a user."""
        if isinstance(skills, Skill):
            skills = [skills]
        for s in skills:
            if not self.skill_exists(uid, s):
                self.session.add(UserSkill(uid=uid, skill=s))
        self.session.commit()

    def set_user_skills(self,
                        uid: int,
                        skills: Union[Skill, List[Skill]]) -> None:
        """Set the skills of a user."""
        self.del_user_skills_all(uid)
        self.add_user_skills(uid, skills)

    def remove_user_skill(self, uid: int, skill: Skill) -> None:
        """Delete a skill from a user"""
        (self.session.query(UserSkill)
         .filter(UserSkill.uid == uid,
                 UserSkill.skill == skill)
         .delete())
        self.session.commit()

    def del_user_skills_all(self, uid: int) -> None:
        """Delete all skills from a user"""
        self.session.query(UserSkill).filter(UserSkill.uid == uid).delete()
        self.session.commit()
    # endregion

    # region Coworking management
    def get_coworking_status(self) -> CoworkingStatus:
        """Get the status of the coworking space"""
        user = (self.session.query(Coworking)
                .order_by(Coworking.id.desc())
                .first())
        if user is None:
            raise AttributeError("User not found")
        return user.status

    def get_coworking_delta(self) -> int:
        """Get the delta of the coworking space"""
        user = (self.session.query(Coworking)
                .order_by(Coworking.id.desc())
                .first())
        if user is None:
            raise AttributeError("User not found")
        return user.temp_delta

    def set_coworking_status(self,
                             status: CoworkingStatus,
                             uid: int,
                             delta_mins: int = 15) -> CoworkingStatus:
        """Update the status of the coworking space (add new entry to log)."""
        if status == CoworkingStatus.temp_closed:
            coworking_status = Coworking(status=status, uid=uid, temp_delta=delta_mins, time=datetime.utcnow())
        else:
            coworking_status = Coworking(status=status,
                                         uid=uid,
                                         time=datetime.utcnow())
        self.session.add(coworking_status)
        self.session.commit()
        return status

    def get_coworking_responsible(self) -> int:
        """Get the responsible uid for the coworking space key."""
        status = (self.session.query(Coworking)
                  .order_by(Coworking.id.desc())
                  .first())
        if status is None:
            raise AttributeError("Current coworking status not found")
        return status.uid

    def get_coworking_responsible_uname(self) -> str:
        """Get the responsible uname for the coworking space key."""
        uid: int = self.session.query(Coworking).order_by(Coworking.id.desc()).first().uid
        return self.session.query(User).filter(User.uid == uid).first().uname

    def coworking_status_set_uid_responsible(self, uid: int) -> bool:
        """Set the responsible uid for the coworking space key."""
        coworking_status = (self.session.query(Coworking)
                            .order_by(Coworking.id.desc())
                            .first())
        if coworking_status is None:
            raise AttributeError("Current coworking status not found")
        status: CoworkingStatus = coworking_status.status
        # Create new entry
        self.session.add(Coworking(status=status,
                                   uid=uid,
                                   time=datetime.utcnow()))
        self.session.commit()
        return True

    def trim_coworking_status_log(self, limit: int = 10):
        """Trim the coworking log to the specified limit, \
           starting from the oldest entry."""
        log = self.get_coworking_log()
        if len(log) > limit:
            for i in range(len(log) - limit):
                self.session.delete(log[i])
            self.session.commit()
    # endregion

    # region Trusted users
    def is_coworking_user_trusted(self, uid: int) -> bool:
        """Check if a user is trusted."""
        admin: bool = self.is_admin(uid)
        trusted: bool = (self.session.query(CoworkingTrustedUser)
                         .filter(CoworkingTrustedUser.uid == uid)
                         .first()) is not None
        return admin or trusted

    def coworking_trusted_user_add(self, uid: int, admin_uid: int) -> bool:
        """
        Add a user to trusted coworking users table (CoworkingTrustedUsers)

        Return False if the user is already trusted, else True.
        """
        if (self.session.query(CoworkingTrustedUser)
                .filter(CoworkingTrustedUser.uid == uid)
                .first()) is not None:
            return False
        self.session.add(CoworkingTrustedUser(uid=uid, admin_uid=admin_uid))
        self.session.commit()
        return True

    def coworking_trusted_user_del(self, uid: int) -> None:
        """Remove a user from trusted \
           coworking users table (CoworkingTrustedUsers)."""
        if (self.session.query(CoworkingTrustedUser)
                .filter(CoworkingTrustedUser.uid == uid)
                .first()) is None:
            return
        (self.session.query(CoworkingTrustedUser)
         .filter(CoworkingTrustedUser.uid == uid)
         .delete())
        self.session.commit()

    def coworking_trusted_user_get_admin_uid(self, uid: int) -> int:
        """Get admin_id of a trusted user."""
        user = (self.session.query(CoworkingTrustedUser)
                .filter(CoworkingTrustedUser.uid == uid)
                .first())
        if user is None:
            raise AttributeError("User not found")
        return user.admin_uid
    # endregion

    # region Coworking notifications
    def change_coworking_notifications(self, cid: int, notify: bool) -> None:
        """Change coworking notifications boolean value for a chat id (cid)."""
        # Check if the chat id is already in the database
        if self.session.query(ChatSettings).filter(ChatSettings.cid == cid).first() is None:
            # If not, add it
            self.session.add(ChatSettings(cid=cid, notifications_enabled=notify))
            return
        self.session.query(ChatSettings).filter(ChatSettings.cid == cid).update({"notifications_enabled": notify})
        self.session.commit()

    def toggle_coworking_notifications(self, cid: int) -> bool:
        """Toggle coworking notifications for a chat id (cid)."""
        notify = not self.get_coworking_notifications(cid)
        self.change_coworking_notifications(cid, notify)
        return notify

    def get_coworking_notifications(self, cid: int) -> bool:
        """Get coworking notifications boolean value for a chat id (cid)."""
        try:
            user = (self.session.query(ChatSettings)
                    .filter(ChatSettings.cid == cid)
                    .first())
            if user is None:
                raise AttributeError("Chat not found")
            status = user.notifications_enabled
        except AttributeError:
            status = False
        return status

    def get_coworking_notification_chats(self) -> List[int]:
        """Get a dict of all chats (present in ChatSettings table) that have notifications enabled."""
        return [c.cid for c in (self.session.query(ChatSettings)
                                .filter(ChatSettings.notifications_enabled)
                                .all())]

    def get_coworking_notification_chats_str(self) -> str:
        """Get a structured string containing all chats that have notifications enabled."""
        return "\n".join([f"{i+1}. {c}" for i, c in enumerate(self.get_coworking_notification_chats())])

    def get_coworking_notification_enabled_count(self) -> int:
        """Get the number of chats with coworking notifications enabled."""
        return self.session.query(ChatSettings).filter(ChatSettings.notifications_enabled).count()

    # region Admin coworking notifications
    def coworking_notified_admin_closed_during_hours_today(self) -> bool:
        """Check if admins have been notified about the coworking space being closed during hours today."""
        closed_status_id = None
        offset = 0
        while not closed_status_id:
            status_id = (self.session.query(AdminCoworkingNotification)
                         .order_by(AdminCoworkingNotification.id.desc())
                         .offset(offset).first())
            if status_id is not None:
                status_id = status_id.status_id
            else:
                return False
            last_event = (self.session.query(Coworking)
                          .filter(Coworking.id == status_id)
                          .first())
            if last_event is None:
                raise AttributeError("Event not found")
            if last_event.status == CoworkingStatus.open:
                closed_status_id = status_id
            offset += 1
        event = self.session.query(Coworking).filter(Coworking.id == closed_status_id).first()
        if event is None:
            raise AttributeError("Event not found")
        # Check if the event status is CoworkingStatus.closed
        if event.status not in CoworkingStatus.closed:
            return False
        # Check if the event happened today (from 00:00 to 23:59)
        if event.time.date() == datetime.utcnow().date():
            return True
        return False

    def coworking_notified_admin_open_after_hours_today(self) -> bool:
        """Check if admins have been notified about the coworking space being open after hours today."""
        open_status_id = None
        offset = 0
        while not open_status_id:
            status_id = (self.session.query(AdminCoworkingNotification)
                         .order_by(AdminCoworkingNotification.id.desc())
                         .offset(offset)
                         .first())
            if status_id is not None:
                status_id = status_id.status_id
            else:
                return False
            if (self.session.query(Coworking)
                    .filter(Coworking.id == status_id)
                    .first()
                    .status) == CoworkingStatus.open:
                open_status_id = status_id
            offset += 1
        event = self.session.query(Coworking).filter(Coworking.id == open_status_id).first()
        if event is None:
            raise AttributeError("Event not found")
        # Check if the event status is CoworkingStatus.open
        if event.status not in [CoworkingStatus.open, CoworkingStatus.event_open]:
            return False
        # Check if the event happened today (from 00:00 to 23:59)
        if event.time.date() == datetime.utcnow().date():
            return True
        return False

    def coworking_opened_today(self) -> bool:
        """Check if the coworking space has been opened today"""
        try:
            return (self.session.query(Coworking)
                    .filter(Coworking.time.date() == datetime.utcnow().date())
                    .filter(Coworking.status == CoworkingStatus.open)
                    .first()) is not None
        except Exception as exc:
            self.log.error(f"Error while checking if coworking space \
has been opened today: {exc}")
            return False  # TODO: Raise exception?
    # endregion
    # endregion

    # region Answer plaintext user messages
    def change_message_answers_status(self, cid: int, enabled: bool) -> None:
        """Enable answers to user messages for a chat id (cid)"""
        # Check if the chat id is already in the database
        if self.session.query(ChatSettings).filter(ChatSettings.cid == cid).first() is None:
            self.session.add(ChatSettings(cid=cid, plaintext_answers_enabled=enabled))
            self.session.commit()
            return
        # If it is, update the value
        self.session.query(ChatSettings).filter(ChatSettings.cid == cid).update({"plaintext_answers_enabled": enabled})
        self.session.commit()

    def set_message_answers_status(self, cid: int) -> None:
        self.change_message_answers_status(cid, True)

    def unset_message_answers_status(self, cid: int) -> None:
        self.change_message_answers_status(cid, False)

    def get_message_answers_status(self, cid: int) -> bool:
        # Check if the chat id is already in the database
        if self.session.query(ChatSettings).filter(ChatSettings.cid == cid).first() is None:
            self.session.add(ChatSettings(cid=cid))
            self.session.commit()
        return self.session.query(ChatSettings).filter(ChatSettings.cid == cid).first().plaintext_answers_enabled

    def toggle_message_answers_status(self, cid: int) -> bool:
        if self.get_message_answers_status(cid):
            self.change_message_answers_status(cid, False)
            return False
        else:
            self.change_message_answers_status(cid, True)
            return True
    # endregion

    # region Privilege management
    def get_user_chats(self) -> List[int]:
        """Get a list of all uids with GroupType user."""
        return [i.uid for i in self.session.query(User).filter(User.gid == GroupType.users).all()]

    def get_admin_chats(self) -> List[int]:
        """Get a list of all uids with GroupType admin."""
        return [i.uid for i in self.session.query(User).filter(User.gid == GroupType.admins).all()]

    def get_all_chats(self) -> List[int]:
        """Get a list of all uids"""
        return [i.uid for i in self.session.query(User).all()]

    @staticmethod
    def get_superadmin_uids() -> list[int]:
        """Get a list of all super admins."""
        return [int(i) for i in getenv("SUPERADMIN_UIDS", "").split(":")]

    def is_superadmin(self, uid: int) -> bool:
        """Check if a user is a super admin."""
        return uid in self.get_superadmin_uids()
    # endregion
