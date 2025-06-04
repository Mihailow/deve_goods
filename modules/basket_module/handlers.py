from aiogram.dispatcher import FSMContext
from main import MyStates, bot, dp
from modules.basket_module.commands_to_db import add_product_to_basket_in_db, get_user_basket_from_db, \
    clean_basket_in_db
from modules.basket_module.generate_template import generate_basket_template
from modules.basket_module.keyboards import get_main_basket_keyboard
from postgres.commands_to_db import get_language
from translations import _
from aiogram import types


@dp.callback_query_handler(lambda callback: 'add_product_to_basket' in callback.data)
async def add_product_to_basket(callback_query: types.CallbackQuery):
    await callback_query.answer("")
    callback_query.data = callback_query.data.split(' ')
    user_id = callback_query.message.chat.id
    product_id = callback_query.data[1]
    count = callback_query.data[2]

    add_product_to_basket_in_db(user_id,product_id,count)

    await bot.send_message(callback_query.message.chat.id, "Товар был успешно добавлен в корзину")


async def get_basket(user_id):
    data = get_user_basket_from_db(user_id)
    template, price, currency = await generate_basket_template(data)
    if template != 'В корзине нет товаров':
        keyboards = await get_main_basket_keyboard(price, currency)
    else:
        keyboards = None
    await bot.send_message(user_id,template, reply_markup=keyboards)

@dp.callback_query_handler(lambda callback: 'clean_basket' in callback.data)
async def clean_basket(callback_query: types.CallbackQuery):
    await callback_query.answer("")
    await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    clean_basket_in_db(callback_query.message.chat.id)
    await bot.send_message(callback_query.message.chat.id, "Корзина была успешно очищена")
