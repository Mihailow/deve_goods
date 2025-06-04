from aiogram import types
from aiogram.types import InlineKeyboardMarkup

from postgres.commands_to_db import get_language
from translations import _


async def get_main_basket_keyboard(sum, currency) -> InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton(f"Оформить заказ ({sum} {currency})",callback_data='confirm_basket'))
    markup.row(types.InlineKeyboardButton(f"Очистить корзину",callback_data='clean_basket'),
               types.InlineKeyboardButton(f"Редактировать корзину",callback_data='edit_basket'))
    markup.row(types.InlineKeyboardButton(f"Посмотреть каталог", callback_data='BackToAllCategories'))
    return markup