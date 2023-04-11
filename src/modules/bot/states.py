from aiogram.dispatcher.filters.state import State, StatesGroup


class AdminChangeUserGroup(StatesGroup):
    user_id = State()
    group_id = State()


class AdminBroadcast(StatesGroup):
    msg_type = State()
    message = State()
    media = State()
    scope = State()
    confirm = State()


class AdminCoworkingTempCloseFlow(StatesGroup):
    delta = State()
    notification = State()
    confirm = State()


class AdminGetObjectId(StatesGroup):
    get = State()


class UserEditProfile(StatesGroup):
    first_name = State()
    last_name = State()
    birthday = State()
    email = State()
    phone = State()
    skills = State()


class UserProfileSetup(StatesGroup):
    first_name = State()
    last_name = State()
    birthday = State()
    email = State()
    phone = State()


# Bot Skills
class YandexInternship(StatesGroup):
    first_name = State()
    last_name = State()
    phone = State()
    email = State()
    skills = State()
    listing_await = State()
