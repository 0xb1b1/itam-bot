#!/usr/bin/env python3
# region Local dependencies
from modules import btntext as btn
from modules.models import CoworkingStatus
# endregion

def pong():
    return "Pong!"

def welcome_message(uname) -> str:
    return f"""Привет, {uname}!

Я — Telegram-бот ITAM. Помогу тебе узнать статус коворкинга, получать обновления от твоих любимых клубов и искать команды на хаки.

Поехали!"""

def permission_denied() -> str:
    return "❌ У вас недостаточно прав для выполнения этой команды"

def profile_fields() -> dict:
    return {
        "first_name": "Имя",
        "last_name": "Фамилия",
        "gname": "Группа",
        "birthday": "День рождения",
        "phone": "Телефон",
        "email": "Почта",
        "bio": "Био",
        "resume": "Резюме"
    }

def profile_info(info) -> str:
    fields = profile_fields()
    return f"""🛂 Информация о пользователе

{fields['first_name']}: {info['first_name']}
{fields['last_name']}: {is_set(info['last_name'])}
{fields['gname']}: {info['gname']}
{fields['birthday']}: {is_set(info['birthday'])}
{fields['phone']}: {is_set(info['phone'])}
{fields['email']}: {is_set(info['email'])}
{fields['bio']}: /bio
{fields['resume']}: /resume"""

def profile_edit_first_name(first_name: str, last_name: str) -> str:
    return f"""🛂 Изменение имени

Текущее имя: {first_name}
Фамилия: {last_name}

Отправьте новое имя"""

def profile_edit_last_name(first_name: str, last_name: str) -> str:
    return f"""🛂 Изменение имени

Имя: {first_name}
Текущая фамилия: {last_name}

Отправьте новую фамилию"""

def profile_edit_success() -> str:
    return "✅ Информация обновлена"

def is_set(data) -> str:
    return data if data else btn.NOT_SET

def coworking_notifications_on() -> str:
    return "🔔🟢 Уведомления о статусе коворкинга включены"

def coworking_notifications_off() -> str:
    return "🔔🔴 Уведомления о статусе коворкинга выключены"

def get_coworking_status_reply_data(status: CoworkingStatus, responsible_uname: str = None, delta_mins: int = 0, responsible_account: bool = True, one_newline: bool = False) -> tuple:
    """Return reply data for coworking status"""
    newline = "\n" if one_newline else "\n\n"
    postfix_msg =  f"{newline}Ответственный: @{responsible_uname}" if responsible_account else ""
    if delta_mins > 0 and delta_mins is not None:
        postfix_msg = f" (на {delta_mins} минут)!" + postfix_msg
    if status == CoworkingStatus.open:
        status_icon = "🟢"
        status_str = f"открыт{postfix_msg}"
    elif status == CoworkingStatus.event_open:
        status_icon = "🟡"
        status_str = f"открыт (проходит мероприятие!){postfix_msg}"
    elif status == CoworkingStatus.temp_closed:
        status_icon = "🟠"
        status_str = f"временно закрыт{postfix_msg}"  # User without `@`
    elif status == CoworkingStatus.closed:
        status_icon = "🔴"
        status_str = f"закрыт{postfix_msg}"
    else:
        status_icon = "❓"
        status_str = "[статус неизвестен]"
    return status_icon, status_str

def coworking_status_reply(status: CoworkingStatus, responsible_uname: str = "(не назначен)", delta_mins: int = 0) -> str:
    """Return coworking status reply string"""
    status_icon, status_str = get_coworking_status_reply_data(status, responsible_uname=responsible_uname, delta_mins=delta_mins)
    return f"🔑{status_icon} Коворкинг ITAM (Г-511) {status_str}"

def switch_coworking_status_inline_binary_action(status: CoworkingStatus) -> str:
    """Return coworking status inline action (to do) string [open/close]"""
    status_icon, status_str = get_coworking_status_reply_data(status, responsible_account=False)
    status_inl = status_str + " " + status_icon
    if status in [CoworkingStatus.open, CoworkingStatus.event_open]:
        action_inl = "Закрыть"
    elif status in [CoworkingStatus.temp_closed, CoworkingStatus.closed]:
        action_inl = "Открыть"
    return f"{action_inl} коворкинг (сейчас {status_inl})"

