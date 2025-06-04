import asyncio
import datetime
from datetime import timedelta
import json
import logging
import os
import time
from typing import List

from _decimal import Decimal
from aiogram.dispatcher.filters import Text, BoundFilter
from aiogram.types import InputMediaVideo, InputMediaPhoto, InputMediaAnimation
from aiogram.utils.json import JSON
from psycopg2 import Error
from aiogram import executor
from generate_product_quantity_selection import generate_product_quantity_selection, generate_calculator_selection, \
    generate_without_quantity_with_confirmation, generate_product_quantity_selection_back
from generate_template import *
from log_filter import ContextFilter
from modules.admin_module.admin_mailings.mailingsSystems import check_file_type, AlbumMiddleware
from misc import *
from payment import generate_markup_of_payment_systems, genereatePaymentComment
from postgres.commands_to_db import *
from translations import _
from modules.promo_code_module.handlers import *
from modules.admin_module.handlers import *
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from modules.admin_module.admin_settings_bot.handlers import *
from modules.admin_module.admin_user_management.handlers import *
from modules.admin_module.admin_mailings.handlers import *
from modules.basket_module.handlers import *
from action_handler import *

from modules.favourit_module.commands_to_db import *
from modules.favourit_module.handlers import *

@dp.message_handler(lambda message: message.get_command() not in (None, "/start", "/admin", "/help"))
async def answer_unknown_command(message: types.Message):
    await generate_and_send_default_message(message.from_user.id, 'invalid_command')


# Обработчик новых пользователей
@dp.message_handler(lambda message: message.from_user.id in unverified_users)
async def handle_new_users(message: types.Message):
    global user_notification
    result = get_template_from_db('agreements')

    if result is None:
        await update_user_status(message.from_user.id, "active")
        if user_notification:
            for admin in admins_users:
                await bot.send_message(admin, _(f'Зарегистрировался новый пользователь:',
                                                await get_language(
                                                    message.from_user.id)) + f' @{message.from_user.username}')
        await start(message)
    else:
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        keyboard.add(types.InlineKeyboardButton(text=_("Я прочитал соглашение и принимаю условия",
                                                       await get_language(message.from_user.id)),
                                                callback_data='agreement_with_terms'))
        await bot.send_message(chat_id=message.from_user.id,
                               text=_('Чтобы продолжить, ты должен согласиться с условиями пользования магазином.',
                                      await get_language(message.from_user.id)) + f"\n{result['template']}",
                               reply_markup=keyboard)

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(_('Начать!', await get_language(message.from_user.id)))


@dp.callback_query_handler(text=['agreement_with_terms'])
async def agreement_with_terms(call: types.CallbackQuery):
    await call.answer("")
    await call.message.answer(_("Вы приняли условия соглашения ✅ Теперь можете пользоваться ботом",
                                call.from_user.language_code))
    await update_user_status(call.from_user.id, "active")
    if user_notification:
        for admin in admins_users:
                await bot.send_message(admin, _(f'Зарегистрировался новый пользователь:',
                                            call.from_user.language_code) + f' @{call.from_user.username}')
    await start_from_callback(call)


@dp.message_handler(IsSubscriber(), commands=['start'])
async def start(message: types.Message):
    main_markup = await generate_main_panel_markup(message.from_user.id)
    await bot.send_message(message.chat.id, _("🏘 Меню", await get_language(message.from_user.id)),
                           reply_markup=main_markup)
    await generate_and_send_default_message(message.from_user.id, 'greetings')


async def start_from_callback(callback):
    user_id = callback.message.chat.id
    main_markup = await generate_main_panel_markup(user_id)
    await bot.send_message(callback.message.chat.id, _("🏘 Меню", await get_language(user_id)), reply_markup=main_markup)
    await generate_and_send_default_message(callback.message.chat.id, 'greetings')


@dp.callback_query_handler(lambda callback: 'AdminWatchOrdHist' in callback.data)
async def AdminWatchOrdHist(callback_query: types.CallbackQuery):
    data = callback_query.data.split(' ')
    user_id = data[1]
    await order_history(callback_query, user_id)


@dp.callback_query_handler(lambda callback: 'SendMessageUserFromAdmin' in callback.data)
async def SendMessageUserFromAdmin(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer("")
    await state.set_state(MyStates.send_message_from_admin_state.state)
    await state.update_data(user_id=callback_query.data.split(' ')[1])
    await bot.send_message(callback_query.message.chat.id, _('Введите сообщение, которое отправить пользователю',
                                                             await get_language(callback_query.message.chat.id)),
                           parse_mode="HTML")


@dp.callback_query_handler(lambda callback: 'AdminFindOrder' in callback.data)
async def do_find_order(callback, state: FSMContext):
    await callback.answer("")
    await state.set_state(MyStates.find_order.state)
    await bot.send_message(callback.message.chat.id,
                           _('Введите id заказа', await get_language(callback.message.chat.id)), parse_mode="HTML")


@dp.message_handler(state=MyStates.find_order)
async def do2_find_order(message, state: FSMContext):
    order_id = message.text
    order = get_order_from_db(order_id)
    # В будущем хранить в заказе валюту и способ оплаты
    if order != None:
        currency = "₽"
        method_of_payments = 'balance'
        date_format = "%d %B %Y %H:%M"
        formatted_datetime = order['time'].strftime(date_format)
        text = f"{_('Заказ', await get_language(message.from_user.id))} №{order['id']}\n" \
               f"{_('id покупателя', await get_language(message.from_user.id))}: {order['buyer']}\n" \
               f"{_('Статус', await get_language(message.from_user.id))}: {order['status']}\n" \
               f"{_('Товар', await get_language(message.from_user.id))}: {order['product_id']}\n" \
               f"{_('Сумма заказа', await get_language(message.from_user.id))}: {order['price']} {currency}\n" \
               f"{_('Способ оплаты', await get_language(message.from_user.id))}: {method_of_payments}\n" \
               f"{_('Время заказа', await get_language(message.from_user.id))}: {formatted_datetime}\n"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(_('Посмотреть заказ на сайте', await get_language(message.from_user.id)),
                                              callback_data='ShowOrderInSite'))
        # Реализовать
        markup.add(types.InlineKeyboardButton(_('Посмотреть товар', await get_language(message.from_user.id)),
                                              callback_data='getProductsFromOrder'))
        markup.add(types.InlineKeyboardButton(_('Сделать возврат', await get_language(message.from_user.id)),
                                              callback_data=f"MakeRefund {order['buyer']} {order['price']} {order['id']}"))
        # markup.add(types.InlineKeyboardButton('Удалить', callback_data='DeleteOrder'))
    else:
        text = _('Товар не был найден', await get_language(message.from_user.id))
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(_('Вернуться в админ панель', await get_language(message.from_user.id)),
                                              callback_data='backToAdminMenu'))

    await state.reset_state()
    await bot.send_message(message.chat.id, text, reply_markup=markup)


@dp.callback_query_handler(lambda callback: 'MakeRefund' in callback.data)
async def MakeRefund(callback, state: FSMContext):
    await state.update_data(buyer=callback.data.split(' ')[1],
                            price=callback.data.split(' ')[2],
                            id=callback.data.split(' ')[3])
    await callback.answer("")
    await state.set_state(MyStates.refund_order_state.state)
    await bot.send_message(callback.message.chat.id,
                           _('Укажите процент от суммы заказа для возврата на баланс (0-100%)(Только число)',
                             await get_language(callback.message.chat.id)),
                           parse_mode="HTML")


@dp.message_handler(state=MyStates.refund_order_state)
async def MakeRefundState(message, state: FSMContext):
    try:
        data = await state.get_data()
        buyer = data['buyer']
        price = float(data['price'])
        refund_procent = int(message.text)
        id = data['id']
        if refund_procent < 0 or refund_procent > 100:
            await bot.send_message(message.chat.id,
                                   text=_('Процент должен быть в диапазоне от 0 до 100. '
                                          'Введите корректный процент возврата.',
                                          await get_language(message.from_user.id)))
        else:
            balance_increase_in_db(buyer, refund_procent / 100 * price)
            await bot.send_message(message.chat.id, text="Баланс успешно зачислен")
            await bot.send_message(buyer,
                                   text=f"{_('Пришёл возврат в размере', await get_language(message.from_user.id))} "
                                        f"{round(refund_procent / 100 * price, 3)} "
                                        f"{_('за заказ', await get_language(message.from_user.id))} №{id}")
            await state.reset_state()
    except ValueError:
        await bot.send_message(message.chat.id,
                               _('Введите корректный процент', await get_language(message.from_user.id)))


