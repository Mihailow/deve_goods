from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import callback_query, InputMediaVideo, InputMediaAnimation, InputMediaPhoto

from generate_product_quantity_selection import generate_product_quantity_selection, generate_calculator_selection, \
    generate_without_quantity_with_confirmation
from generate_template import generate_products_availability_template, generate_profile_template, \
    generate_history_order_template, generate_catalog_template, generate_product_template

from misc import dp, bot,admins_users , message_action_dictionary, name_and_action_reply_button, input_field_placeholder, \
    generate_default_template, replace_tags_in_template, parse_reply_keyboard_markup, parse_inline_keyboard_markup
from modules.admin_module.generate_template import generate_admin_menu_template
from modules.admin_module.keyboards import get_admin_keyboards_for_message_handler
from modules.basket_module.handlers import get_basket
from postgres.commands_to_db import get_categories_from_db, get_language, get_sub_categories_from_db, \
    get_products_from_db, get_product_from_db, get_user_from_db
from states import MyStates
from translations import _

@dp.callback_query_handler(lambda callback: 'action_handler_products_availability' in callback.data)
async def action_handler_products_availability(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer("")
    template, pages, page = await generate_products_availability_template(callback_query)
    if pages == 1:
        await bot.send_message(callback_query.from_user.id, template)
        return
    markup = types.InlineKeyboardMarkup()
    btns = []
    btns.append(types.InlineKeyboardButton("⬅️", callback_data=f"products_availability_page_back"))
    btns.append(types.InlineKeyboardButton(f"{page}/{pages}", callback_data=f"nothing"))
    btns.append(types.InlineKeyboardButton("➡️", callback_data=f"products_availability_page_next"))
    markup.row(*btns)
    await bot.send_message(callback_query.from_user.id, template, reply_markup=markup)
    await state.update_data(products_availability_page=page)

@dp.callback_query_handler(text_startswith = 'products_availability_page_')
async def action_products_availability_page_(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer("")
    page_action = callback_query.data.replace("products_availability_page_", "")
    page = (await state.get_data())["products_availability_page"]
    if page_action == "back":
        if page > 1:
            page -= 1
    if page_action == "next":
        page += 1
    await callback_query.answer("")
    template, pages, page = await generate_products_availability_template(callback_query, page)
    markup = types.InlineKeyboardMarkup()
    btns = []
    btns.append(types.InlineKeyboardButton("⬅️", callback_data=f"products_availability_page_back"))
    btns.append(types.InlineKeyboardButton(f"{page}/{pages}", callback_data=f"nothing"))
    btns.append(types.InlineKeyboardButton("➡️", callback_data=f"products_availability_page_next"))
    markup.row(*btns)
    await bot.send_message(callback_query.from_user.id, template, reply_markup=markup)


@dp.callback_query_handler(lambda callback: 'action_handler_all_categories' in callback.data)
async def action_handler_all_categories(callback_query: types.CallbackQuery):
    await callback_query.answer("")
    all_categories = get_categories_from_db()
    markup = types.InlineKeyboardMarkup()
    for category in all_categories:
        markup.add(
            types.InlineKeyboardButton(category['name'], callback_data=f"DisplayCategories {category['id']}"))
    await bot.send_message(callback_query.from_user.id,
                           f"{_('Выберите категорию', await get_language(callback_query.from_user.id))}",
                           reply_markup=markup)

@dp.callback_query_handler(lambda callback: 'action_handler_referral_system' in callback.data)
async def action_handler_referral_system(callback_query: types.CallbackQuery):
    await callback_query.answer("")
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton(_('История начислений', await get_language(callback_query.from_user.id)),
                                   callback_data='RefHistory'))
    markup.add(types.InlineKeyboardButton(_('Рефералы', await get_language(callback_query.from_user.id)),
                                          callback_data='RefList'))
    markup.add(types.InlineKeyboardButton(_('Реферальная ссылка отдельным сообщением',
                                            await get_language(callback_query.from_user.id)),
                                          callback_data='RefOneMessage'))
    await bot.send_message(callback_query.from_user.id,
                           f"{_('В боте включена реферальная система. Приглашайте друзей изарабатывайте на этом! Вы будете получать: 10% от каждой покупки вашего реферала. Ваша реферальная ссылка', await get_language(callback_query.from_user.id))}\n https://t.me/ShopWithoutBasketBot/start={callback_query.from_user.id}",
                           reply_markup=markup)

@dp.callback_query_handler(lambda callback: 'action_handler_profile' in callback.data)
async def action_handler_profile(callback_query: types.CallbackQuery):
    await callback_query.answer("")
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(_('История заказов',
                                            await get_language(callback_query.from_user.id)),
                                          callback_data='OrderHistory'))
    markup.add(types.InlineKeyboardButton(_('Реферальная система',
                                            await get_language(callback_query.from_user.id)),
                                          callback_data='ReferralSystem'))
    markup.add(types.InlineKeyboardButton(_('Активировать купон',
                                            await get_language(callback_query.from_user.id)),
                                          callback_data='ActivateCoupon'))
    markup.add(types.InlineKeyboardButton(_('Пополнить баланс',
                                            await get_language(callback_query.from_user.id)),
                                          callback_data='IncreaseBalanceGetAmount'),
               types.InlineKeyboardButton(_('История пополнений',
                                            await get_language(callback_query.from_user.id)),
                                          callback_data='PaymentsHistory'))
    markup.add(types.InlineKeyboardButton("Favourit", callback_data='getFavouriteGoods'))
    markup.add(types.InlineKeyboardButton(_('Изменить язык',
                                            await get_language(callback_query.from_user.id)),
                                          callback_data='ChangeLanguage'))
    await bot.send_animation(callback_query.message.chat.id, animation='https://i.yapx.cc/VakAF.gif',
                             caption=await generate_profile_template(callback_query.from_user.id),
                             reply_markup=markup)


