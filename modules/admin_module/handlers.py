from misc import *
from modules.admin_module.generate_template import generate_admin_menu_template
from modules.admin_module.keyboards import get_admin_keyboards_for_message_handler, \
    get_admin_keyboards_for_callback_query_handler
from postgres.commands_to_db import get_language

from aiogram.dispatcher import FSMContext
from main import bot, dp
from translations import _
from aiogram import types

@dp.message_handler(commands=['admin'])
async def admin_main(message: types.Message):
    if message.from_user.id not in admins_users:
        await message.answer(_('К сожалению, вы не являетесь администратором', await get_language(message.from_user.id)))
        return

    markup = await get_admin_keyboards_for_message_handler(message.from_user.id)
    await message.answer(await generate_admin_menu_template(message), parse_mode="HTML", reply_markup=markup)

@dp.callback_query_handler(lambda callback: 'backToAdminMenu' in callback.data)
async def backToAdminMenu(callback):
    await callback.answer("")
    await bot.delete_message(callback.message.chat.id, callback.message.message_id)
    markup = await get_admin_keyboards_for_callback_query_handler(callback)

    await bot.send_message(callback.message.chat.id, await generate_admin_menu_template(callback), parse_mode="HTML",
                           reply_markup=markup)