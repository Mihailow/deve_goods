from aiogram import types
from aiogram.types import InlineKeyboardMarkup

from postgres.commands_to_db import get_language
from translations import _


async def get_user_management_keyboards(callback_query) -> InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton(_("Поиск пользователя по ID", await get_language(callback_query.message.chat.id)),
                                   callback_data="FindUserByID"))
    markup.row(types.InlineKeyboardButton(
        _("Поиск пользователя по TELEGRAM_ID", await get_language(callback_query.message.chat.id)),
        callback_data="FindUserByTELEGRAM_ID"))
    markup.row(types.InlineKeyboardButton(
        _("Поиск пользователя по USERNAME", await get_language(callback_query.message.chat.id)),
        callback_data="FindUserByUSERNAME"))
    markup.row(types.InlineKeyboardButton(_("Отмена", await get_language(callback_query.message.chat.id)),
                                          callback_data="backToAdminMenu"))
    return markup