def switch_coworking_from_nonbinary_action(status: CoworkingStatus, to_open: bool) -> str:
    """Accepts only CoworkingStatus.temp_closed or CoworkingStatus.event_open"""
    if status not in [CoworkingStatus.temp_closed, CoworkingStatus.event_open]:
        raise ValueError("Invalid status")
    status_icon, status_str = get_coworking_status_reply_data(status, responsible_account=False)
    status_inl = status_str + " " + status_icon
    return f"{'Открыть' if to_open else 'Закрыть'} коворкинг (сейчас {status_inl})"

def coworking_status_changed(status: CoworkingStatus, responsible_uname: str = "(не назначен)",delta_mins: int = 0) -> str:
    status_icon, status_str = get_coworking_status_reply_data(status, responsible_uname=responsible_uname, delta_mins=delta_mins)
    return f"🔑{status_icon} Коворкинг ITAM (Г-511) {status_str}"

def coworking_status_not_binary() -> str:
    return "❌ Невозможно выполнить действие: коворкинг не в открытом или закрытом состоянии"

def plaintext_answers_reply(status: bool, toggled: bool = False, chat_id: int = None, admin_uname: str = None) -> str:
    return f"Ответы на обычные сообщения{' теперь' if toggled else ''} {'включены 🟢' if status else 'выключены 🔴'}{f' для чата {str(chat_id)}' if chat_id else ''}{f' администратором @{admin_uname}' if admin_uname else ''}"

def menu_updated_reply(user_count: int, admins_only: bool = False) -> str:
    return f"Меню обновлено для {user_count} {'пользователей' if not admins_only else 'администраторов'}"

def profile_info_only_in_pm() -> str:
    return "🛂‼️ Эту команду можно использовать только в личных сообщениях"

def coworking_status_only_in_pm() -> str:
    return "🔑‼️ Эту команду можно использовать только в личных сообщениях"

def please_click_start() -> str:
    return "🛂‼️ Пожалуйста, нажмите сюда: /start"

def help_message() -> str:
    return """Список команд:

/notify — 🔔 включить/выключить уведомления о статусе коворкинга

[Сайт проекта](https://go.itatmisis.ru)"""

def cancel_action() -> str:
    return "/cancel — ❌ Отменить действие"

def admin_panel(is_coworking_open: bool) -> str:
    return f"""🛂 Панель администратора

兀 Команды

🧑‍💻 Администрация
— /admin — 🛂 Показать эту панель
— /stats — 📊 Показать статистику

💃 Пользователи
— /get_users — 📋 Получить список пользователей
— /get_users_verbose — 📋📝 Получить список пользователей с подробной информацией
— /get_notif_db — 📋🔔 Получить список пользователей и их настройки уведомлений

🦊 Разное
— /broadcast — 📢 Создать рассылку
— /cancel — ❌ Отменить любой flow"""

def stats(stats: dict) -> str:
    """Display statistics for admins"""
    cw_icon, cw_status = get_coworking_status_reply_data(stats["coworking_status"], responsible_account=False)
    cw_status = f"{cw_icon} {cw_status}"
    return f"""📊 Статистика

💃 Пользователей: {stats['users']}
🧑‍💻 Администраторов: {stats['admins']}
🔑 Статус коворкинга: {cw_status}
💫 Изменений статуса коворкинга: {stats['coworking_log_count']}
🔔 Пользователей с включенными уведомлениями: {stats['coworking_notifications']}"""

def coworking_control(cw_status, responsible_uname) -> str:
    cw_icon, cw_status = get_coworking_status_reply_data(cw_status, responsible_uname=responsible_uname, one_newline=True)
    return f"""🔑 Управление коворкингом

Сейчас коворкинг {cw_icon} {cw_status}

🔑 Команды (⚠️ Без подтверждения)
— /coworking_toggle — 🟢🔴 Переключить статус коворкинга)
— /coworking_open — 🟢 Открыть коворкинг
— /coworking_close — 🔴 Закрыть коворкинг
— /coworking_temp_close — 🔴⚠️ Временно закрыть коворкинг
— /coworking_event_open — 🟢⚠️ Открыть коворкинг на мероприятие
— /trim_coworking_status_log — 🧹 Обрезать лог статусов коворкинга"""