@dp.message_handler(IsSubscriber())
async def main_panel(message: types.Message, state: FSMContext):
    action = name_and_action_reply_button.get(message.text)
    if action is None:
        await generate_and_send_default_message(message.from_user.id, 'invalid_command')

    if action == "products_availability":
        template, pages, page = await generate_products_availability_template(message)
        if pages == 1:
            await bot.send_message(message.from_user.id, template)
            return
        markup = types.InlineKeyboardMarkup()
        btns = []
        btns.append(types.InlineKeyboardButton("⬅️", callback_data=f"products_availability_page_back"))
        btns.append(types.InlineKeyboardButton(f"{page}/{pages}", callback_data=f"nothing"))
        btns.append(types.InlineKeyboardButton("➡️", callback_data=f"products_availability_page_next"))
        markup.row(*btns)
        await bot.send_message(message.from_user.id, template, reply_markup=markup)
        await state.update_data(products_availability_page=page)
    elif action == "all_categories":
        all_categories = get_categories_from_db()
        markup = types.InlineKeyboardMarkup()
        for category in all_categories:
            markup.add(
                types.InlineKeyboardButton(category['name'], callback_data=f" {category['id']}"))
        await message.answer(f"{_('Выберите категорию', await get_language(message.from_user.id))}:",
                             reply_markup=markup)
    elif action == "profile":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(_('История заказов',
                                                await get_language(message.from_user.id)),
                                              callback_data='OrderHistory'))
        markup.add(types.InlineKeyboardButton(_('Реферальная система',
                                                await get_language(message.from_user.id)),
                                              callback_data='ReferralSystem'))
        markup.add(types.InlineKeyboardButton(_('Активировать купон',
                                                await get_language(message.from_user.id)),
                                              callback_data='ActivateCoupon'))
        markup.add(types.InlineKeyboardButton(_('Пополнить баланс',
                                                await get_language(message.from_user.id)),
                                              callback_data='IncreaseBalanceGetAmount'),
                   types.InlineKeyboardButton(_('История пополнений',
                                                await get_language(message.from_user.id)),
                                              callback_data='PaymentsHistory'))
        markup.add(types.InlineKeyboardButton(_('Избранные товары',
                                                await get_language(message.from_user.id)),
                                              callback_data='getFavouriteGoods'))
        markup.add(types.InlineKeyboardButton(_('Изменить язык',
                                                await get_language(message.from_user.id)),
                                              callback_data='ChangeLanguage'))
        await bot.send_animation(message.chat.id, animation='https://i.yapx.cc/VakAF.gif',
                                 caption=await generate_profile_template(message.from_user.id),
                                 reply_markup=markup)
    elif action == "referral_system":
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton(_('История начислений', await get_language(message.from_user.id)),
                                       callback_data='RefHistory'))
        markup.add(types.InlineKeyboardButton(_('Рефералы', await get_language(message.from_user.id)),
                                              callback_data='RefList'))
        markup.add(types.InlineKeyboardButton(_('Реферальная ссылка отдельным сообщением',
                                                await get_language(message.from_user.id)),
                                              callback_data='RefOneMessage'))
        await bot.send_message(message.from_user.id,
                               f"{_('В боте включена реферальная система. Приглашайте друзей изарабатывайте на этом! Вы будете получать: 10% от каждой покупки вашего реферала. Ваша реферальная ссылка', await get_language(message.from_user.id))}\n https://t.me/ShopWithoutBasketBot/start={message.from_user.id}",
                               reply_markup=markup)
    elif action == "about_service" or action == "rules" or action == "about_store" or action == "help":
        template, markup = await generate_default_template(message.from_user.id, action)
        await message.answer(template, reply_markup=markup)
    elif action == 'order_history':
        template, orders_amount = await generate_history_order_template(message.from_user.id, 1)
        markup = types.InlineKeyboardMarkup()
        if orders_amount > 3:
            markup.add(
                types.InlineKeyboardButton(f"{_('Вперёд', await get_language(message.from_user.id))}➡️",
                                           callback_data=f'OrdHistNextPage 2'))
            markup.add(
                types.InlineKeyboardButton(f"{_('В конец', await get_language(message.from_user.id))}➡️",
                                           callback_data=f'OrdHistPastPage {orders_amount // 3 + 1}'))
        await message.answer(template, reply_markup=markup)
    elif action == 'activate_coupon':
        await state.set_state(MyStates.activateCoupon.state)
        await message.answer(f"{_('Введите промокод', await get_language(message.from_user.id))}: ",
                             parse_mode="HTML")
    elif action == 'admin':
        if message.from_user.id not in admins_users:
            await message.answer(
                _('К сожалению, вы не являетесь администратором', await get_language(message.from_user.id)))
            return
        markup = await get_admin_keyboards_for_message_handler(message.from_user.id)
        await message.answer(await generate_admin_menu_template(message), parse_mode="HTML", reply_markup=markup)
    elif action == 'message':
        await message.answer(message_action_dictionary[message.text], parse_mode="HTML")
    elif action == 'basket':
        await get_basket(message.from_user.id)
    elif action == 'select_category':
        await display_categories_from_message(message_action_dictionary[message.text], message)
    elif action == 'select_product':
        await product_menu_from_message(message_action_dictionary[message.text], message)


@dp.callback_query_handler(lambda callback: 'ChangeLanguage' in callback.data)
async def ChangeLanguage(callback_query: types.CallbackQuery):
    await callback_query.answer("")
    await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    data = callback_query.data.split(' ')
    markup = types.InlineKeyboardMarkup()
    if len(data) == 1:
        markup.add(types.InlineKeyboardButton(_('ru', await get_language(callback_query.message.chat.id)),
                                              callback_data='ChangeLanguage ru'),
                   types.InlineKeyboardButton(_('en', await get_language(callback_query.message.chat.id)),
                                              callback_data='ChangeLanguage en'))
        await bot.send_message(callback_query.message.chat.id,
                               _('Выберите язык:', await get_language(callback_query.message.chat.id)),
                               reply_markup=markup)
    else:
        lang = data[1]
        update_language(callback_query.message.chat.id, lang)
        await bot.send_message(callback_query.message.chat.id,
                               f"{_('Язык был успешно изменен на', await get_language(callback_query.message.chat.id))} - {lang}")
        await start_from_callback(callback_query)


async def send_file(type_file, chat_id, file_id, text=None, media_group=None):
    if media_group is not None:
        await bot.send_media_group(chat_id=chat_id, media=media_group)
    else:
        if type_file == 'photo':
            await bot.send_photo(chat_id=chat_id, photo=file_id, caption=text)
        elif type_file == 'animation':
            await bot.send_animation(chat_id=chat_id, animation=file_id, caption=text)
        elif type_file == 'video':
            await bot.send_video(chat_id=chat_id, video=file_id, caption=text)


@dp.callback_query_handler(lambda callback: 'PaymentsHistory' in callback.data)
async def PaymentsHistory(callback_query: types.CallbackQuery):
    await callback_query.answer("")
    await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    page = 1
    text, page_count = await generate_history_payments_template(callback_query.from_user.id, page, callback_query)

    markup = types.InlineKeyboardMarkup()
    if page_count > 1:
        buttons = []
        if page > 1:
            buttons.append(types.InlineKeyboardButton(f"⬅️", callback_data=f'PayHistLastPage {page-1}'))
        if page != page_count:
            buttons.append(types.InlineKeyboardButton(f"➡️", callback_data=f'PayHistNextPage {page+1}'))
        markup.row(*buttons)
    await bot.send_message(callback_query.message.chat.id, text, reply_markup=markup)


@dp.callback_query_handler(lambda callback: 'PayHistLastPage' in callback.data)
async def OrdHistLastPage(callback_query: types.CallbackQuery):
    await callback_query.answer("")
    await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    callback_data = callback_query.data.split(' ')
    page = int(callback_data[1])
    text, page_count = await generate_history_payments_template(callback_query.from_user.id, page, callback_query)

    markup = types.InlineKeyboardMarkup()
    if page_count > 1:
        buttons = []
        if page > 1:
            buttons.append(types.InlineKeyboardButton(f"⬅️", callback_data=f'PayHistLastPage {page-1}'))
        if page != page_count:
            buttons.append(types.InlineKeyboardButton(f"➡️", callback_data=f'PayHistNextPage {page+1}'))
        markup.row(*buttons)
    await bot.send_message(callback_query.message.chat.id, text, reply_markup=markup)


@dp.callback_query_handler(lambda callback: 'PayHistNextPage' in callback.data)
async def OrdHistNextPage(callback_query: types.CallbackQuery):
    await callback_query.answer("")
    await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    callback_data = callback_query.data.split(' ')
    page = int(callback_data[1])
    text, page_count = await generate_history_payments_template(callback_query.from_user.id, page, callback_query)

    markup = types.InlineKeyboardMarkup()
    if page_count > 1:
        buttons = []
        if page > 1:
            buttons.append(types.InlineKeyboardButton(f"⬅️", callback_data=f'PayHistLastPage {page-1}'))
        if page != page_count:
            buttons.append(types.InlineKeyboardButton(f"➡️", callback_data=f'PayHistNextPage {page+1}'))
        markup.row(*buttons)
    await bot.send_message(callback_query.message.chat.id, text, reply_markup=markup)


@dp.callback_query_handler(lambda callback: 'OrderHistory' in callback.data)
async def order_history(callback_query: types.CallbackQuery):
    await callback_query.answer("")
    await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    text, orders_amount = await generate_history_order_template(callback_query.from_user.id, 1)

    markup = types.InlineKeyboardMarkup()
    if orders_amount > 3:
        markup.add(types.InlineKeyboardButton(f"{_('Вперёд', await get_language(callback_query.message.chat.id))}➡️",
                                              callback_data=f'OrdHistNextPage 2'))
        markup.add(types.InlineKeyboardButton(f"{_('В конец', await get_language(callback_query.message.chat.id))}➡️",
                                              callback_data=f'OrdHistPastPage {orders_amount // 3 + 1}'))
    await bot.send_message(callback_query.message.chat.id, text, reply_markup=markup)


async def order_history(callback_query: types.CallbackQuery, user_id):
    await callback_query.answer("")
    text, orders_amount = await generate_history_order_template(user_id, 1)

    markup = types.InlineKeyboardMarkup()
    if orders_amount > 3:
        markup.add(types.InlineKeyboardButton(f"{_('Вперёд', await get_language(callback_query.message.chat.id))}➡️",
                                              callback_data=f'OrdHistNextPage 2'))
        markup.add(types.InlineKeyboardButton(f"{_('В конец', await get_language(callback_query.message.chat.id))}➡️",
                                              callback_data=f'OrdHistPastPage {orders_amount // 3 + 1}'))

    await bot.send_message(callback_query.message.chat.id, text, reply_markup=markup)


@dp.callback_query_handler(lambda callback: 'OrdHistLastPage' in callback.data)
async def OrdHistLastPage(callback_query: types.CallbackQuery):
    await callback_query.answer("")
    await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    callback_data = callback_query.data.split(' ')
    page = int(callback_data[1])
    text, orders_amount = await generate_history_order_template(callback_query.from_user.id, page)
    markup = types.InlineKeyboardMarkup()

    if page - 1 != 0 and page != orders_amount // 3 + 1:
        markup.add(types.InlineKeyboardButton(f"⬅️{_('Назад', await get_language(callback_query.message.chat.id))}",
                                              callback_data=f'OrdHistLastPage {page - 1}'),
                   types.InlineKeyboardButton(f"{_('Вперёд', await get_language(callback_query.message.chat.id))}➡️",
                                              callback_data=f'OrdHistNextPage {page + 1}'))
    else:
        if page - 1 != 0:
            markup.add(types.InlineKeyboardButton(f"⬅️{_('Назад', await get_language(callback_query.message.chat.id))}",
                                                  callback_data=f'OrdHistLastPage {page - 1}'))
        if page != orders_amount // 3 + 1:
            markup.add(
                types.InlineKeyboardButton(f"{_('Вперёд', await get_language(callback_query.message.chat.id))}➡️",
                                           callback_data=f'OrdHistNextPage {page + 1}'))

    markup.add(types.InlineKeyboardButton(f"⬅️{_('В начало', await get_language(callback_query.message.chat.id))}"
                                          , callback_data=f'OrderHistory'),
               types.InlineKeyboardButton(f"{_('В конец', await get_language(callback_query.message.chat.id))}➡️",
                                          callback_data=f'OrdHistLastPage {orders_amount // 3 + 1}'))

    await bot.send_message(callback_query.message.chat.id, text, reply_markup=markup)