@dp.callback_query_handler(lambda callback: 'action_handler_about_service' in callback.data)
async def action_handler_about_service(callback_query: types.CallbackQuery):
    action = callback_query.data.replace('action_handler_','')
    await callback_query.answer("")
    template, markup = await generate_default_template(callback_query.from_user.id, action)
    await bot.send_message(callback_query.from_user.id,template, reply_markup=markup)

@dp.callback_query_handler(lambda callback: 'action_handler_rules' in callback.data)
async def action_handler_rules(callback_query: types.CallbackQuery):
    action = callback_query.data.replace('action_handler_', '')
    await callback_query.answer("")
    template, markup = await generate_default_template(callback_query.from_user.id, action)
    await bot.send_message(callback_query.from_user.id,template, reply_markup=markup)

@dp.callback_query_handler(lambda callback: 'action_handler_about_store' in callback.data)
async def action_handler_about_store(callback_query: types.CallbackQuery):
    action = callback_query.data.replace('action_handler_', '')
    await callback_query.answer("")
    template, markup = await generate_default_template(callback_query.from_user.id, action)
    await bot.send_message(callback_query.from_user.id,template, reply_markup=markup)

@dp.callback_query_handler(lambda callback: 'action_handler_help' in callback.data)
async def action_handler_help(callback_query: types.CallbackQuery):
    action = callback_query.data.replace('action_handler_', '')
    await callback_query.answer("")
    template, markup = await generate_default_template(callback_query.from_user.id, action)
    await bot.send_message(callback_query.from_user.id,template, reply_markup=markup)

@dp.callback_query_handler(lambda callback: 'action_handler_order_history' in callback.data)
async def action_handler_order_history(callback_query: types.CallbackQuery):
    await callback_query.answer("")
    template, orders_amount = await generate_history_order_template(callback_query.from_user.id, 1)
    markup = types.InlineKeyboardMarkup()
    if orders_amount > 3:
        markup.add(
            types.InlineKeyboardButton(f"{_('Вперёд', await get_language(callback_query.from_user.id))}➡️",
                                       callback_data=f'OrdHistNextPage 2'))
        markup.add(
            types.InlineKeyboardButton(f"{_('В конец', await get_language(callback_query.from_user.id))}➡️",
                                       callback_data=f'OrdHistPastPage {orders_amount // 3 + 1}'))
    await callback_query.message.answer(template, reply_markup=markup)

