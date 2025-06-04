from postgres.commands_to_db import get_language
from translations import _


async def generate_admin_view_user_profile_template(user, message):
    id = user['id']
    if user['nickname'] != None:
        nickname = user['nickname']
    else:
        nickname = _("Не существует", await get_language(message.from_user.id))
    if user['first_name'] != None:
        first_name = user['first_name']
    else:
        first_name = _("Не существует", await get_language(message.from_user.id))
    if user['last_name'] != None:
        last_name = user['last_name']
    else:
        last_name = _("Не существует", await get_language(message.from_user.id))
    if user['user_id'] != None:
        user_id = user['user_id']
    else:
        user_id = _("Не существует", await get_language(message.from_user.id))
    balance = user['balance']
    date_registration = user['date_registration']
    date_format = "%d %B %Y %H:%M"
    formatted_datetime = date_registration.strftime(date_format)
    return f"""
<b>{_("Имя", await get_language(message.from_user.id))}:</b> {first_name}
<b>{_("Фамилия", await get_language(message.from_user.id))}:</b> {last_name}
<b>{_("Ник", await get_language(message.from_user.id))}:</b> {nickname}
<b>ID:</b> {user_id}
<b>TELEGRAM_ID:</b> {id}
<b>{_("Текущий баланс", await get_language(message.from_user.id))}:</b> {balance}
<b>{_("Дата регистрации", await get_language(message.from_user.id))}:</b> {formatted_datetime}
"""