@dp.callback_query_handler(lambda callback: 'OrdHistNextPage' in callback.data)
async def OrdHistNextPage(callback_query: types.CallbackQuery):
    await callback_query.answer("")
    await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    callback_data = callback_query.data.split(' ')
    page = int(callback_data[1])
    text, orders_amount = await generate_history_order_template(callback_query.from_user.id, page)
    markup = types.InlineKeyboardMarkup()

    if page - 1 != 0 and page != orders_amount // 3 + 1:
        markup.add(types.InlineKeyboardButton(f"⬅️{_('Назад', await get_language(callback_query.message.chat.id))}",
                                              callback_data=f'OrdHistLastPage {page - 1}'),
                   types.InlineKeyboardButton(f"{_('Вперёд', await get_language(callback_query.message.chat.id))}➡️",
                                              callback_data=f'OrdHistNextPage {page + 1}'))
    else:
        if page - 1 != 0:
            markup.add(types.InlineKeyboardButton(f"⬅️{_('Назад', await get_language(callback_query.message.chat.id))}",
                                                  callback_data=f'OrdHistLastPage {page - 1}'))
        if page != orders_amount // 3 + 1:
            markup.add(
                types.InlineKeyboardButton(f"{_('Вперёд', await get_language(callback_query.message.chat.id))}➡️",
                                           callback_data=f'OrdHistNextPage {page + 1}'))

    markup.add(types.InlineKeyboardButton(f"⬅️{_('В начало', await get_language(callback_query.message.chat.id))}",
                                          callback_data=f'OrderHistory'),
               types.InlineKeyboardButton(f"{_('В конец', await get_language(callback_query.message.chat.id))}➡️",
                                          callback_data=f'OrdHistLastPage {orders_amount // 3 + 1}'))
    await bot.send_message(callback_query.message.chat.id, text, reply_markup=markup)


@dp.callback_query_handler(lambda callback: 'OrdHistPastPage' in callback.data)
async def OrdHistPastPage(callback_query: types.CallbackQuery):
    await callback_query.answer("")
    await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    callback_data = callback_query.data.split(' ')
    page = int(callback_data[1])
    text, orders_amount = await generate_history_order_template(callback_query.from_user.id, page)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(f"⬅️{_('Назад', await get_language(callback_query.message.chat.id))}",
                                          callback_data=f'OrdHistLastPage {page - 1}'))
    markup.add(types.InlineKeyboardButton(f"⬅️{_('В начало', await get_language(callback_query.message.chat.id))}",
                                          callback_data=f'OrderHistory'))
    await bot.send_message(callback_query.message.chat.id, text, reply_markup=markup)


@dp.callback_query_handler(lambda callback: 'ReferralSystem' in callback.data)
async def main_referral_system(callback_query: types.CallbackQuery):
    await callback_query.answer("")
    await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(_('История начислений', await get_language(callback_query.message.chat.id)),
                                          callback_data='RefHistory'))
    markup.add(types.InlineKeyboardButton(_('Рефералы', await get_language(callback_query.message.chat.id)),
                                          callback_data='RefList'))
    markup.add(types.InlineKeyboardButton(_('Реферальная ссылка отдельным сообщением',
                                            await get_language(callback_query.message.chat.id)),
                                          callback_data='RefOneMessage'))
    await bot.send_message(callback_query.message.chat.id,
                           f"{_('В боте включена реферальная система. Приглашайте друзей изарабатывайте на этом! Вы будете получать: 10% от каждой покупки вашего реферала. Ваша реферальная ссылка', await get_language(callback_query.message.chat.id))}\n https://t.me/ShopWithoutBasketBot/start={callback_query.message.from_user.id}",
                           reply_markup=markup)


@dp.callback_query_handler(lambda callback: 'RefOneMessage' in callback.data)
async def ref_one_message(callback_query: types.CallbackQuery):
    await callback_query.answer("")
    await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    await bot.send_message(callback_query.message.chat.id,
                           f'https://t.me/ShopWithoutBasketBot/start={callback_query.message.from_user.id}')


@dp.callback_query_handler(lambda callback: 'IncreaseBalanceGetAmount' in callback.data)
async def start_increase_balance(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer("")
    await state.set_state(MyStates.increaseBalance.state)
    await bot.send_message(callback_query.message.chat.id, _('Отправьте сумму пополнения:',
                                                             await get_language(callback_query.message.chat.id)))


@dp.message_handler(state=MyStates.increaseBalance)
async def handle_increase_balance(message, state: FSMContext):
    user_id = message.from_user.id
    try:
        amount = float(message.text)  # Получаем введенную сумму
        await state.reset_state()
        markup = await generate_markup_of_payment_systems(user_id, amount)
        await bot.send_message(message.chat.id,
                               text=_('Выберите платёжную систему', await get_language(message.from_user.id)),
                               reply_markup=markup, parse_mode="HTML")
    except ValueError:
        await bot.send_message(message.chat.id,
                               _('Введите корректную сумму.', await get_language(message.from_user.id)))


async def GenerateAdminChangeProductParametersMarkup(productID, message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(_('Изменить название', await get_language(message.from_user.id)),
                                          callback_data=f'AdminChangeNameProduct {productID}'))
    markup.add(types.InlineKeyboardButton(_('Изменить описание', await get_language(message.from_user.id)),
                                          callback_data=f'AdminChangeDescProduct {productID}'))
    markup.add(types.InlineKeyboardButton(_('Изменить цену', await get_language(message.from_user.id)),
                                          callback_data=f'AdminChangePriceProduct {productID}'))
    markup.add(types.InlineKeyboardButton(f"⬅️ {_('Назад', await get_language(message.from_user.id))}",
                                          callback_data=f'AdminProductMenu {productID}'))
    return markup


@dp.message_handler(state=MyStates.adminChangeNameProduct)
async def ChangeNameProductConfirm(message, state: FSMContext):
    productID = await state.get_data()
    productID = productID['value']
    try:
        text = message.text
        update_product_in_db('name', text, productID)
        await state.reset_state()
        await bot.send_message(message.chat.id, text=_('Название было успешно изменено',
                                                       await get_language(message.from_user.id)))
        markup = await GenerateAdminChangeProductParametersMarkup(productID, message)
        await bot.send_message(message.chat.id, await generate_product_template(message.from_user.id, productID, 1), reply_markup=markup,
                               parse_mode="HTML")
    except Exception:
        await bot.send_message(message.chat.id, _('Введите корр ектное название товара',
                                                  await get_language(message.from_user.id)))


@dp.message_handler(state=MyStates.adminChangeDescProduct)
async def ChangeDescProductConfirm(message, state: FSMContext):
    productID = await state.get_data()
    productID = productID['value']
    try:
        text = message.text
        update_product_in_db('description', text, productID)
        await state.reset_state()
        await bot.send_message(message.chat.id, text=_('Описание было успешно изменено',
                                                       await get_language(message.from_user.id)))
        markup = await GenerateAdminChangeProductParametersMarkup(productID, message)
        await bot.send_message(message.chat.id, await generate_product_template(message.from_user.id, productID, 1), reply_markup=markup,
                               parse_mode="HTML")
    except Exception:
        await bot.send_message(message.chat.id, _('Введите корректное описание товара',
                                                  await get_language(message.from_user.id)))


@dp.message_handler(state=MyStates.adminChangePriceProduct)
async def ChangePriceProductConfirm(message, state: FSMContext):
    productID = await state.get_data()
    productID = productID['value']
    try:
        amount = float(message.text)  # Получаем введенную сумму
        if amount < 0:
            await bot.send_message(message.chat.id, text=_('Цена не может быть меньше 0. Введите корректную сумму.',
                                                           await get_language(message.from_user.id)))
        else:
            update_product_in_db('price', amount, productID)
            await bot.send_message(message.chat.id, text=_('Цена была успешно изменена',
                                                           await get_language(message.from_user.id)))
            await state.reset_state()
            markup = await GenerateAdminChangeProductParametersMarkup(productID, message)
            await bot.send_message(message.chat.id, await generate_product_template(message.from_user.id, productID, 1), reply_markup=markup,
                                   parse_mode="HTML")
    except ValueError:
        await bot.send_message(message.chat.id,
                               _('Введите корректную сумму.', await get_language(message.from_user.id)))


@dp.message_handler(state=MyStates.CreateNewProductSelectName)
async def CreateNewProductSelectNameConfirm(message, state: FSMContext):
    try:
        text = message.text
        await state.update_data(name=text)
        await state.set_state(MyStates.CreateNewProductSelectDesc.state)
        await bot.send_message(message.chat.id,
                               text=_('Введите описание товара:', await get_language(message.from_user.id)))
    except Exception:
        await bot.send_message(message.chat.id,
                               _('Введите корректное имя товара:', await get_language(message.from_user.id)))


@dp.message_handler(state=MyStates.CreateNewProductSelectDesc)
async def CreateNewProductSelectDescConfirm(message, state: FSMContext):
    try:
        text = message.text
        await state.update_data(desc=text)
        await state.set_state(MyStates.CreateNewProductSelectPrice.state)
        await bot.send_message(message.chat.id,
                               text=_('Введите цену товара:', await get_language(message.from_user.id)))
    except Exception:
        await bot.send_message(message.chat.id,
                               _('Введите корректное описание товара:', await get_language(message.from_user.id)))


@dp.message_handler(state=MyStates.CreateNewProductSelectPrice)
async def CreateNewProductSelectPriceConfirm(message, state: FSMContext):
    try:
        amount = float(message.text)  # Получаем введенную сумму
        if amount < 0:
            await bot.send_message(message.chat.id, text=_('Цена не может быть меньше 0. Введите корректную сумму.',
                                                           await get_language(message.from_user.id)))
        else:
            await state.update_data(price=amount)
            data = await state.get_data()
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(_('Вернуться в категорию', await get_language(message.from_user.id)),
                                                  callback_data=f"AdminDisplayCategories {data['id_category']}"))
            add_new_product_to_db(data['id_category'], data['type'], data['name'], data['desc'], data['price'])
            await state.reset_state()
            await bot.send_message(message.chat.id,
                                   text=f"{_('Товар', await get_language(message.from_user.id))} "
                                        f"{data['name']} {_('успешно добавлен!', await get_language(message.from_user.id))}",
                                   reply_markup=markup)

    except ValueError:
        await bot.send_message(message.chat.id,
                               _('Введите корректную сумму.', await get_language(message.from_user.id)))


@dp.message_handler(state=MyStates.searchByID)
async def earchByID(message, state: FSMContext):
    try:
        text = message.text
        if text == _('Завершить', await get_language(message.from_user.id)):
            await state.reset_state()
            await bot.send_message(message.chat.id,
                                   _('Поиск товара по ID завершён.', await get_language(message.from_user.id)))
        else:
            product = get_product_from_db(int(text), message.from_user.id)
            if product == None:
                await bot.send_message(message.chat.id,
                                       _('Товар с таким ID не найден', await get_language(message.from_user.id)))
            else:
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton(_('Перейти к товару', await get_language(message.from_user.id)),
                                                      callback_data=f"AdminProductMenu {product['id']}"))
                await bot.send_message(message.chat.id,
                                       f"{_('Найден товар:', await get_language(message.from_user.id))}"
                                       f" {product['name']}", reply_markup=markup)
                await state.reset_state()
    except Exception as ex:
        print(ex)