def club_info_general() -> str:
    return """👩‍🎨🥷🎮💸🧑‍💻
Информация о клубах"""

def ctf_club_info() -> str:
    return """🥷🧑‍💻 CTF Club

CTF клуб занимается изучением программного обеспечения для дальшего поиска уязвимостей и обеспечения информационной безопасности.

CTF (Capture the Flag/Захват Флага) — командные совернования в области компьютерной (информационной) безопасности. Разностороннее развитие в IT, компетентность и глубокий уровень познаний — все это получают ученики CTF клуба.

Члены CTF клуба принимают участие в регулярных внутренних соревнованиях, которые помогают отточить навыки для дальнейшего участия в городских, федеральных и международных конкурсах.

📌 Контакты

[⚡️ Руководитель](https://t.me/oxb1b1)
[💬 Чат](https://t.me/+lgw8dT2HFuRhZmFi)
[📣 Канал](https://t.me/misis_ctf)
"""

def hackathon_club_info() -> str:
    return """💸🧑‍💻 Hackathon Club

Участники клуба активно принимают участие в хакатонах.
Командам предоставляется экспертная поддержка, технической инфраструктурой.

📌 Контакты

[⚡️ Руководитель](https://t.me/Daniil_Y)
[💬 Чат](https://t.me/+WQeYWDOPnvs5yhhY)
"""

def gamedev_club_info() -> str:
    return """🎮🧑‍💻 GameDev Club

В клубе игровых разработчиков студенты совместно изучают особенности игровой индустрии,
учаться работать с различными технологиями для разработки игр и участвуют в соревнованиях игровых разработчиков GameJam.

📌 Контакты

[⚡️ Руководитель](https://t.me/kerliaa)
[💬 Чат](https://t.me/+MH0JVkTEsmozYzRi)
"""

def design_club_info() -> str:
    return """👩‍🎨🧑‍💻 Design at MISIS Now

DAMN — это не просто клуб, это школа и дизайн-студия, в которой каждый студент может получить теоретические и практические навыки.
Участники движения хакатонят и разрабатывают коммерческие продукты.

📌 Контакты

[⚡️ Руководитель](https://t.me/a_asyotr)
[💬 Чат](https://t.me/+zTBGzdqNc4xlZWUy)
"""

def robotics_club_info() -> str:
    return """🤖🧑‍💻 Robotics Club

Клуб робототехников, работающих с передовыми технологиями
в сфере проектирования и программирования роботов.

📌 Контакты

(Crickets' chirp)
"""

def ml_club_info() -> str:
    return """🤖🧑‍💻 MISIS AI Lab

Прогрессивное молодое сообщество студентов, где исследуют и создают модели нейросетей, обсуждают вопросы машинного обучения, обмениваются интересными наборами данных и организуют свои kaggle-like соревнования.

[⚡️ Руководитель](https://t.me/arsmathprog)
[💬 Чат](https://t.me/+vEZLTQ9wWT44OTRi)"""

def coworking_closed_during_hours() -> str:
    return """🚧 Коворкинг закрыт в рабочее время!"""

def coworking_open_after_hours() -> str:
    return """🚧 Коворкинг открыт в нерабочее время!"""

def coworking_status_already_responsible() -> str:
    return """🔑🚧🔴 Ты уже отвечаешь за коворкинг!"""

def coworking_status_now_responsible() -> str:
    return """🔑🚧🟢 Теперь ты отвечаешь за коворкинг!"""

def credits() -> str:
    return """🤖 Бот разработан в **ITAM**
[💙 Telegram](https://t.me/itatmisis)
[🚾 VK](https://vk.com/itatmisis)

📌 Контакты разработчиков
Аксель @oxb1b1"""

def user_group_changed() -> str:
    return """👥 Группа пользователя изменена"""

def broadcast_successful() -> str:
    return """📢 Рассылка успешна"""

def toggle_coworking_notifications(curr_status: bool) -> str:
    return f"[{'🟢' if curr_status else '🔴'}] {'Выключить' if curr_status else 'Включить'} уведомления"
