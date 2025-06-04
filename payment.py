from random import randint

from aiogram import types

from postgres.commands_to_db import get_list_payment_systems_from_db, balance_increase_in_db, \
    change_payments_status_in_db, CheckPayComment, CheckPay, UpdatePay


async def genereatePaymentComment():
    while True:
        id_pay = randint(1000, 100000000)
        if CheckPayComment(id_pay):
            break
    return str(id_pay)

async def generate_markup_of_payment_systems(id, amount):
    paymentSystems = get_list_payment_systems_from_db()
    markup = types.InlineKeyboardMarkup()
    for system in paymentSystems:
        system = system['name']
        markup.row(types.InlineKeyboardButton(system, callback_data=f"CreatingPayment {system} {amount}"))
    return markup



async def balance_increase_in_successful_transfer(bot,paymentID, userID, amount):
    balance_increase_in_db(userID,amount)
    await change_payments_status_in_db(paymentID,'completed')
    #await bot.send_message(userID, f"Средства в размере {amount} ₽ были успешно зачислены на ваш счёт!")