@dp.message_handler(state=MyStates.searchByName)
async def earchByName(message, state: FSMContext):
    try:
        name = message.text
        products = get_products_by_name_from_db(name)
        markup = types.InlineKeyboardMarkup()
        MAX_COUNT = 5
        COUNT = 0
        for product in products:
            if COUNT != 5:
                markup.add(
                    types.InlineKeyboardButton(f"{product['name']} | "
                                               f"{product['price']}{product['currency']} | "
                                               f"{_('Кол-во', await get_language(message.from_user.id))}"
                                               f" {product['amount']} {_('шт.', await get_language(message.from_user.id))}",
                                               callback_data=f"AdminProductMenu {product['id']}"))
        markup.add(types.InlineKeyboardButton(f"{_('Вернуться', await get_language(message.from_user.id))}",
                                              callback_data=f"backToAdminMenu"))

        await bot.send_message(message.chat.id, _('Выберите нужный товар:', await get_language(message.from_user.id)),
                               reply_markup=markup)
        await state.reset_state()
        # if product == None:
        #    await bot.send_message(message.chat.id, 'Товар с таким ID не найден')
        # else:
        #    markup = types.InlineKeyboardMarkup()
        #    markup.add(types.InlineKeyboardButton("Перейти к товару",
        #                                          callback_data=f"AdminProductMenu {product['id']}"))
        #    await bot.send_message(message.chat.id, f"Найден товар: {product['name']}", reply_markup=markup)
    except Exception as ex:
        print(ex)


@dp.message_handler(content_types=['document', 'text'], state=MyStates.adminAddProductDataNonuniqueF)
async def AdminAddProductDataNonuniqueF(message, state: FSMContext):
    userID = message.from_user.id
    productID = await state.get_data()
    productID = productID['value']
    if message.content_type == 'text':
        if message.text == _('Завершить', await get_language(message.from_user.id)):
            await state.reset_state()
            await bot.send_message(message.chat.id, text=_('Загрузка файла была отменена',
                                                           await get_language(message.from_user.id)))
            markup = await GenerateAdminChangeProductParametersMarkup(productID, message)
            await bot.send_message(message.chat.id, await generate_product_template(message.from_user.id, productID, 1), reply_markup=markup,
                                   parse_mode="HTML")
    if message.content_type == 'document':
        data = []
        data.append(str(userID) + " " + str(message.document.file_id))
        delete_all_product_data_from_db(productID)
        result = add_product_data_to_db(productID, data, True)
        if result == 1:
            await bot.send_message(message.chat.id, text=f"{_('Файл', await get_language(message.from_user.id))} ' \
                                                                   '{message.document.file_name} "
                                                         f"{_('был успешно добавлен', await get_language(message.from_user.id))}")
        else:
            await bot.send_message(message.chat.id,
                                   text=f"{_('При добавлении файла произошла ошибка и он не был добавлен.', await get_language(message.from_user.id))}\n")
        await state.reset_state()
        markup = await GenerateAdminChangeProductParametersMarkup(productID, message)
        await bot.send_message(message.chat.id, await generate_product_template(message.from_user.id, productID, 1), reply_markup=markup,
                               parse_mode="HTML")


@dp.message_handler(content_types=['document', 'text'], state=MyStates.adminAddProductDataUniqueF)
async def AdminAddProductDataUniqueF(message, state: FSMContext):
    userID = message.from_user.id
    productID = await state.get_data()
    productID = productID['value']
    if message.content_type == 'text':
        if message.text == _('Завершить', await get_language(message.from_user.id)):
            await bot.send_message(message.chat.id, text=_('Загрузка файлов успешно завершена',
                                                           await get_language(message.from_user.id)))
            markup = await GenerateAdminChangeProductParametersMarkup(productID, message)
            await bot.send_message(message.chat.id, await generate_product_template(message.from_user.id, productID, 1), reply_markup=markup,
                                   parse_mode="HTML")
            await state.reset_state()
    if message.content_type == 'document':
        data = []
        data.append(str(userID) + " " + str(message.document.file_id))
        result = add_product_data_to_db(productID, data, True)
        if result == 1:
            await bot.send_message(message.chat.id, text=f"{_('Файл', await get_language(message.from_user.id))} ' \
                                                                               '{message.document.file_name} "
                                                         f"{_('был успешно добавлен', await get_language(message.from_user.id))}")
        else:
            await bot.send_message(message.chat.id,
                                   text=f"{_('При добавлении файла произошла ошибка и он не был добавлен.', await get_language(message.from_user.id))}\n")


@dp.message_handler(content_types=['text'], state=[MyStates.adminAddProductDataNonuniqueP,
                                                   MyStates.adminAddProductDataService,
                                                   MyStates.adminAddProductDataNonuniqueGift])
async def AdminAddProductDataNonuniqueP(message, state: FSMContext):
    productID = await state.get_data()
    productID = productID['value']
    data = []
    data.append(message.text)
    delete_all_product_data_from_db(productID)
    result = add_product_data_to_db(productID, data, False)
    if result == 1:
        await bot.send_message(message.chat.id,
                               text=_('Товар был успешно добавлен', await get_language(message.from_user.id)))
        markup = await GenerateAdminChangeProductParametersMarkup(productID, message)
        await bot.send_message(message.chat.id, await generate_product_template(message.from_user.id, productID, 1), reply_markup=markup,
                               parse_mode="HTML")
        await state.reset_state()
    else:
        await bot.send_message(message.chat.id,
                               text=f"{_('При добавлении товара произошла ошибка и он не был добавлен.', await get_language(message.from_user.id))}\n")
        markup = await GenerateAdminChangeProductParametersMarkup(productID, message)
        await bot.send_message(message.chat.id, await generate_product_template(message.from_user.id, productID, 1), reply_markup=markup,
                               parse_mode="HTML")
        await state.reset_state()


@dp.message_handler(content_types=['document', 'text'], state=[MyStates.adminAddProductDataUniqueP,
                                                               MyStates.adminAddProductDataUniqueGift])
async def AdminAddProductDataUniqueP(message, state: FSMContext):
    userID = message.from_user.id
    productID = await state.get_data()
    productID = productID['value']
    if message.content_type == 'text':
        data = message.text.split('\n')
        result = add_product_data_to_db(productID, data, True)
        if result == 1:
            await bot.send_message(message.chat.id,
                                   text=_('Товар был успешно добавлен', await get_language(message.from_user.id)))
            markup = await GenerateAdminChangeProductParametersMarkup(productID, message)
            await bot.send_message(message.chat.id, await generate_product_template(message.from_user.id, productID, 1), reply_markup=markup,
                                   parse_mode="HTML")
            await state.reset_state()
        else:
            await bot.send_message(message.chat.id,
                                   text=f"{_('При добавлении товара произошла ошибка и он не был добавлен.', await get_language(message.from_user.id))}\n")
            markup = await GenerateAdminChangeProductParametersMarkup(productID, message)
            await bot.send_message(message.chat.id, await generate_product_template(message.from_user.id, productID, 1), reply_markup=markup,
                                   parse_mode="HTML")
            await state.reset_state()
    elif message.content_type == 'document':
        file_info = await bot.get_file(message.document.file_id)
        file_path = file_info.file_path
        file_extension = os.path.splitext(file_path)[1]
        if file_extension == '.txt':
            downloaded_file = await bot.download_file(file_path)
            data = downloaded_file.read().decode('utf-8')
            data = data.splitlines()
            result = add_product_data_to_db(productID, data, True)
            if result == 1:
                await bot.send_message(message.chat.id,
                                       text=_('Товар был успешно добавлен', await get_language(message.from_user.id)))
                markup = await GenerateAdminChangeProductParametersMarkup(productID, message)
                await bot.send_message(message.chat.id, await generate_product_template(message.from_user.id, productID, 1),
                                       reply_markup=markup,
                                       parse_mode="HTML")
                await state.reset_state()
            else:
                await bot.send_message(message.chat.id,
                                       text=f"{_('При добавлении товара произошла ошибка и он не был добавлен.', await get_language(message.from_user.id))}\n")
                markup = await GenerateAdminChangeProductParametersMarkup(productID, message)
                await bot.send_message(message.chat.id, await generate_product_template(message.from_user.id, productID, 1),
                                       reply_markup=markup,
                                       parse_mode="HTML")
                await state.reset_state()
        else:
            await bot.send_message(message.chat.id,
                                   text=f"{_('Вами был отправлен не .txt файл. Новый товар не добавлен.', await get_language(message.from_user.id))}\n")
            markup = await GenerateAdminChangeProductParametersMarkup(productID, message)
            await bot.send_message(message.chat.id, await generate_product_template(message.from_user.id, productID, 1), reply_markup=markup,
                                   parse_mode="HTML")
            await state.reset_state()


@dp.message_handler(state=MyStates.adminDeleteProductData)
async def AdminDeleteProductDataConfirm(message, state: FSMContext):
    data = await state.get_data()
    productID = data['value']
    type = data['type']

    try:
        if message.text == "*":
            product = get_product_from_db(productID, message.from_user.id)
            count = int(product['amount'])
        else:
            count = int(message.text)

        result = unload_unused_product_data_from_db(productID, count)
        if result == None:
            await bot.send_message(message.chat.id, text=_('При выгрузке данных произошла ошибка',
                                                           await get_language(message.from_user.id)))
            markup = await GenerateAdminChangeProductParametersMarkup(productID, message)
            await bot.send_message(message.chat.id, await generate_product_template(message.from_user.id, productID, 1), reply_markup=markup,
                                   parse_mode="HTML")
            return
        if len(result) == 0:
            await bot.send_message(message.chat.id,
                                   text=_('Товары для выгрузки отсуствуют', await get_language(message.from_user.id)))
            markup = await GenerateAdminChangeProductParametersMarkup(productID, message)
            await bot.send_message(message.chat.id, await generate_product_template(message.from_user.id, productID, 1), reply_markup=markup,
                                   parse_mode="HTML")
            return
        if type == 'nonuniqueFile' or type == 'uniqueFile':
            await bot.send_message(message.chat.id, _("Выгруженные файлы:", await get_language(message.from_user.id)))
            for line in result:
                data = line.split(' ')
                user_id = data[0]
                document_id = data[1]
                await bot.send_document(message.chat.id, document_id)
            await state.reset_state()
            markup = await GenerateAdminChangeProductParametersMarkup(productID, message)
            await bot.send_message(message.chat.id, await generate_product_template(message.from_user.id, productID, 1), reply_markup=markup,
                                   parse_mode="HTML")
            return

        current_datetime = datetime.now()
        filename = current_datetime.strftime("%Y-%m-%d.txt")
        filename = f"{_('Выгрузка товара', await get_language(message.from_user.id))} №{productID} " + filename
        with open(filename, 'w', encoding='utf-8') as file:
            for item in result:
                file.write(item + '\n')
        with open(filename, 'rb') as f:
            await bot.send_document(message.chat.id, f,
                                    caption=_("Данные были успешно выгружены",
                                              await get_language(message.from_user.id)))
        os.remove(filename)
        await state.reset_state()
        markup = await GenerateAdminChangeProductParametersMarkup(productID, message)
        await bot.send_message(message.chat.id, await generate_product_template(message.from_user.id, productID, 1), reply_markup=markup,
                               parse_mode="HTML")
    except ValueError:
        await bot.send_message(message.chat.id,
                               _("Пожалуйста, отправьте только число или *", await get_language(message.from_user.id)))