@dp.callback_query_handler(lambda callback: 'action_handler_activate_coupon' in callback.data)
async def action_handler_activate_coupon(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer("")
    await state.set_state(MyStates.activateCoupon.state)
    await callback_query.message.answer(f"{_('Введите промокод', await get_language(callback_query.from_user.id))}: ",
                         parse_mode="HTML")

@dp.callback_query_handler(lambda callback: 'action_handler_admin' in callback.data)
async def action_handler_admin(callback_query: types.CallbackQuery):
    await callback_query.answer("")
    if callback_query.from_user.id not in admins_users:
        await callback_query.message.answer(
            _('К сожалению, вы не являетесь администратором', await get_language(callback_query.from_user.id)))
        return
    markup = await get_admin_keyboards_for_message_handler(callback_query.from_user.id)
    await callback_query.message.answer(await generate_admin_menu_template(callback_query.message), parse_mode="HTML",
                         reply_markup=markup)

@dp.callback_query_handler(lambda callback: 'action_handler_message' in callback.data)
async def action_handler_message(callback_query: types.CallbackQuery):
    data = callback_query.data.replace('action_handler_message ','')
    await callback_query.answer("")
    await callback_query.message.answer(message_action_dictionary[data], parse_mode="HTML")

@dp.callback_query_handler(lambda callback: 'action_handler_basket' in callback.data)
async def action_handler_basket(callback_query: types.CallbackQuery):
    await callback_query.answer("")
    await get_basket(callback_query.from_user.id)

@dp.callback_query_handler(lambda callback: 'action_handler_select_category' in callback.data)
async def action_handler_select_category(callback_query: types.CallbackQuery):
    data = callback_query.data.replace('action_handler_select_category ', '')
    await callback_query.answer("")
    await display_categories_from_message(message_action_dictionary[data], callback_query.message)

@dp.callback_query_handler(lambda callback: 'action_handler_select_product' in callback.data)
async def action_handler_select_product(callback_query: types.CallbackQuery):
    data = callback_query.data.replace('action_handler_select_product ', '')
    await callback_query.answer("")
    await product_menu_from_message(message_action_dictionary[data], callback_query.message)

async def display_categories_from_message(category_id,message):
    # Отображение каталога, когда передаётся в callback id каталога
    categories = get_sub_categories_from_db(category_id)
    await bot.delete_message(message.chat.id, message.message_id)
    markup = types.InlineKeyboardMarkup()

    for category in categories:
        callback = f"DisplayCategories {category['id']}"
        markup.add(types.InlineKeyboardButton(category['name'], callback_data=callback))

    # Отображение товара каталога, когда передаётся в callback id каталога
    products = get_products_from_db(category_id, message.chat.id)
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

    await bot.send_message(message.chat.id, await generate_catalog_template(category_id),reply_markup=markup)

async def product_menu_from_message(product_id, message):
    data = get_product_from_db(product_id, message.chat.id)
    await bot.delete_message(message.chat.id, message.message_id)
    min_value = data['min_count'] if data['min_count'] is not None else 1
    markup = await generate_calculator_selection(data, min_value, message)
    await bot.send_message(message.chat.id,
                           await generate_product_template(message.chat.id, product_id, min_value),
                           reply_markup=markup, parse_mode="HTML")

async def action_send_message(action):
    for user_id in action["users"]:
        template = action["template"]
        template["template"] = await replace_tags_in_template(user_id, template["template"], "greetings")
        if template["is_reply"]:
            markup = await parse_reply_keyboard_markup(template)
        else:
            markup = await parse_inline_keyboard_markup(template)
        if template["media"] is not None:
            try:
                media_group = []
                for current_media in template["media"]:
                    current_media = current_media.replace(':8080/api/v1', '')
                    type = current_media.split('.')[-1]
                    if type in ['mp4', 'mov']:
                        media_group.append(InputMediaVideo(current_media, type='video'))
                    if type == 'gif':
                        media_group.append(InputMediaAnimation(current_media))
                    if type in ['png', 'jpeg']:
                        media_group.append(InputMediaPhoto(current_media))
                await bot.send_media_group(user_id, media_group)
            except Exception as Ex:
                print(Ex)
        await bot.send_message(user_id, text=template["template"], reply_markup=markup, parse_mode='HTML',
                               disable_web_page_preview=template["settings"]["preview"],
                               protect_content=template["settings"]["protected"], disable_notification=template["settings"]["silent"])