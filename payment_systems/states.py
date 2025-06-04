from aiogram.dispatcher.filters.state import State, StatesGroup


class PaymentStates(StatesGroup):
    payment_get_amount = State()
    payment_formed = State()