@dp.callback_query_handler(lambda callback: 'CreatingPayment' in callback.data)
async def CreatingPayment(callback_query: types.CallbackQuery):
    await callback_query.answer("")
    await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    # Требуется доработка


@dp.callback_query_handler(lambda callback: 'DisplayCategories' in callback.data)
async def display_categories(callback_query: types.CallbackQuery):
    callback_data = callback_query.data.split(' ')

    is_admin = False
    if 'Admin' in callback_data[0]:
        is_admin = True
    category_id = callback_data[1]

    # Отображение каталога, когда передаётся в callback id каталога
    categories = get_sub_categories_from_db(category_id)
    await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    markup = types.InlineKeyboardMarkup()
    if is_admin:
        markup.add(
            types.InlineKeyboardButton(_("Создать новый товар", await get_language(callback_query.message.chat.id)),
                                       callback_data=f"CreateNewProduct {category_id}"))

    for category in categories:
        callback = f"AdminDisplayCategories {category['id']}" if is_admin else f"DisplayCategories {category['id']}"
        markup.add(types.InlineKeyboardButton(category['name'], callback_data=callback))

    # Отображение товара каталога, когда передаётся в callback id каталога
    products = get_products_from_db(category_id, callback_query.from_user.id)
    for product in products:
        callback = f"AdminProductMenu {product['id']}" if is_admin else f"ProductMenu {product['id']}"
        button_text = f"{product['name']} | {product['price']}{product['currency']} " \
                      f"| {_('Кол-во:', await get_language(callback_query.message.chat.id))} " \
                      f"{product['amount']} {_('шт.', await get_language(callback_query.message.chat.id))}"
        markup.add(types.InlineKeyboardButton(button_text, callback_data=callback))

    # Придумать как убрать кнопку ️⬅️ Назад из первого выбора категорий
    id = callback_data[1]
    if id != '1' and id != '6':
        if is_admin:
            markup.row(
                types.InlineKeyboardButton(f"️⬅️ {_('Назад', await get_language(callback_query.message.chat.id))}",
                                           callback_data=f"AdminBackToOneCategory {callback_data[1]}"))
        else:
            markup.row(
                types.InlineKeyboardButton(f"️⬅️ {_('Назад', await get_language(callback_query.message.chat.id))}",
                                           callback_data=f"BackToOneCategory {callback_data[1]}"))
    if is_admin:
        markup.row(types.InlineKeyboardButton(
            f"⬅️ {_('Назад ко всем категориям', await get_language(callback_query.message.chat.id))}",
            callback_data="AdminBackToAllCategories"))
    else:
        markup.row(types.InlineKeyboardButton(
            f"⬅️ {_('Назад ко всем категориям', await get_language(callback_query.message.chat.id))}",
            callback_data="BackToAllCategories"))

    await bot.send_message(callback_query.message.chat.id, await generate_catalog_template(category_id),
                           reply_markup=markup)


async def display_categories_from_message(category_id, message):
    # Отображение каталога, когда передаётся в callback id каталога
    categories = get_sub_categories_from_db(category_id)
    await bot.delete_message(message.chat.id, message.message_id)
    markup = types.InlineKeyboardMarkup()

    for category in categories:
        callback = f"DisplayCategories {category['id']}"
        markup.add(types.InlineKeyboardButton(category['name'], callback_data=callback))

    # Отображение товара каталога, когда передаётся в callback id каталога
    products = get_products_from_db(category_id, message.from_user.id)
    for product in products:
        callback = f"ProductMenu {product['id']}"
        button_text = f"{product['name']} | {product['price']}{product['currency']} " \
                      f"| {_('Кол-во:', await get_language(message.chat.id))} " \
                      f"{product['amount']} {_('шт.', await get_language(message.chat.id))}"
        markup.add(types.InlineKeyboardButton(button_text, callback_data=callback))

    # Придумать как убрать кнопку ️⬅️ Назад из первого выбора категорий

    if category_id != '1' and category_id != '6':
        markup.row(
            types.InlineKeyboardButton(f"️⬅️ {_('Назад', await get_language(message.chat.id))}",
                                       callback_data=f"BackToOneCategory {category_id}"))
    markup.row(types.InlineKeyboardButton(
        f"⬅️ {_('Назад ко всем категориям', await get_language(message.chat.id))}",
        callback_data="BackToAllCategories"))

    await bot.send_message(message.chat.id, await generate_catalog_template(category_id), reply_markup=markup)


@dp.callback_query_handler(lambda callback: 'BackToOneCategory' in callback.data)
async def back_to_one_category(callback_query: types.CallbackQuery):
    is_admin = False
    if 'Admin' in callback_query.data:
        is_admin = True

    category_id = get_parent_id(telegram_token, callback_query.data.split()[1])

    if category_id is None:
        await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)

        all_categories = get_categories_from_db()
        markup = types.InlineKeyboardMarkup()
        if is_admin:
            markup.add(
                types.InlineKeyboardButton(_("Создать новый товар", await get_language(callback_query.message.chat.id)),
                                           callback_data=f"CreateNewProduct {category_id}"))

        for category in all_categories:
            callback = f"AdminDisplayCategories {category['id']}" if is_admin else f"DisplayCategories {category['id']}"
            markup.add(types.InlineKeyboardButton(category['name'], callback_data=callback))

        await bot.send_message(callback_query.message.chat.id, _("Выберите категорию:",
                                                                 await get_language(callback_query.message.chat.id)),
                               reply_markup=markup)
        return

    content = get_sub_categories_from_db(category_id)
    await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)

    markup = types.InlineKeyboardMarkup()
    if is_admin:
        markup.add(
            types.InlineKeyboardButton(_("Создать новый товар", await get_language(callback_query.message.chat.id)),
                                       callback_data=f"CreateNewProduct {category_id}"))
    for category in content:
        callback = f"AdminDisplayCategories {category['id']}" if is_admin else f"DisplayCategories {category['id']}"
        markup.add(types.InlineKeyboardButton(category['name'], callback_data=callback))

    content = get_products_from_db(category_id, callback_query.from_user.id)
    for product in content:
        callback = f"AdminProductMenu {product['id']}" if is_admin else f"ProductMenu {product['id']}"
        button_text = f"{product['name']} | {product['price']}{product['currency']} " \
                      f"| {_('Кол-во:', await get_language(callback_query.message.chat.id))} " \
                      f"{product['amount']} {_('шт.', await get_language(callback_query.message.chat.id))}"
        markup.add(types.InlineKeyboardButton(button_text, callback_data=callback))

    if is_admin:
        if category_id != 1 and category_id != 6:
            markup.row(
                types.InlineKeyboardButton(f"️⬅️ {_('Назад', await get_language(callback_query.message.chat.id))}",
                                           callback_data=f"AdminBackToOneCategory {category_id}"))
        markup.row(types.InlineKeyboardButton(
            f"⬅️ {_('Назад ко всем категориям', await get_language(callback_query.message.chat.id))}",
            callback_data="AdminBackToAllCategories"))
    else:
        if category_id != 1 and category_id != 6:
            markup.row(
                types.InlineKeyboardButton(f"️⬅️ {_('Назад', await get_language(callback_query.message.chat.id))}",
                                           callback_data=f"BackToOneCategory {category_id}"))
        markup.row(types.InlineKeyboardButton(
            f"⬅️ {_('Назад ко всем категориям', await get_language(callback_query.message.chat.id))}",
            callback_data="BackToAllCategories"))

    await bot.send_message(callback_query.message.chat.id, await generate_catalog_template(category_id),
                           reply_markup=markup,
                           parse_mode="HTML")


@dp.callback_query_handler(lambda callback: 'BackToAllCategories' in callback.data)
async def back_to_all_categories(callback_query: types.CallbackQuery):
    is_admin = False
    if 'Admin' in callback_query.data:
        is_admin = True

    await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)

    all_categories = get_categories_from_db()
    markup = types.InlineKeyboardMarkup()

    for category in all_categories:
        callback = f"AdminDisplayCategories {str(category['id'])}" if is_admin else f"DisplayCategories {str(category['id'])}"
        markup.add(types.InlineKeyboardButton(category['name'], callback_data=callback))

    if is_admin:
        markup.add(types.InlineKeyboardButton(f"️⬅️ {_('Назад', await get_language(callback_query.message.chat.id))}",
                                              callback_data='electProductSearchMethod'))

    await bot.send_message(callback_query.message.chat.id, _("Выберите категорию:",
                                                             await get_language(callback_query.message.chat.id)),
                           reply_markup=markup)


@dp.callback_query_handler(lambda callback: 'ProductMenu' in callback.data)
async def product_menu(callback_query: types.CallbackQuery):
    is_admin = False
    if 'Admin' in callback_query.data:
        is_admin = True

    if is_admin:
        await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
        callback_data = callback_query.data.split(' ')[1]
        data = get_product_from_db(callback_data, callback_query.from_user.id)
        markup = await generate_admin_change_product_markup(data['id'], data['id_category'], callback_query)
        await bot.send_message(callback_query.message.chat.id, await generate_product_template(callback_query.from_user.id, callback_data, 1),
                               reply_markup=markup, parse_mode="HTML")
        return

    callback_data = callback_query.data.split(' ')[1]
    data = get_product_from_db(callback_data, callback_query.from_user.id)
    markup = types.InlineKeyboardMarkup()

    await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    min_value = data['min_count'] if data['min_count'] is not None else 1
    markup = await generate_calculator_selection(data, min_value, callback_query)
    await bot.send_message(callback_query.message.chat.id,
                           await generate_product_template(callback_query.from_user.id, callback_data, min_value),
                           reply_markup=markup, parse_mode="HTML")


async def product_menu_from_message(product_id, message):
    data = get_product_from_db(product_id, message.from_user.id)
    await bot.delete_message(message.chat.id, message.message_id)
    min_value = data['min_count'] if data['min_count'] is not None else 1
    markup = await generate_calculator_selection(data, min_value, message)
    await bot.send_message(message.chat.id,
                           await generate_product_template(message.chat.id, message, min_value),
                           reply_markup=markup, parse_mode="HTML")


