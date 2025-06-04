from aiogram.dispatcher import FSMContext

import misc
from main import bot, dp
from modules.admin_module.admin_user_management.commands_to_db import find_user_in_db
from modules.admin_module.admin_user_management.generate_template import generate_admin_view_user_profile_template
from postgres.commands_to_db import get_language
from states import MyStates
from translations import _
from aiogram import types

@dp.callback_query_handler(lambda callback: "UserManagement" in callback.data)
async def UserManagement(callback_query: types.CallbackQuery):
    await callback_query.answer("")
    await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton(_("Поиск пользователя по ID", await get_language(callback_query.message.chat.id)),
                                          callback_data="FindUserByID"))
    markup.row(types.InlineKeyboardButton(_("Поиск пользователя по TELEGRAM_ID", await get_language(callback_query.message.chat.id)),
                                          callback_data="FindUserByTELEGRAM_ID"))
    markup.row(types.InlineKeyboardButton(_("Поиск пользователя по USERNAME", await get_language(callback_query.message.chat.id)),
                                          callback_data="FindUserByUSERNAME"))
    markup.row(types.InlineKeyboardButton(_("Отмена", await get_language(callback_query.message.chat.id)),
                                          callback_data="backToAdminMenu"))
    await callback_query.message.answer(_("Управление пользователями", await get_language(callback_query.message.chat.id)),
                                        parse_mode="HTML", reply_markup=markup)


@dp.callback_query_handler(lambda callback: "FindUserByID" in callback.data)
async def FindUserByID(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer("")
    await state.set_state(MyStates.find_user_by_ID_state.state)
    await bot.send_message(callback_query.message.chat.id,_("Введите ID пользователя:",
                                                            await get_language(callback_query.message.chat.id)), parse_mode="HTML")


@dp.message_handler(state=MyStates.find_user_by_ID_state)
async def FindUserByIDState(message, state: FSMContext):
    text = message.text
    user_data = await find_user_in_db("user_id", text)
    if user_data is None:
        await bot.send_message(message.chat.id, _("Пользователь с указанным ID не найден",
                                                  await get_language(message.from_user.id)), parse_mode="HTML")
    else:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(_("Посмотреть заказы", await get_language(message.from_user.id)),
                                              callback_data=f"AdminWatchOrdHist {user_data['id']}"))
        markup.add(
            types.InlineKeyboardButton(_("Отправить сообщение",
                                         await get_language(message.from_user.id)),
                                       callback_data=f"SendMessageUserFromAdmin {user_data['id']}"))
        if user_data["status"] != "blocked":
            markup.add(types.InlineKeyboardButton(_("Заблокировать",
                                                    await get_language(message.from_user.id)),
                                                  callback_data=f"BanUser ban {user_data['id']}"))
        else:
            markup.add(types.InlineKeyboardButton(_("Разблокировать", await get_language(message.from_user.id)),
                                                  callback_data=f"BanUser unban {user_data['id']}"))
        markup.add(types.InlineKeyboardButton(_("Отмена", await get_language(message.from_user.id)),
                                              callback_data="backToAdminMenu"))

        await bot.send_message(message.chat.id, await generate_admin_view_user_profile_template(user_data, message),
                               parse_mode="HTML", reply_markup=markup)
    await state.reset_state()


@dp.callback_query_handler(lambda callback: "FindUserByTELEGRAM_ID" in callback.data)
async def FindUserByTELEGRAM_ID(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer("")
    await state.set_state(MyStates.find_user_by_TELEGRAM_ID_state.state)
    await bot.send_message(callback_query.message.chat.id, _("Введите TELEGRAM_ID пользователя:",
                                                             await get_language(callback_query.message.chat.id)), parse_mode="HTML")


@dp.message_handler(state=MyStates.find_user_by_TELEGRAM_ID_state)
async def FindUserByTELEGRAM_IDState(message, state: FSMContext):
    text = message.text
    user_data = await find_user_in_db("id", text)
    if user_data is None:
        await bot.send_message(message.chat.id, _("Пользователь с указанным TELEGRAM_ID не найден",
                                                  await get_language(message.from_user.id)), parse_mode="HTML")
    else:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(_("Посмотреть заказы", await get_language(message.from_user.id)),
                                              callback_data=f"AdminWatchOrdHist {user_data['id']}"))
        markup.add(
            types.InlineKeyboardButton(_("Отправить сообщение", await get_language(message.from_user.id)),
                                       callback_data=f"SendMessageUserFromAdmin {user_data['id']}"))
        if user_data["status"] != "blocked":
            markup.add(types.InlineKeyboardButton(_("Заблокировать", await get_language(message.from_user.id)),
                                                  callback_data=f"BanUser ban {user_data['id']}"))
        else:
            markup.add(types.InlineKeyboardButton(_("Разблокировать", await get_language(message.from_user.id)),
                                                  callback_data=f"BanUser unban {user_data['id']}"))
        markup.add(types.InlineKeyboardButton(_("Отмена", await get_language(message.from_user.id)),
                                              callback_data="backToAdminMenu"))

        await bot.send_message(message.chat.id, await generate_admin_view_user_profile_template(user_data,message),
                               parse_mode="HTML", reply_markup=markup)
    await state.reset_state()


