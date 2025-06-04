from modules.favourit_module.commands_to_db import *
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from config import telegram_token
from aiogram.dispatcher import FSMContext
import math
from main import MyStates, bot, dp
from translations import _
from postgres.commands_to_db import get_language


@dp.callback_query_handler(lambda callback: 'addToFavourites' in callback.data)
async def add_to_favourites(callback, state: FSMContext):
    data = callback.data.split(' ')
    buyer = callback.message.chat.id
    id_good = data[1]
    add_favorite(id_good, buyer)
    await callback.answer("")

@dp.callback_query_handler(lambda callback: 'DelFavourites' in callback.data)
async def del_to_favourites(callback, state: FSMContext):
    data = callback.data.split(' ')
    buyer = callback.message.chat.id
    id_good = data[1]
    del_favorite(id_good, buyer)
    await callback.answer("")

async def generate_history_order_template(user_id, page):
    data = show_favourite(user_id)

    format_string = '%Y-%m-%d %H:%M:%S'

    result = f"{'Всего у Вас заказов'}: {len(data)}\n"
    if page == len(data) // 3 + 1:
        result = f"{'Всего у Вас заказов'}: {len(data)}\n"
    else:
        result = f"{'Всего у Вас заказов'}: {len(data)}\n"

    result += f"Страница {page} " \
              f" из {len(data) // 3 + 1}"
    return result, len(data)


@dp.callback_query_handler(lambda callback: 'getFavouriteGoods' in callback.data)
async def fav_history(callback_query: types.CallbackQuery):

    await callback_query.answer("")
    await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    text, orders_amount = await generate_history_order_template(callback_query.message.chat.id, 1)
    markup = types.InlineKeyboardMarkup()
    data = show_favourite(callback_query.message.chat.id)
    page = 1
    if page == len(data) // 3 + 1:
        for i in range(page * 3 - 3, len(data)):
            markup.add(types.InlineKeyboardButton(f"Заказ - {data[i]}", callback_data=f'ProductMenu {data[i]}'))
    else:
        for i in range(page * 3 - 3, 3):
            markup.add(types.InlineKeyboardButton(f"Заказ - {data[i]}", callback_data=f'ProductMenu {data[i]}'))
    if orders_amount > 3:
        markup.add(types.InlineKeyboardButton(f"{_('Вперёд', await get_language(callback_query.from_user.id))}➡️",
                                              callback_data=f'FavNextPage 2'))
        markup.add(types.InlineKeyboardButton(f"{_('В конец', await get_language(callback_query.message.chat.id))} ➡️",
                                              callback_data=f'FavPastPage {orders_amount // 3 + 1}'))

    await bot.send_message(callback_query.message.chat.id, text, reply_markup=markup)


@dp.callback_query_handler(lambda callback: 'FavLastPage' in callback.data)
async def FavLastPage(callback_query: types.CallbackQuery):

    await callback_query.answer("")
    await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    callback_data = callback_query.data.split(' ')
    page = int(callback_data[1])
    text, orders_amount = await generate_history_order_template(callback_query.from_user.id, page)
    markup = types.InlineKeyboardMarkup()
    data = show_favourite(callback_query.message.chat.id)
    if page == len(data) // 3 + 1:
        a = 0
        for i in range(page * 3 - 3, len(data)):
            if a < 3:
                markup.add(types.InlineKeyboardButton(f"Заказ - {data[i]}", callback_data=f'ProductMenu {data[i]}'))
                a += 1

    else:
        a = 0
        for i in range(page * 3 - 3, len(data)):
            print(a)
            if a < 3:
                markup.add(types.InlineKeyboardButton(f"Заказ - {data[i]}", callback_data=f'ProductMenu {data[i]}'))
                a += 1

    if page - 1 != 0 and page != orders_amount // 3 + 1:
        markup.add(types.InlineKeyboardButton(f"⬅️{_('Назад', await get_language(callback_query.from_user.id))}",
                                              callback_data=f'FavLastPage {page - 1}'),
                   types.InlineKeyboardButton(f"{_('Вперёд', await get_language(callback_query.from_user.id))}➡️",
                                              callback_data=f'FavNextPage {page + 1}'))
    else:
        if page - 1 != 0:
            markup.add(types.InlineKeyboardButton(f"⬅️{_('Назад', await get_language(callback_query.from_user.id))}",
                                                  callback_data=f'FavLastPage {page - 1}'))
        if page != orders_amount // 3 + 1:
            markup.add(
                types.InlineKeyboardButton(f"{_('Вперёд', await get_language(callback_query.from_user.id))}➡️",
                                           callback_data=f'FavNextPage {page + 1}'))

    markup.add(types.InlineKeyboardButton(f"⬅️{_('В начало', await get_language(callback_query.message.chat.id))}"
                                          , callback_data=f'getFavouriteGoods'),
               types.InlineKeyboardButton(f"{_('В конец', await get_language(callback_query.message.chat.id))} ➡️",
                                          callback_data=f'FavLastPage {orders_amount // 3 + 1}'))

    await bot.send_message(callback_query.message.chat.id, text, reply_markup=markup)


