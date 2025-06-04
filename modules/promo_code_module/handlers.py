from aiogram.dispatcher import FSMContext
from main import MyStates, bot, dp
from translations import _
from aiogram import types



from datetime import datetime
from _decimal import Decimal
from modules.promo_code_module.commands_to_db import *
from postgres.commands_to_db import get_language, get_product_from_db



@dp.callback_query_handler(lambda callback: 'ActivateCoupon' in callback.data)
async def ActivateCoupon(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer("")
    await state.set_state(MyStates.activateCoupon.state)
    await bot.send_message(callback_query.message.chat.id,
                           f"{_('Введите промокод', await get_language(callback_query.message.chat.id))}: ",
                           parse_mode="HTML")


@dp.message_handler(state=MyStates.activateCoupon)
async def write_coupon(message, state: FSMContext):
    coupon_text = message.text
    promo_code = get_promocode(coupon_text)
    await state.reset_state()
    if promo_code is None:
        await bot.send_message(message.chat.id,
                               _('Данный купон не обнаружен', await get_language(message.from_user.id)))
    else:
        promo_code_id = promo_code['id']
        activated = promo_code['activated']
        type = promo_code['type']
        sum = promo_code['sum']
        remaining_uses = promo_code['remaining_uses']
        for_new_users = promo_code['for_new_users']
        repeat = promo_code['repeat']
        lifetime = promo_code['lifetime']
        name = promo_code['name']

        if activated or type != "add_money" or remaining_uses < 1 or datetime.now() < lifetime:
            await bot.send_message(message.chat.id,
                                   _('Данный купон недействителен', await get_language(message.from_user.id)))
            return

        if for_new_users:
            if not check_new_user(message.chat.id):
                await bot.send_message(message.chat.id,
                                       _('Данный купон действует только для новых пользователей',
                                         await get_language(message.from_user.id)))
                return
        if not repeat:
            if check_repeat(message.chat.id, promo_code_id):
                await bot.send_message(message.chat.id,
                                       _('Данный купон действует только 1 раз',
                                         await get_language(message.from_user.id)))
                return
        add_balance(message.from_user.id, sum)
        save_in_history(message.from_user.id, sum, "Top-up", datetime.now(), promo_code_id)
        if remaining_uses is not None:
            reduce_remaining_uses_promo_code(promo_code_id)
        await bot.send_message(message.chat.id,
                               f"Промокод {name} был успешно активирован! Баланс пополнен на {round(sum, 2)}.")


@dp.callback_query_handler(lambda callback: 'promo_code_during_purchase' in callback.data)
async def promo_code_during_purchase(callback, state: FSMContext):
    await bot.delete_message(callback.message.chat.id, callback.message.message_id)
    await callback.answer("")
    callback.data = callback.data.split(' ')
    orderID = callback.data[1]
    productID = callback.data[2]
    count = callback.data[3]
    price = Decimal(callback.data[4])
    await state.set_state(MyStates.promo_code_during_purchase_state.state)
    await state.update_data(orderID=orderID, productID=productID, count=count, price=price)
    await bot.send_message(callback.message.chat.id,
                           f"{_('Введите промокод', await get_language(callback.message.chat.id))}: ",
                           parse_mode="HTML")


@dp.message_handler(state=MyStates.promo_code_during_purchase_state)
async def promo_code_during_purchase2(message, state: FSMContext):
    coupon_text = message.text
    promo_code = get_promocode(coupon_text)
    if promo_code is None:
        await bot.send_message(message.chat.id,
                               _('Данный купон не обнаружен', await get_language(message.from_user.id)))
    else:
        promo_code_id = promo_code['id']
        activated = promo_code['activated']
        type = promo_code['type']
        sum = promo_code['sum']
        remaining_uses = promo_code['remaining_uses']
        for_new_users = promo_code['for_new_users']
        repeat = promo_code['repeat']
        lifetime = promo_code['lifetime']
        name = promo_code['name']
        min_sum = promo_code['min_sum']

        order_data = await state.get_data()
        print(order_data)
        print(type)

        if activated  or remaining_uses < 1 or datetime.now() < lifetime:
            await bot.send_message(message.chat.id,
                                   _('Данный купон недействителен', await get_language(message.from_user.id)))
            return

        if for_new_users:
            if not check_new_user(message.chat.id):
                await bot.send_message(message.chat.id,
                                       _('Данный купон действует только для новых пользователей',
                                         await get_language(message.from_user.id)))
                return

        if not repeat:
            if check_repeat(message.chat.id, promo_code_id):
                await bot.send_message(message.chat.id,
                                       _('Данный купон действует только 1 раз',
                                         await get_language(message.from_user.id)))
                return

        if type == "add_money":
            add_balance(message.from_user.id, sum)
            save_in_history(message.from_user.id, sum, "Top-up", datetime.now(), promo_code_id)
            if remaining_uses is not None:
                await bot.send_message(message.chat.id,
                                       f"Промокод {name} был успешно активирован! Баланс пополнен на {round(sum, 2)}.")

        if type == "percentage_discount" or 'cash_discount':
            #(orderID=orderID, productID=productID, count=count, price=price)
            order_price = order_data['price']
            new_price = order_price
            if type == 'percentage_discount':
                new_price = order_price * (sum/100)
                if new_price < 0:
                    new_price = 0
                await bot.send_message(message.chat.id,
                                       f"Промокод {name} был успешно активирован! Скидка составила {round(sum)}%. "
                                       f"Новая цена заказа: {round(new_price, 4)}")
            if type == 'cash_discount':
                new_price = order_price - sum
                if new_price < 0:
                    new_price = 0
                await bot.send_message(message.chat.id,
                                       f"Промокод {name} был успешно активирован! Скидка составила {round(sum, 4)}."
                                       f"Новая цена заказа: {round(new_price, 4)}")
            await state.update_data(price=new_price)
            product = get_product_from_db(order_data['productID'])
            save_in_history(message.from_user.id, sum, product['name'], datetime.now(), promo_code_id)
        reduce_remaining_uses_promo_code(promo_code_id)

#async def ConfirmationProductPurchaseAfterPromoCode(state: FSMContext):
#    order_data = await state.get_data()
#    productID = order_data['productID']
#    count = order_data['count']
#    productID = order_data['productID']
#    productID = order_data['productID']
#    productID = order_data['productID']
#    count = callback.data[2]
#    time = datetime.now()
#    productFromDB = get_product_from_db(productID)
#    price = int(count) * productFromDB['price']
#    await add_order_to_db(callback.from_user.id,
#                          time,
#                          price,
#                          count,
#                          'formed',
#                          productID)
#    orderID = await get_order_id_from_db(callback.from_user.id,
#                                         time,
#                                         price,
#                                         count,
#                                         'formed')
#    markup = types.InlineKeyboardMarkup()
#    btn1 = types.InlineKeyboardButton(_("Отмена", await get_language(callback.message.chat.id)),
#                                      callback_data=f"CancelProductPurchase {orderID}")
#    btn2 = types.InlineKeyboardButton(_('Подтвердить', await get_language(callback.message.chat.id)),
#                                      callback_data=f"PurchaseProduct {orderID} {productID} {count} {price}")
#    btn3 = types.InlineKeyboardButton(_('Ввести промокод', await get_language(callback.message.chat.id)),
#                                      callback_data=f"promo_code_during_purchase {orderID} {productID} {count} {price}")
#    markup.row(btn1, btn2)
#    markup.row(btn3)
#    await bot.send_message(callback.message.chat.id,
#                           text=await generate_payment_template('paymentConfirmation',
#                                                                orderID,
#                                                                productFromDB,
#                                                                callback.from_user.id,
#                                                                time,
#                                                                price,
#                                                                count,
#                                                                'formed'),
#                           reply_markup=markup, parse_mode="HTML")
#    return
#