@dp.callback_query_handler(lambda callback: 'CalculatorMIN' in callback.data)
async def calculator_min(callback_query: types.CallbackQuery):
    await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    callback_data = callback_query.data.split(' ')
    product_id = callback_data[1]
    data = get_product_from_db(product_id, callback_query.from_user.id)

    min_value = data['min_count'] if data['min_count'] is not None else 1
    markup = await generate_calculator_selection(data, min_value, callback_query)

    await bot.send_message(callback_query.message.chat.id, await generate_product_template(callback_query.from_user.id, product_id, min_value),
                           reply_markup=markup, parse_mode="HTML")


@dp.callback_query_handler(lambda callback: 'CalculatorMAX' in callback.data)
async def calculator_max(callback_query: types.CallbackQuery):
    await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    callback_data = callback_query.data.split(' ')
    product_id = callback_data[1]
    data = get_product_from_db(product_id, callback_query.from_user.id)

    max_value = data['max_count'] if data['max_count'] is not None else data['amount']
    markup = await generate_calculator_selection(data, max_value, callback_query)

    # markup.row(types.InlineKeyboardButton(f"️⬅️ {_('Назад', await get_language(callback_query.message.chat.id))}",
    #                                       callback_data=f"ExitProduct {data['id']}"))
    # markup.row(types.InlineKeyboardButton(
    #     f"⬅️ {_('Назад ко всем категориям', await get_language(callback_query.message.chat.id))}",
    #     callback_data="BackToAllCategories"))

    await bot.send_message(callback_query.message.chat.id, await generate_product_template(callback_query.from_user.id, product_id, max_value),
                           reply_markup=markup, parse_mode="HTML")


@dp.callback_query_handler(lambda callback: 'CalculatorAdd' in callback.data)
async def calculator_add(callback_query: types.CallbackQuery):
    await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    callback_data = callback_query.data.split(' ')
    product_id = callback_data[1]
    amount = int(callback_data[2])
    data = get_product_from_db(product_id, callback_query.from_user.id)

    if amount == data['amount'] or amount == data['max_count']:
        amount -= 1

    markup = await generate_calculator_selection(data, amount + 1, callback_query)

    # markup.row(types.InlineKeyboardButton(f"️⬅️ {_('Назад', await get_language(callback_query.message.chat.id))}",
    #                                       callback_data=f"ExitProduct {data['id']}"))
    # markup.row(types.InlineKeyboardButton(
    #     f"⬅️ {_('Назад ко всем категориям', await get_language(callback_query.message.chat.id))}",
    #     callback_data="BackToAllCategories"))

    await bot.send_message(callback_query.message.chat.id, await generate_product_template(callback_query.from_user.id, product_id, amount + 1),
                           reply_markup=markup, parse_mode="HTML")


@dp.callback_query_handler(lambda callback: 'CalculatorDecrease' in callback.data)
async def calculator_decrease(callback_query: types.CallbackQuery):
    await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    callback_data = callback_query.data.split(' ')
    product_id = callback_data[1]
    amount = int(callback_data[2])
    data = get_product_from_db(product_id, callback_query.from_user.id)

    if amount == 1 or amount == data['min_count']:
        amount += 1

    markup = await generate_calculator_selection(data, amount - 1, callback_query)

    # markup.row(types.InlineKeyboardButton(f"️⬅️ {_('Назад', await get_language(callback_query.message.chat.id))}",
    #                                       callback_data=f"ExitProduct {data['id']}"))
    # markup.row(types.InlineKeyboardButton(
    #     f"⬅️ {_('Назад ко всем категориям', await get_language(callback_query.message.chat.id))}",
    #     callback_data="BackToAllCategories"))

    await bot.send_message(callback_query.message.chat.id, await generate_product_template(callback_query.from_user.id, product_id, amount - 1),
                           reply_markup=markup, parse_mode="HTML")


@dp.callback_query_handler(lambda callback: 'CalculatorCount' in callback.data)
async def calculatorcount(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)

    callback_data = callback_query.data.split(' ')
    product_id = callback_data[1]

    await state.update_data(product_id=product_id)
    await state.set_state(MyStates.product_count_state)

    markup = await generate_product_quantity_selection_back(callback_query.from_user.id)
    template = await generate_product_count_template(callback_query.from_user.id, product_id)
    await bot.send_message(callback_query.from_user.id, template, reply_markup=markup)


@dp.callback_query_handler(lambda callback: 'BackToProduct' in callback.data, state="*")
async def back_to_product(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)

    product_id = (await state.get_data())["product_id"]
    data = get_product_from_db(product_id, callback_query.from_user.id)
    amount = 1

    await state.finish()

    markup = await generate_calculator_selection(data, amount, callback_query)

    await bot.send_message(callback_query.message.chat.id, await generate_product_template(callback_query.from_user.id, product_id, amount),
                           reply_markup=markup, parse_mode="HTML")

@dp.message_handler(state=MyStates.product_count_state)
async def calculatorcount_product_count_state(message: types.Message, state: FSMContext):
    await bot.delete_message(message.chat.id, message.message_id)
    product_id = (await state.get_data())["product_id"]
    data = get_product_from_db(product_id, message.from_user.id)
    try:
       amount = int(message.text)
    except:
        amount = 1
    if data['min_count'] and amount < int(data['min_count']):
        amount = int(data['min_count'])
    elif data['min_count'] and amount > int(data['max_count']):
        amount = int(data['max_count'])
    elif amount > int(data['amount']):
        amount = int(data['amount'])
    elif amount < 1:
        amount = 1

    data = get_product_from_db(product_id, message.from_user.id)

    markup = await generate_calculator_selection(data, amount, callback_query)

    await bot.send_message(message.chat.id, await generate_product_template(message.from_user.id, product_id, amount),
                           reply_markup=markup, parse_mode="HTML")
    await state.finish()


@dp.callback_query_handler(lambda callback: 'ConfirmationProductPurchase' in callback.data)
async def ConfirmationProductPurchase(callback):
    await bot.delete_message(callback.message.chat.id, callback.message.message_id)
    callback.data = callback.data.split(' ')
    productID = callback.data[1]
    count = callback.data[2]
    promo = 1 #callback.data[3]
    time = datetime.now()
    productFromDB = get_product_from_db(productID, callback.from_user.id)
    price = int(count) * productFromDB['price']
    balance_price = price - 0      # сделать функцию, преобразующую промокод в сумму скидки
    add_order_to_db(callback.from_user.id, time, price, count, 'formed', productID, promo, balance_price)
    orderID = get_order_id_from_db(callback.from_user.id, time, price, count, 'formed')['id']
    localization = get_language(callback.from_user.id)
    template, markup = await generate_payment_template('paymentConfirmation', orderID, productFromDB,
                                                       callback.from_user.id, time, price, count, 'formed')

    await bot.send_message(callback.message.chat.id,
                           text=template,
                           reply_markup=markup, parse_mode="HTML")
    return


@dp.callback_query_handler(lambda callback: 'CancelProductPurchase' in callback.data)
async def cancel_product_purchase(callback):
    await bot.delete_message(callback.message.chat.id, callback.message.message_id)
    callback.data = callback.data.split(' ')
    change_order_status_in_db(callback.data[1], 'Cancel')
    await bot.send_message(callback.message.chat.id,
                           text=f"{_('Заказ', await get_language(callback.message.chat.id))}:"
                                f" #<code>{callback.data[1]}</code> "
                                f"{_('был отменен', await get_language(callback.message.chat.id))}",
                           parse_mode="HTML")


@dp.callback_query_handler(lambda callback: 'ExitFromProduct' in callback.data)
async def exit_from_product(callback):
    await bot.delete_message(callback.message.chat.id, callback.message.message_id)
    main_markup = await generate_main_panel_markup(callback.from_user.id)
    await bot.send_message(callback.from_user.id,_("🏘 Меню", await get_language(callback.from_user.id)),
                           reply_markup=main_markup)
    await generate_and_send_default_message(callback.from_user.id,'greetings')


@dp.callback_query_handler(lambda callback: 'PurchaseProduct' in callback.data)
async def PurchaseProduct(callback):
    await bot.delete_message(callback.message.chat.id, callback.message.message_id)
    user = get_user_from_db(callback.from_user.id)
    callback.data = callback.data.split(' ')
    orderID = callback.data[1]
    orderFromDB = get_order_from_db(orderID)
    productID = callback.data[2]
    productFromDB = get_product_from_db(productID, callback.from_user.id)
    count = callback.data[3]
    price = Decimal(callback.data[4])
    markup = types.InlineKeyboardMarkup()
    # Проверить хватает ли денег на балансе
    if user['balance'] < price:
        template = get_template_from_db(f"{user['localization']}/not_enough_balance")
        if template is None:
            template = get_template_from_db(f"en/not_enough_balance")
        template["template"] = template["template"].replace("{AMOUNT}", str(price))
        template["template"] = template["template"].replace("{DONT_HAVE_AMOUNT}", str(price-user['balance']))
        for row in (template["buttons"])["buttons"]:
            markup_row = []
            for button in row:
                markup_row.append(InlineKeyboardButton(button["text"], callback_data=button["action"]))
            markup.row(*markup_row)
        await bot.send_message(callback.message.chat.id,
                               text=template["template"], parse_mode="HTML", reply_markup=markup)
        return ()
    receipt, markup = await generate_payment_template('paymentReceipt',
                                              orderID,
                                              productFromDB,
                                              callback.from_user.id,
                                              orderFromDB['time'],
                                              price,
                                              count,
                                              'Complete')
    await bot.send_message(callback.message.chat.id,
                           text=receipt,
                           parse_mode="HTML",
                           reply_markup=markup)
    balance_increase_in_db(callback.from_user.id, -1 * price)
    # Выдать товар
    product_type = productFromDB['type']
    # УНИКАЛЬНЫЕ
    if product_type == 'uniqueFile' or product_type == "uniqueGift" or product_type == "uniqueProduct":
        products = get_products_for_delivery_from_db(productID, count, orderID, True)
        if product_type == "uniqueGift" or product_type == "uniqueProduct" or product_type == "service":
            for product in products:
                await bot.send_message(callback.from_user.id, product['data'])
        else:
            for product in products:
                file_id = product['data'].split(' ')[1]
                await bot.send_document(callback.from_user.id, file_id)
    # НЕУНИКАЛЬНЫЕ
    if product_type == "nonuniqueFile" or product_type == "nonuniqueProduct" \
            or product_type == "nonuniqueGift" or product_type == "service":
        products = get_products_for_delivery_from_db(productID, 1, orderID, False)
        if product_type == "nonuniqueProduct" or product_type == "nonuniqueGift" or product_type == "service":
            for product in products:
                await bot.send_message(callback.from_user.id, product['data'])
        else:
            for product in products:
                file_id = product['data'].split(' ')[1]
                await bot.send_document(callback.from_user.id, file_id)

                # callback_data = f"PurchaseProduct {orderID} {productID} {count} {price}")
    change_order_status_in_db(orderID, 'Complete')

    if order_notification:
        for admin in admins_users:
            await bot.send_message(admin,
                                   f"[{_('Уведомление о покупке', await get_language(callback.message.chat.id))}]\n"
                                   f"{receipt}", parse_mode="HTML")
    pass


