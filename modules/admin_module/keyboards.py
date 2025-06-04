from aiogram import types
from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup

from postgres.commands_to_db import get_language
from translations import _


async def get_admin_keyboards_for_message_handler(user_id) -> InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton(_('Настройки бота', await get_language(user_id)),
                                          callback_data='SettingsBot'))
    markup.row(types.InlineKeyboardButton(_('Управление пользователями', await get_language(user_id)),
                                          callback_data='UserManagement'))
    markup.row(types.InlineKeyboardButton(_('Редактирование товаров', await get_language(user_id)),
                                          callback_data='electProductSearchMethod'))
    markup.row(types.InlineKeyboardButton(_('Управление рассылками', await get_language(user_id)),
                                          callback_data='mailing_button'))
    markup.row(types.InlineKeyboardButton(_('Поиск заказа', await get_language(user_id)),
                                          callback_data=f'AdminFindOrder'))
    return markup

async def get_admin_keyboards_for_callback_query_handler(callback) -> InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton(_('Настройки бота', await get_language(callback.message.chat.id)),
                                          callback_data='SettingsBot'))
    markup.row(types.InlineKeyboardButton(_('Управление пользователями', await get_language(callback.message.chat.id)),
                                          callback_data='UserManagement'))
    markup.row(types.InlineKeyboardButton(_('Редактирование товаров', await get_language(callback.message.chat.id)),
                                          callback_data=f'electProductSearchMethod'))
    markup.row(types.InlineKeyboardButton(_('Управление рассылками', await get_language(callback.message.chat.id)),
                                          callback_data=f'mailing_button'))
    markup.row(types.InlineKeyboardButton(_('Поиск заказа', await get_language(callback.message.chat.id)),
                                          callback_data=f'AdminFindOrder'))
    return markup

