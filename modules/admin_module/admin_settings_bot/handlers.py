from aiogram.dispatcher import FSMContext

import misc
from main import bot, dp
from modules.admin_module.admin_settings_bot.commands_to_db import update_settings
from modules.admin_module.admin_settings_bot.keyboards import get_settingsBot_keyboards
from postgres.commands_to_db import get_language
from translations import _
from aiogram import types


@dp.callback_query_handler(lambda callback: 'SettingsBot' in callback.data)
async def settingsBot(callback_query: types.CallbackQuery):

    await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    markup = await get_settingsBot_keyboards(callback_query)
    await bot.send_message(callback_query.message.chat.id, f"{_('Настройки', await get_language(callback_query.message.chat.id))}:",
                           reply_markup=markup, parse_mode="HTML")

@dp.callback_query_handler(lambda callback: 'ChangeUserNotificationBot' in callback.data)
async def ChangeUserNotificationBot(callback_query: types.CallbackQuery):
    print(callback_query.data)
    await callback_query.answer("")
    data = callback_query.data.split(' ')
    action = data[1]
    if action == 'enable':
        misc.user_notification = True
        update_settings('notif_new_user', True)
    else:
        misc.user_notification = False
        update_settings('notif_new_user', False)
    await settingsBot(callback_query)


@dp.callback_query_handler(lambda callback: 'ChangeOrderNotificationBot' in callback.data)
async def ChangeOrderNotificationBot(callback_query: types.CallbackQuery):
    print(callback_query.data)
    await callback_query.answer("")
    data = callback_query.data.split(' ')
    action = data[1]
    if action == 'enable':
        misc.order_notification = True
        update_settings('notif_new_order', True)
    else:
        misc.order_notification = False
        update_settings('notif_new_order', False)
    await settingsBot(callback_query)

@dp.callback_query_handler(lambda callback: 'ChangeEnabledBot' in callback.data)
async def ChangeEnabledBot(callback_query: types.CallbackQuery):
    await callback_query.answer("")
    data = callback_query.data.split(' ')
    action = data[1]
    if action == 'enable':
        misc.bot_enabled = True
        update_settings('status', True)
    else:
        misc.bot_enabled = False
        update_settings('status', False)
    await settingsBot(callback_query)