async def generate_admin_change_product_markup(product_id, id_category, message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(_("Редактировать", await get_language(message.from_user.id)),
                                          callback_data=f"AdminChangeProduct {product_id}"))
    markup.add(types.InlineKeyboardButton(_("Добавить товар", await get_language(message.from_user.id)),
                                          callback_data=f"AdminAddProductData {product_id}"))
    markup.add(types.InlineKeyboardButton(_("Выгрузить товар", await get_language(message.from_user.id)),
                                          callback_data=f"AdminDeleteProductData {product_id}"))
    markup.add(types.InlineKeyboardButton(f"️⬅️ {_('Назад', await get_language(message.from_user.id))}",
                                          callback_data=f"AdminExitProduct {id_category}"))
    markup.add(
        types.InlineKeyboardButton(f"️⬅️ {_('Назад ко всем категориям', await get_language(message.from_user.id))}",
                                   callback_data="AdminBackToAllCategories"))
    return markup


@dp.callback_query_handler(lambda callback: 'ExitProduct' in callback.data)
async def exit_product(callback_query: types.CallbackQuery):
    # try:
    isAdmin = False
    if 'Admin' in callback_query.data:
        isAdmin = True
    product_id = callback_query.data.split(' ')[1]
    data = get_product_from_db(product_id, callback_query.from_user.id)
    content = get_sub_categories_from_db(data['id_category'])

    await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    markup = types.InlineKeyboardMarkup()
    if isAdmin:
        markup.add(
            types.InlineKeyboardButton(_("Создать новый товар", await get_language(callback_query.message.chat.id)),
                                       callback_data=f"CreateNewProduct {data['id_category']}"))

    for category in content:
        callback = f"AdminDisplayCategories {category['id']}" if isAdmin else f"DisplayCategories {category['id']}"
        markup.add(types.InlineKeyboardButton(category['name'], callback_data=callback))

    products = get_products_from_db(product_id, callback_query.from_user.id)
    for product in products:
        callback = f"AdminProductMenu {product['id']}" if isAdmin else f"ProductMenu {product['id']}"
        button_text = f"{product['name']} | {product['price']}{product['currency']} " \
                      f"| {_('Кол-во:', await get_language(callback_query.message.chat.id))} {product['amount']} " \
                      f"{_('шт.', await get_language(callback_query.message.chat.id))}"
        markup.add(types.InlineKeyboardButton(button_text, callback_data=callback))

    if isAdmin:
        if content[0]['parent_id'] != 1 and content[0]['parent_id'] != 6:
            markup.row(
                types.InlineKeyboardButton(f"️⬅️ {_('Назад', await get_language(callback_query.message.chat.id))}",
                                           callback_data=f"AdminBackToOneCategory {product_id}"))
        markup.row(
            types.InlineKeyboardButton(
                f"⬅️ {_('Назад ко всем категориям', await get_language(callback_query.message.chat.id))}",
                callback_data="AdminBackToAllCategories"))
    else:
        if content[0]['parent_id'] != 1 and content[0]['parent_id'] != 6:
            markup.row(
                types.InlineKeyboardButton(f"️⬅️ {_('Назад', await get_language(callback_query.message.chat.id))}",
                                           callback_data=f"BackToOneCategory {product_id}"))
        markup.row(types.InlineKeyboardButton(
            f"⬅️ {_('Назад ко всем категориям', await get_language(callback_query.message.chat.id))}",
            callback_data="BackToAllCategories"))
    template = await generate_catalog_template(product_id)
    await bot.send_message(callback_query.message.chat.id, template, reply_markup=markup, parse_mode="HTML")
    # except Exception as ex:
    #     print(ex)


# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------Панель администратора-----------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
@dp.callback_query_handler(lambda callback: 'AdminSelectProductSearchMethod' in callback.data)
async def AdminSelectProductSearchMethod(callback):
    await bot.delete_message(callback.message.chat.id, callback.message.message_id)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(_('Смотреть каталог', await get_language(callback.message.chat.id)),
                                          callback_data=f'AdminCatalogViewingMainCatalog'))
    markup.add(types.InlineKeyboardButton(_('Искать по имени', await get_language(callback.message.chat.id)),
                                          callback_data=f'AdminProductSearchByName'))
    markup.add(types.InlineKeyboardButton(_('Я знаю ID товара', await get_language(callback.message.chat.id)),
                                          callback_data=f'AdminProductSearchByID'))
    markup.add(types.InlineKeyboardButton(f"⬅️ {_('Назад', await get_language(callback.message.chat.id))}",
                                          callback_data=f'backToAdminMenu'))

    await bot.send_message(callback.from_user.id, "Как будем искать товар?",
                           reply_markup=markup, parse_mode="HTML")


@dp.callback_query_handler(lambda callback: 'AdminProductSearchByName' in callback.data)
async def AdminProductSearchByName(callback, state: FSMContext):
    await callback.answer("")
    await bot.delete_message(callback.message.chat.id, callback.message.message_id)
    await state.set_state(MyStates.searchByName.state)
    await bot.send_message(callback.message.chat.id,
                           _('Введите название товара для его поиска:', await get_language(callback.message.chat.id)))


@dp.callback_query_handler(lambda callback: 'AdminCatalogViewingMainCatalog' in callback.data)
async def AdminCatalogViewingMainCatalog(callback):
    await bot.delete_message(callback.message.chat.id, callback.message.message_id)
    allCategories = get_categories_from_db()
    markup = types.InlineKeyboardMarkup()
    for category in allCategories:
        markup.add(
            types.InlineKeyboardButton(category['name'], callback_data=f"AdminDisplayCategories {category['id']}"))
    markup.add(types.InlineKeyboardButton(f"⬅️ {_('Назад', await get_language(callback.message.chat.id))}",
                                          callback_data=f'AdminSelectProductSearchMethod'))
    await bot.send_message(callback.message.chat.id,
                           _('Выберите категорию:', await get_language(callback.message.chat.id)),
                           reply_markup=markup)


@dp.callback_query_handler(lambda callback: 'AdminProductSearchByID' in callback.data)
async def AdminProductSearchByID(callback, state: FSMContext):
    await callback.answer("")
    await bot.delete_message(callback.message.chat.id, callback.message.message_id)
    await state.set_state(MyStates.searchByID.state)
    await bot.send_message(callback.message.chat.id,
                           _('Введите ID товара. Если хотите выйти из поиска введите -Завершить-.',
                             await get_language(callback.message.chat.id)))


@dp.callback_query_handler(lambda callback: 'AdminChangeProduct' in callback.data)
async def AdminChangeProduct(callback):
    await callback.answer("")
    await bot.delete_message(callback.message.chat.id, callback.message.message_id)
    callback.data = callback.data.split(' ')[1]
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(_('Изменить название', await get_language(callback.message.chat.id)),
                                          callback_data=f'AdminChangeNameProduct {callback.data}'))
    markup.add(types.InlineKeyboardButton(_('Изменить описание', await get_language(callback.message.chat.id)),
                                          callback_data=f'AdminChangeDescProduct {callback.data}'))
    markup.add(types.InlineKeyboardButton(_('Изменить цену', await get_language(callback.message.chat.id)),
                                          callback_data=f'AdminChangePriceProduct {callback.data}'))
    markup.add(types.InlineKeyboardButton(f"⬅️ {_('Назад', await get_language(callback.message.chat.id))}",
                                          callback_data=f'AdminProductMenu {callback.data}'))
    await bot.send_message(callback.message.chat.id, await generate_product_template(callback.from_user.id, callback.data, 1),
                           reply_markup=markup,
                           parse_mode="HTML")


@dp.callback_query_handler(lambda callback: 'AdminChangeNameProduct' in callback.data)
async def AdminChangeNameProduct(callback, state: FSMContext):
    await callback.answer("")
    await state.set_state(MyStates.adminChangeNameProduct.state)
    await state.update_data(value=callback.data.split(' ')[1])
    await bot.send_message(callback.message.chat.id,
                           _('Введите новое название товара', await get_language(callback.message.chat.id)),
                           parse_mode="HTML")


@dp.callback_query_handler(lambda callback: 'AdminChangeDescProduct' in callback.data)
async def AdminChangeDescProduct(callback, state: FSMContext):
    await callback.answer("")
    await state.set_state(MyStates.adminChangeDescProduct.state)
    await state.update_data(value=callback.data.split(' ')[1])
    await bot.send_message(callback.message.chat.id,
                           _('Введите новое описание товара', await get_language(callback.message.chat.id)),
                           parse_mode="HTML")


@dp.callback_query_handler(lambda callback: 'AdminChangePriceProduct' in callback.data)
async def AdminChangePriceProduct(callback, state: FSMContext):
    await callback.answer("")
    await state.set_state(MyStates.adminChangePriceProduct.state)
    await state.update_data(value=callback.data.split(' ')[1])
    await bot.send_message(callback.message.chat.id,
                           _('Введите новую цену товара', await get_language(callback.message.chat.id)),
                           parse_mode="HTML")


