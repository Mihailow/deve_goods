from aiogram import types
from aiogram.types import InlineKeyboardMarkup

import misc
from postgres.commands_to_db import get_language
from translations import _


async def get_settingsBot_keyboards(callback_query) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    if misc.bot_enabled:
        markup.add(types.InlineKeyboardButton(_('Включен', await get_language(callback_query.message.chat.id)),
                                              callback_data='ChangeEnabledBot disable'))
    else:
        markup.add(types.InlineKeyboardButton(_('Выключен', await get_language(callback_query.message.chat.id)),
                                              callback_data='ChangeEnabledBot enable'))
    if misc.order_notification:
        markup.add(types.InlineKeyboardButton(_('Уведомление о сделках [вкл]',
                                                await get_language(callback_query.message.chat.id)),
                                              callback_data='ChangeOrderNotificationBot disable'))
    else:
        markup.add(types.InlineKeyboardButton(_("Уведомление о сделках [выкл]",
                                                await get_language(callback_query.message.chat.id)),
                                              callback_data='ChangeOrderNotificationBot enable'))
    if misc.user_notification:
        markup.add(types.InlineKeyboardButton(_("Уведомление о пользователях [вкл]",
                                                await get_language(callback_query.message.chat.id)),
                                              callback_data='ChangeUserNotificationBot disable'))
    else:
        markup.add(types.InlineKeyboardButton(_("Уведомление о пользователях [выкл]",
                                                await get_language(callback_query.message.chat.id)),
                                              callback_data='ChangeUserNotificationBot enable'))
    markup.add(types.InlineKeyboardButton(_("Назад", await get_language(callback_query.message.chat.id)),
                                          callback_data='backToAdminMenu'))
    return markup
