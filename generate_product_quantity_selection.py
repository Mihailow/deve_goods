from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from modules.favourit_module.commands_to_db import *
from postgres.commands_to_db import get_language, get_user_from_db, get_template_from_db
from translations import _

async def generate_product_quantity_selection_back(user_id):
    markup = InlineKeyboardMarkup(row_width=4)
    user = get_user_from_db(user_id)
    localization = user['localization']
    markup.add(InlineKeyboardButton(_('Отмена', await get_language(user_id)),
                                    callback_data=f"BackToProduct"))
    return markup

async def generate_product_quantity_selection(product):
    if product['min_count'] is not None:
        min_value = product['min_count']
    else:
        min_value = 1

    if product['max_count'] is not None:
        max_value = product['max_count']
    else:
        max_value = product['amount']

    markup = InlineKeyboardMarkup(row_width=5)
    buttons = [
        InlineKeyboardButton(str(i), callback_data=f"ConfirmationProductPurchase {product['id']} {str(i)}")
        for i in range(min_value, max_value + 1)
    ]

    markup.add(*buttons)
    return markup


async def generate_calculator_selection(product, current_count, message, promo="0"):
    markup = InlineKeyboardMarkup(row_width=4)
    if product["amount"] != 0:
        buttons = (product["buttons"])["buttons"]
    else:
        user = get_user_from_db(message.from_user.id)
        localization = user['localization']
        template = get_template_from_db(f'{localization}/empty_product')
        if template is None:
            template = get_template_from_db(f'en/empty_product')
            if template is None:
                template = "Language not configured. Contact the bot administrator."
            else:
                buttons = (template['buttons'])['buttons']
        else:
            buttons = (template['buttons'])['buttons']

    if product["amount"] == 0:
        current_count = 0
    elif current_count is None:
        current_count = 1

    for row in buttons:
        markup_row = []
        for button in row:
            action = button["action"].replace("{product_id}", str(product["id"]))
            action = action.replace("{current_count}", str(current_count))
            action = action.replace("{category_id}", str(product["id_category"]))
            if button["text"] == "❤️":
                if check_fav(product['id'], message.from_user.id):
                    markup.add(InlineKeyboardButton('💔',
                                                    callback_data=f"DelFavourites {str(product['id'])}"))
                else:
                    markup.add(InlineKeyboardButton('❤️',
                                                    callback_data=f"addToFavourites {str(product['id'])}"))
            markup_row.append(InlineKeyboardButton(button["text"], callback_data=action))
        markup.row(*markup_row)
    return markup


async def generate_without_quantity_with_confirmation(product, message, promo="0"):
    markup = InlineKeyboardMarkup()
    count = product['max_count'] if product['max_count'] is not None else 1
    markup.row(InlineKeyboardButton(_('Подтверждаю', await get_language(message.from_user.id)),
                                    callback_data=f"ConfirmationProductPurchase {product['id']} {count} {promo}"))
    markup.add(InlineKeyboardButton(_('Добавить в корзину', await get_language(message.from_user.id)),
                                    callback_data=f"add_product_to_basket {product['id']} {count}"))
    if check_fav(product['id'], message.from_user.id):
        markup.add(InlineKeyboardButton('💔 ',
                                        callback_data=f"DelFavourites {str(product['id'])}"))
    else:
        markup.add(InlineKeyboardButton('❤️',
                                        callback_data=f"addToFavourites {str(product['id'])}"))

    return markup