@dp.callback_query_handler(lambda callback: "FindUserByUSERNAME" in callback.data)
async def FindUserByUSERNAME(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer("")
    await state.set_state(MyStates.find_user_by_USERNAME_state.state)
    await bot.send_message(callback_query.message.chat.id, _("Введите USERNAME пользователя",
                                                             await get_language(callback_query.message.chat.id)), parse_mode="HTML")

@dp.message_handler(state=MyStates.find_user_by_USERNAME_state)
async def FindUserByUSERNAMEState(message, state: FSMContext):
    text = message.text
    user_data = await find_user_in_db("nickname", text)
    if user_data is None:
        await bot.send_message(message.chat.id, _("Пользователь с указанным USERNAME не найден",
                                                  await get_language(message.from_user.id)), parse_mode="HTML")
    else:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(_("Посмотреть заказы", await get_language(message.from_user.id)),
                                              callback_data=f"AdminWatchOrdHist {user_data['id']}"))
        markup.add(
            types.InlineKeyboardButton(_("Отправить сообщение", await get_language(message.from_user.id)),
                                       callback_data=f"SendMessageUserFromAdmin {user_data['id']}"))
        if user_data["status"] != "blocked":
            markup.add(types.InlineKeyboardButton(_("Заблокировать", await get_language(message.from_user.id)),
                                                  callback_data=f"BanUser ban {user_data['id']}"))
        else:
            markup.add(types.InlineKeyboardButton(_("Разблокировать",
                                                    await get_language(message.from_user.id)),
                                                  callback_data=f"BanUser unban {user_data['id']}"))
        markup.add(types.InlineKeyboardButton(_("Отмена", await get_language(message.from_user.id)), callback_data="backToAdminMenu"))

        await bot.send_message(message.chat.id, await generate_admin_view_user_profile_template(user_data, message),
                               parse_mode="HTML", reply_markup=markup)
    await state.reset_state()

@dp.message_handler(state=MyStates.send_message_from_admin_state)
async def SendMessageUserFromtate(message, state: FSMContext):
    data = await state.get_data()
    user_id = data["user_id"]
    try:
        await bot.send_message(user_id, message.text, parse_mode="HTML")
        await bot.send_message(message.chat.id, f"{_('Сообщение успешно отправлено', await get_language(message.from_user.id))} ✔️")
    except Exception as ex:
        await bot.send_message(message.chat.id, f"{_('Отправка сообщения не удалась', await get_language(message.from_user.id))} ❌")

    user_data = await find_user_in_db("id", user_id)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(_("Посмотреть заказы", await get_language(message.from_user.id)),
                                          callback_data=f"AdminWatchOrdHist {user_data['id']}"))
    markup.add(
        types.InlineKeyboardButton(_("Отправить сообщение", await get_language(message.from_user.id)),
                                   callback_data=f"SendMessageUserFromAdmin {user_data['id']}"))
    if user_data["status"] != "blocked":
        markup.add(types.InlineKeyboardButton(_("Заблокировать", await get_language(message.from_user.id)),
                                              callback_data=f"BanUser ban {user_data['id']}"))
    else:
        markup.add(types.InlineKeyboardButton(_("Разблокировать", await get_language(message.from_user.id)),
                                              callback_data=f"BanUser unban {user_data['id']}"))
    markup.add(types.InlineKeyboardButton(_("Отмена", await get_language(message.from_user.id)),
                                          callback_data="backToAdminMenu"))

    await bot.send_message(message.chat.id, await generate_admin_view_user_profile_template(user_data,message),
                           parse_mode="HTML", reply_markup=markup)

    await state.reset_state()

@dp.callback_query_handler(lambda callback: "BanUser" in callback.data)
async def BanUser(callback_query: types.CallbackQuery):
    await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    await callback_query.answer("")
    data = callback_query.data.split(" ")
    action = data[1]
    user_id = data[2]
    if action == "ban":
        await bot.send_message(user_id, _("Вы заблокированы", await get_language(callback_query.message.chat.id)))
        await bot.send_message(callback_query.message.chat.id, _("Пользователь был заблокирован",
                                                                 await get_language(callback_query.message.chat.id)))
        await misc.update_user_status(user_id, "blocked")
    else:
        await bot.send_message(callback_query.message.chat.id, _("Пользователь был разблокирован",
                                                                 await get_language(callback_query.message.chat.id)))
        await misc.update_user_status(user_id, "unverified")

    user_data = await find_user_in_db("id", user_id)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(_("Посмотреть заказы", await get_language(callback_query.message.chat.id)),
                                          callback_data=f"AdminWatchOrdHist {user_data['id']}"))
    markup.add(
        types.InlineKeyboardButton(_("Отправить сообщение", await get_language(callback_query.message.chat.id)),
                                   callback_data=f"SendMessageUserFromAdmin {user_data['id']}"))
    if user_data["status"] != "blocked":
        markup.add(types.InlineKeyboardButton(_("Заблокировать", await get_language(callback_query.message.chat.id)),
                                              callback_data=f"BanUser ban {user_data['id']}"))
    else:
        markup.add(types.InlineKeyboardButton(_("Разблокировать", await get_language(callback_query.message.chat.id)),
                                              callback_data=f"BanUser unban {user_data['id']}"))
    markup.add(types.InlineKeyboardButton(_("Отмена", await get_language(callback_query.message.chat.id)),
                                          callback_data="backToAdminMenu"))
    await bot.send_message(callback_query.message.chat.id,
                           await generate_admin_view_user_profile_template(user_data, callback_query),
                           parse_mode="HTML", reply_markup=markup)