@dp.callback_query_handler(lambda callback: 'FavNextPage' in callback.data)
async def FavNextPage(callback_query: types.CallbackQuery):
    await callback_query.answer("")
    await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    callback_data = callback_query.data.split(' ')
    page = int(callback_data[1])
    text, orders_amount = await generate_history_order_template(callback_query.from_user.id, page)
    markup = types.InlineKeyboardMarkup()
    data = show_favourite(callback_query.message.chat.id)
    if page == len(data) // 3 + 1:
        a = 0
        for i in range(page * 3 - 3, len(data)):
            if a < 3:
                markup.add(types.InlineKeyboardButton(f"Заказ - {data[i]}", callback_data=f'ProductMenu {data[i]}'))
                a += 1
    else:
        a = 0
        for i in range(page * 3 - 3, len(data)):
            if a < 3:
                markup.add(types.InlineKeyboardButton(f"Заказ - {data[i]}", callback_data=f'ProductMenu {data[i]}'))
                a += 1
    if page - 1 != 0 and page != orders_amount // 3 + 1:
        markup.add(types.InlineKeyboardButton(f"⬅️{_('Назад', await get_language(callback_query.from_user.id))}",
                                              callback_data=f'FavLastPage {page - 1}'),
                   types.InlineKeyboardButton(f"{_('Вперёд', await get_language(callback_query.from_user.id))}➡️",
                                              callback_data=f'FavNextPage {page + 1}'))
    else:
        if page - 1 != 0:
            markup.add(types.InlineKeyboardButton(f"⬅️{_('Назад', await get_language(callback_query.from_user.id))}",
                                                  callback_data=f'FavLastPage {page - 1}'))
        if page != orders_amount // 3 + 1:
            markup.add(
                types.InlineKeyboardButton(f"{_('Вперёд', await get_language(callback_query.from_user.id))}➡️",
                                           callback_data=f'FavNextPage {page + 1}'))

    markup.add(types.InlineKeyboardButton(f"⬅️{_('В начало', await get_language(callback_query.message.chat.id))}",
                                          callback_data=f'getFavouriteGoods'),
               types.InlineKeyboardButton(f"{_('В конец', await get_language(callback_query.message.chat.id))} ➡️",
                                          callback_data=f'FavLastPage {orders_amount // 3 + 1}'))
    await bot.send_message(callback_query.message.chat.id, text, reply_markup=markup)


@dp.callback_query_handler(lambda callback: 'FavPastPage' in callback.data)
async def FavPastPage(callback_query: types.CallbackQuery):
    await callback_query.answer("")
    await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    callback_data = callback_query.data.split(' ')
    page = int(callback_data[1])
    text, orders_amount = await generate_history_order_template(callback_query.from_user.id, page)
    markup = types.InlineKeyboardMarkup()
    data = show_favourite(callback_query.message.chat.id)
    if page == len(data) // 3 + 1:
        a = 0
        for i in range(page * 3 - 3, len(data)):
            if a < 3:
                markup.add(types.InlineKeyboardButton(f"Заказ - {data[i]}", callback_data=f'ProductMenu {data[i]}'))
                print(data[i])
                a += 1
    else:
        a = 0
        for i in range(page * 3 - 3, len(data)):
            if a < 3:
                print(data[i])
                markup.add(types.InlineKeyboardButton(f"Заказ - {data[i]}", callback_data=f'ProductMenu {data[i]}'))
                a += 1

    markup.add(types.InlineKeyboardButton(f"⬅️{_('Назад', await get_language(callback_query.message.chat.id))}",
                                          callback_data=f'FavLastPage {page - 1}'))
    markup.add(types.InlineKeyboardButton(f"⬅️{_('В начало', await get_language(callback_query.message.chat.id))}",
                                          callback_data=f'getFavouriteGoods'))
    await bot.send_message(callback_query.message.chat.id, text, reply_markup=markup)