@dp.callback_query_handler(lambda callback: 'AdminAddProductData' in callback.data)
async def AdminAddProductData(callback, state: FSMContext):
    await callback.answer("")
    product = get_product_from_db(callback.data.split(' ')[1], callback.from_user.id)
    if product['type'] == 'uniqueProduct':
        await bot.send_message(callback.message.chat.id,
                               _('Выбранный товар является <b>уникальным товаром</b>\n'
                                 'Для его пополнения требуется отправить либо:\n'
                                 '1. Сообщение, где каждая строка - 1 товар\n'
                                 '2. txt файл, где каждая строка - 1 товар',
                                 await get_language(callback.message.chat.id)),
                               parse_mode="HTML")
        await state.set_state(MyStates.adminAddProductDataUniqueP.state)
        await state.update_data(value=callback.data.split(' ')[1])
    if product['type'] == 'nonuniqueProduct':
        await bot.send_message(callback.message.chat.id,
                               _('Выбранный товар является <b>неуникальным товаром</b>\n'
                                 'Для его пополнения требуется отправить: \n'
                                 'Сообщение, которое будет являться товаром',
                                 await get_language(callback.message.chat.id)),
                               parse_mode="HTML")
        await state.set_state(MyStates.adminAddProductDataNonuniqueP.state)
        await state.update_data(value=callback.data.split(' ')[1])
    if product['type'] == 'uniqueFile':
        await bot.send_message(callback.message.chat.id,
                               _('Выбранный товар является <b>уникальным файлом</b>\n'
                                 'Для его пополнения требуется отправить: \n'
                                 'Файлы, которые будут являться товаром.\n'
                                 'Для завершения отправьте -Завершить-', await get_language(callback.message.chat.id)),
                               parse_mode="HTML")
        await state.set_state(MyStates.adminAddProductDataUniqueF.state)
        await state.update_data(value=callback.data.split(' ')[1])
    if product['type'] == 'nonuniqueFile':
        await bot.send_message(callback.message.chat.id,
                               _("Выбранный товар является <b>неуникальным файлом</b>\n"
                                 "Для его пополнения требуется отправить: \n"
                                 "1 файл, который будет являться товаром.\n"
                                 "Для отмены отправьте -Завершить-", await get_language(callback.message.chat.id)),
                               parse_mode="HTML")
        await state.set_state(MyStates.adminAddProductDataNonuniqueF.state)
        await state.update_data(value=callback.data.split(' ')[1])
    if product['type'] == 'service':
        await bot.send_message(callback.message.chat.id,
                               _("Выбранный товар является <b>услугой</b>\n"
                                 "Для его пополнения требуется отправить: \n"
                                 "Cообщение, которое будет являться товаром.\n"
                                 "Для отмены отправьте -Завершить-", await get_language(callback.message.chat.id)),
                               parse_mode="HTML")
        await state.set_state(MyStates.adminAddProductDataService.state)
        await state.update_data(value=callback.data.split(' ')[1])
    if product['type'] == 'uniqueGift':
        await bot.send_message(callback.message.chat.id,
                               _('Выбранный товар является <b>уникальным подарком</b>\n'
                                 'Для его пополнения требуется отправить либо:\n'
                                 '1. Сообщение, где каждая строка - 1 товар\n'
                                 '2. txt файл, где каждая строка - 1 товар',
                                 await get_language(callback.message.chat.id)),
                               parse_mode="HTML")
        await state.set_state(MyStates.adminAddProductDataUniqueGift.state)
        await state.update_data(value=callback.data.split(' ')[1])
    if product['type'] == 'nonuniqueGift':
        await bot.send_message(callback.message.chat.id,
                               _('Выбранный товар является <b>неуникальным товаром</b>\n'
                                 'Для его пополнения требуется отправить: \n'
                                 'Сообщение, которое будет являться товаром',
                                 await get_language(callback.message.chat.id)),
                               parse_mode="HTML")
        await state.set_state(MyStates.adminAddProductDataNonuniqueGift.state)
        await state.update_data(value=callback.data.split(' ')[1])


@dp.callback_query_handler(lambda callback: 'AdminDeleteProductData' in callback.data)
async def AdminDeleteProductData(callback, state: FSMContext):
    await callback.answer("")
    product = get_product_from_db(callback.data.split(' ')[1], callback.from_user.id)
    await bot.send_message(callback.message.chat.id,
                           f"{_('Отправьте кол-во товара, которое хотите выгрузить', await get_language(callback.message.chat.id))}\n"
                           f"{_('В наличии:', await get_language(callback.message.chat.id))} <b>{product['amount']}</b>\n"
                           f"{_('Чтобы выгрузить всё отправьте *', await get_language(callback.message.chat.id))}",
                           parse_mode="HTML")
    await state.set_state(MyStates.adminDeleteProductData.state)
    await state.update_data(value=callback.data.split(' ')[1], type=str(product['type']))


@dp.callback_query_handler(lambda callback: 'CreateNewProduct' in callback.data)
async def CreateNewProduct(callback, state: FSMContext):
    await callback.answer("")
    await bot.delete_message(callback.message.chat.id, callback.message.message_id)
    data = callback.data.split(' ')
    category_id = data[1]
    if len(data) == 2:
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton(_('Уникальный товар', await get_language(callback.message.chat.id)),
                                       callback_data=f'CreateNewProduct {category_id} uniqueP'))
        markup.add(types.InlineKeyboardButton(_('Неуникальный товар', await get_language(callback.message.chat.id)),
                                              callback_data=f'CreateNewProduct {category_id} nonuniqueP'))
        markup.add(
            types.InlineKeyboardButton(_('Уникальный файл', await get_language(callback.message.chat.id)),
                                       callback_data=f'CreateNewProduct {category_id} uniqueF'))
        markup.add(
            types.InlineKeyboardButton(_('Неуникальный файл', await get_language(callback.message.chat.id)),
                                       callback_data=f'CreateNewProduct {category_id} nonuniqueF'))
        markup.add(types.InlineKeyboardButton(_('Услуга', await get_language(callback.message.chat.id)),
                                              callback_data=f'CreateNewProduct {category_id} service'))
        markup.add(types.InlineKeyboardButton(_('Уникальный подарок', await get_language(callback.message.chat.id)),
                                              callback_data=f'CreateNewProduct {category_id} uniqueGift'))
        markup.add(types.InlineKeyboardButton(_('Неуникальный подарок', await get_language(callback.message.chat.id)),
                                              callback_data=f'CreateNewProduct {category_id} nonuniqueGift'))
        markup.add(types.InlineKeyboardButton(
            _('Отмена', await get_language(callback.message.chat.id)),
            callback_data=f'AdminDisplayCategories {category_id}'))
        await bot.send_message(callback.message.chat.id,
                               _('Выберите тип товара:', await get_language(callback.message.chat.id)),
                               reply_markup=markup,
                               parse_mode="HTML")
    else:
        await bot.send_message(callback.message.chat.id,
                               _('Введите название товара:', await get_language(callback.message.chat.id)),
                               parse_mode="HTML")
        await state.set_state(MyStates.CreateNewProductSelectName.state)
        await state.update_data(id_category=data[1])
        await state.update_data(type=data[2])

async def send_test_greeting_message(admin, lang):
    try:
        template, markup, settings = await generate_default_template(admin, 'greetings', isTest=True, lang=lang)
        if settings is not None:
            preview = settings['preview']
            protected = settings['protected']
            silent = settings['silent']
            await bot.send_message(admin, text=template, reply_markup=markup, parse_mode='HTML',
                                   disable_web_page_preview=preview,
                                   protect_content=protected,
                                   disable_notification=silent
                                   )
        else:
            await bot.send_message(admin, text=template, reply_markup=markup, parse_mode='HTML')
    except Exception:
        pass
        # print(f"{admin} не может получить тестовое сообщение. Он не зарегистрирован в данном боте.")


#    await message.answer(template,reply_markup=markup, parse_mode='HTML')

async def action_send_message(action, mailing_id=None):
    if "date" in action:
        try:
            delete_mailings_planned_from_db(action["mailing_id"])
        except:
            pass
    success = 0
    if not action["users"]:
        users = active_users.copy()
    else:
        users = action["users"]
    mailing_name = None
    if "mailing_name" in action:
        mailing_name = action["mailing_name"]
    for user_id in users:
        if int(user_id) in active_users:
            try:
                template = action["template"]
                template["template"] = await replace_tags_in_template(user_id, template["template"], "greetings")
                if template["is_reply"]:
                    markup = await parse_reply_keyboard_markup(template)
                else:
                    markup = await parse_inline_keyboard_markup(template)
                if template["media"] is not None:
                    try:
                        media = types.MediaGroup()
                        media_group = []
                        for current_media in template["media"]:
                            from_website = False
                            if ':8080/api/v1' in current_media:
                                current_media = current_media.replace(':8080/api/v1', '')
                                from_website = True
                            type = current_media.split('.')[-1]
                            if type in ['mp4', 'mov']:
                                if from_website:
                                    media_group.append(InputMediaVideo(current_media, type='video'))
                                else:
                                    media.attach_video(types.InputFile(current_media))
                            if type == 'gif':
                                if from_website:
                                    media_group.append(InputMediaAnimation(current_media))
                                else:
                                    media.attach_video(types.InputFile(current_media))
                            if type in ['png', 'jpeg', 'jpg']:
                                if from_website:
                                    media_group.append(InputMediaPhoto(current_media))
                                else:
                                    media.attach_photo(types.InputFile(current_media))
                        if media_group:
                            await bot.send_media_group(user_id, media_group)
                        if media:
                            await bot.send_media_group(chat_id=user_id, media=media)
                    except Exception as e:
                        if "bot was blocked by the user" in str(e):
                            await update_user_status(user_id, "")
                        else:
                            print(e)
                await bot.send_message(user_id, text=template["template"], reply_markup=markup, parse_mode='HTML',
                                       disable_web_page_preview=template["settings"]["preview"],
                                       protect_content=template["settings"]["protected"],
                                       disable_notification=template["settings"]["silent"])
                success += 1
            except Exception as e:
                if "bot was blocked by the user" in str(e):
                    await update_user_status(user_id, "inactive")
                else:
                    print(e)
    insert_mailings_history(action["users"], json.dumps(action["template"], ensure_ascii=False), success, mailing_name)


async def action_add_manager(action):
    for user_id in action["users"]:
        await update_user_status(user_id, "manager")

async def action_delete_manager(action):
    for user_id in action["users"]:
        await update_user_status(user_id, "unverified")

async def process_action():
    actions = get_actions_from_db()
    for action in actions:
        action = action['action']
        if action['name'] == 'send_test_message':
            admins = get_admin_list()
            for admin in admins:
                path = action['path'].split('/')
                lang = path[0]
                name = path[1]
                if name == 'greetings':
                    await send_test_greeting_message(admin, lang)
        if action['name'] == 'send_messages':
            await action_send_message(action)
        if action['name'] == 'add_manager':
            await action_add_manager(action)
        if action['name'] == 'delete_manager':
            await action_delete_manager(action)

async def process_mailing():
    mailings = get_mailings_planned_from_db(last_mailing_id[0])
    for mailing in mailings:
        last_mailing_id[0] = mailing["mailing_id"]
        scheduler.add_job(action_send_message, 'date',
                          run_date=mailing["date"], args=[mailing])



async def check_enable_bot():
    global bot_enabled
    current_status = get_status_bot_from_db()
    if bot_enabled != current_status:
        bot_enabled = current_status

scheduler = AsyncIOScheduler()
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, filename="logs.log", filemode="a",
                        format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger('apscheduler.executors.default').propagate = False
    f = ContextFilter()
    logging.getLogger('aiogram.contrib.middlewares.logging').addFilter(f)
    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

    scheduler.start()
    scheduler.add_job(process_action, "interval", seconds=5)
    scheduler.add_job(process_mailing, "interval", seconds=5)
    scheduler.add_job(check_enable_bot, "interval", seconds=10)
    executor.start_polling(dp, skip_updates=True)
