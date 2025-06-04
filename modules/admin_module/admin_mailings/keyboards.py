from aiogram import types
from aiogram.types import InlineKeyboardMarkup
from translations import _

async def get_main_mailings_keyboards(call) -> InlineKeyboardMarkup:
    buttons = [
        types.InlineKeyboardButton(text=_('Изменить', call.from_user.language_code), callback_data='change_mailing'),
        types.InlineKeyboardButton(text=_('Запустить', call.from_user.language_code), callback_data='run_mailing'),
        # types.InlineKeyboardButton(text="Запустить с задержкой", callback_data='delay_run_mailing'),
        types.InlineKeyboardButton(text=_('Получить тестовое сообщение', call.from_user.language_code),
                                   callback_data='get_test_mailing'),
        types.InlineKeyboardButton(text=_('Удалить', call.from_user.language_code), callback_data='delete_mailing'),
        types.InlineKeyboardButton(text=f"◀ {_('Назад', call.from_user.language_code)}", callback_data='mailing_button')
    ]
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(*buttons)
    return keyboard
