from datetime import datetime

from aiogram import types
from aiogram.types import InputMediaVideo, InputMediaAnimation, InputMediaPhoto

from misc import name_and_action_reply_button, message_action_dictionary, input_field_placeholder, bot, \
    parse_reply_keyboard_markup
from postgres.commands_to_db import *
from translations import _

async def generate_payment_template(path, orderID, product, userID, time, price, count, status ):
    user_language = await get_language(userID)

    template = get_template_from_db(f"{user_language}/{path}")
    if template is None:
        template = get_template_from_db(f"en/{path}")
    if template is None:
        template = "No language, contact to managers"
        markup = types.InlineKeyboardMarkup()
        return template, markup

    buttons = template['buttons']
    template = template['template']

    template = template.replace('{ORDER_ID}', str(orderID))
    template = template.replace('{ORDER_TIME}', str(time))
    template = template.replace('{ORDER_PRICE}', str(price))
    template = template.replace('{ORDER_STATUS}', str(status))
    template = template.replace(" {ORDER_COUNT}", str(count))
    # template = template.replace('{COUPON_INFO}', )
    template = template.replace('{CATEGORY_TITLE}', str(product['name']))
    if "{CATEGORY_PARENT_TITLE}" in template:
        template = template.replace("{CATEGORY_PARENT_TITLE}", get_category_from_db(product['parent_id'])['name'])

    # CATEGORY_PARENT_PARENT_TITLE
    if "{CATEGORY_PARENT_PARENT_TITLE}" in template:
        parent = get_category_from_db(product['parent_id'])
        parent_parent = get_category_from_db(parent['parent_id'])
        template = template.replace("{CATEGORY_PARENT_PARENT_TITLE}", parent_parent['name'])

    # CATEGORY_PARENT_PARENT_PARENT_TITLE
    if "{CATEGORY_PARENT_PARENT_PARENT_TITLE}" in template:
        parent = get_category_from_db(product['id_category'])
        parent_parent = get_category_from_db(parent[2])
        parent_parent_parent = get_category_from_db(parent_parent[2])
        template = template.replace("{CATEGORY_PARENT_PARENT_PARENT_TITLE}", parent_parent_parent[3])

    # CATEGORY_PARENT_PARENT_PARENT_PARENT_TITLE
    if "{CATEGORY_PARENT_PARENT_PARENT_PARENT_TITLE}" in template:
        parent = get_category_from_db(product['id_category'])
        parent_parent = get_category_from_db(parent[2])
        parent_parent_parent = get_category_from_db(parent_parent[2])
        parent_parent_parent_parent = get_category_from_db(parent_parent_parent[2])
        template = template.replace("{CATEGORY_PARENT_PARENT_PARENT_PARENT_TITLE}", parent_parent_parent_parent[3])

    template = template.replace("{CATEGORY_PRICE}", f"{str(product['price'])} {str(product['currency'])}")
    # CATEGORY_DISCOUNT - реализовать
    # CATEGORY_COUNT - реализовать
    # CATEGORY_DESIGN_COUNT - уточнить
    template = template.replace("{CATEGORY_COUNT_PRODUCT}", str(product['amount']))
    # CATEGORY_MIN_COUNT - реализовать
    # CATEGORY_MAX_COUNT - реализовать
    template = template.replace("{ATTRIBUTE-DESCRIPTION}", product['description'])
    # ATTRIBUTE-INSTRUCTION - реализовать

    # ИНФОРМАЦИЯ О ПОЛЬЗОВАТЕЛЕ
    user = get_user_from_db(userID)
    if user['first_name'] is None:
        template = template.replace('{FIRST_NAME}', 'Отсуствует')
    else:
        template = template.replace('{FIRST_NAME}', user['first_name'])
    if user['last_name'] is None:
        template = template.replace('{SECOND_NAME}', 'Отсуствует')
    else:
        template = template.replace('{SECOND_NAME}', user['last_name'])
    template = template.replace('{USER_TELEGRAM_ID}', str(user['id']))
    template = template.replace('{USERNAME}', user['nickname'])
    template = template.replace('{NAME}', str(user['nickname']))
    template = template.replace('{USER_ID}', str(user['user_id']))
    template = template.replace('{BALANCE}', str(user['balance']))
    # {BALANCE_WITHOUT_CURRENCY}
    template = template.replace('{BOT_USER_CREATED_DATETIME}', str(user['date_registration']))
    template = template.replace('{REF_LINK}', str(user['ref_link']))
    # {STATUS}
    # {SECRET_KEY}
    # {COUNT_ORDER}
    # {SUM_ORDER}

    markup = types.InlineKeyboardMarkup()
    if buttons is not None:
        for row in buttons["buttons"]:
            markup_row = []
            for button in row:
                action = button["action"].replace("{orderID}", str(orderID))
                action = action.replace("{productID}", str(product["id"]))
                action = action.replace("{count}", str(count))
                action = action.replace("{price}", str(price))
                markup_row.append(types.InlineKeyboardButton(button["text"], callback_data=action))
            markup.row(*markup_row)

    return template, markup


async def generate_products_availability_template(message, page=1):
    user = get_user_from_db(message.from_user.id)
    localization = user['localization']
    template = get_template_from_db(f'{localization}/products_availability')
    if template is None:
        template = get_template_from_db(f'en/products_availability')
        if template is None:
            template = "Language not configured. Contact the bot administrator."
        else:
            template = template['settings']
    else:
        template = template['settings']

    products = get_all_products_from_db(message.from_user.id)
    categories = get_all_categories_from_db()
    result = ''
    nonunique_product_text = _(template['nonunique_product_text'], await get_language(message.from_user.id))
    absent_product_text = _(template['absent_product_text'], await get_language(message.from_user.id))
    template['delimiter'] = (("{:<" + str(template["indent_delimiter"]) + "}").format("") + template['delimiter'] +
                             ("{:<" + str(template["indent_delimiter"]) + "}").format(""))

    for category in categories:
        temp_result = ""
        empty_category = True
        if category['parent_id'] is None:
            if template['category_output_format'] is None:
                temp_result += f"{template['category_format']} {category['name']} {template['category_format']}\n"
            else:
                temp_result += await generate_products_availability_template_text(message, template, category=category)
            for product in products:
                if template["show_approximate_quantity_product"]:
                    try:
                        if product["amount"] > 501:
                            product["amount"] = "до 1000"
                        elif product["amount"] > 51:
                            product["amount"] = "до 100"
                    except:
                        pass
                if product['id_category'] == category['id']:
                    if product['amount'] == 0:
                        if template["show_empty_products"] is False:
                            continue
                        if template['product_output_format'] is None:
                            temp_result += ("{:<" + str(template["indent_befor_product"]) + "}").format("")
                            temp_result += f"{product['name']}{template['delimiter']}{product['price']} {product['currency']}{template['delimiter']}" \
                                  f"{absent_product_text}\n"
                            empty_category = False
                        else:
                            temp_result += await generate_products_availability_template_text(message, template, 1, category, product)
                            empty_category = False
                    elif product['type'] == 'uniqueFile' or product['type'] == "uniqueGift" or product['type'] == "uniqueProduct":
                        if template['product_output_format'] is None:
                            temp_result += ("{:<" + str(template["indent_befor_product"]) + "}").format("")
                            temp_result += f"{product['name']}{template['delimiter']}{product['price']} {product['currency']}" \
                                      f"{template['delimiter']}{_('Кол-во:', await get_language(message.from_user.id))} " \
                                      f"{product['amount']} {_('шт.', await get_language(message.from_user.id))}\n"
                            empty_category = False
                        else:
                            temp_result += await generate_products_availability_template_text(message, template, 1, category, product)
                            empty_category = False
                    else:
                        if template['product_output_format'] is None:
                            temp_result += ("{:<" + str(template["indent_befor_product"]) + "}").format("")
                            temp_result += f"{product['name']}{template['delimiter']}{product['price']} {product['currency']}" \
                                      f"{template['delimiter']}{nonunique_product_text}\n"
                            empty_category = False
                        else:
                            temp_result += await generate_products_availability_template_text(message, template, 1, category, product)
                            empty_category = False

            for subcategory in categories:
                if category['id'] == subcategory['parent_id']:
                    temp_result += await generate_subcategory_availability_template(template, products, categories,
                                                                               subcategory, 2, message)
                    empty_category = False
            temp_result += "\n"
        if template['show_empty_categories'] is not False:
            result += temp_result
        else:
            if empty_category is False:
                result += temp_result
    substrings = []
    if template["number_of_char_on_page"]:
        count = 0
        ready = 0
        tmp = ""
        for i in range(len(result)):
            count += 1
            if result[i] == "\n":
                if len(tmp) + count > template["number_of_char_on_page"]:
                    substrings.append(tmp)
                    tmp = ""
                tmp += result[ready:i]
                ready = i
                count = 0
        if substrings == [] or tmp not in substrings[len(substrings)-1]:
            substrings.append(tmp)

    if substrings == [] or len(substrings) == 1:
        return result, 1, 1
    else:
        if page > len(substrings):
            page = len(substrings)
        return substrings[page-1], len(substrings), page


async def generate_subcategory_availability_template(template, products, categories, current_category, level, message):
    nonunique_product_text = _(template['nonunique_product_text'], await get_language(message.from_user.id))
    absent_product_text = _(template['absent_product_text'], await get_language(message.from_user.id))
    result = ""
    temp_result = (level - 1) * ("{:<" + str(template["indent_befor_product"]) + "}").format("") + template['subcategory_icon'] + current_category['name'] + "\n"
    empty_category = True

    for product in products:
        if template["show_approximate_quantity_product"]:
            try:
                if product["amount"] > 501:
                    product["amount"] = "до 1000"
                elif product["amount"] > 51:
                    product["amount"] = "до 100"
            except:
                pass
        if product['id_category'] == current_category['id']:
            if product['amount'] == 0:
                if template["show_empty_products"] is False:
                    continue
                if template['product_output_format'] is None:
                    temp_result += ("{:<" + str(template["indent_befor_product"]) + "}").format("") * level + \
                              f"{product['name']}{template['delimiter']}{product['price']} {product['currency']}" \
                              f"{template['delimiter']}{absent_product_text}\n"
                    empty_category = False
                else:
                    temp_result += await generate_products_availability_template_text(message, template, level, current_category, product)
                    empty_category = False
            elif product['type'] == 'uniqueFile' or product['type'] == "uniqueGift" or product['type'] == "uniqueProduct":
                if template['product_output_format'] is None:
                    temp_result += ("{:<" + str(template["indent_befor_product"]) + "}").format("") * level + \
                              f"{product['name']}{template['delimiter']}{product['price']} {product['currency']}{template['delimiter']}" \
                              f"{_('Кол-во:', await get_language(message.from_user.id))} {product['amount']}" \
                          f" {_('шт.', await get_language(message.from_user.id))}\n"
                    empty_category = False
                else:
                    temp_result += await generate_products_availability_template_text(message, template, level, current_category, product)
                    empty_category = False
            else:
                if template['product_output_format'] is None:
                    temp_result += ("{:<" + str(template["indent_befor_product"]) + "}").format("") * level + \
                              f"{product['name']}{template['delimiter']}{product['price']} {product['currency']}{template['delimiter']}{nonunique_product_text}\n"
                    empty_category = False
                else:
                    temp_result += await generate_products_availability_template_text(message, template, level, current_category, product)
                    empty_category = False

    for category in categories:
        if category['parent_id'] == current_category['id']:
            temp_result += await generate_subcategory_availability_template(template, products, categories, category,
                                                                       level + 1, message)
            empty_category = False
    if template['show_empty_categories'] is not False:
        result += temp_result
    else:
        if empty_category is False:
            result += temp_result
    return result


async def generate_products_availability_template_text(message, template, level=None, category=None, product=None):
    nonunique_product_text = _(template['nonunique_product_text'], await get_language(message.from_user.id))
    absent_product_text = _(template['absent_product_text'], await get_language(message.from_user.id))

    text = ""
    if product:
        text = ("{:<" + str(template["indent_befor_product"]) + "}").format("") * level + template['product_output_format']
    elif category:
        text = template['category_output_format']

    if category:
        text = text.replace("{CATEGORY_TITLE}", f"{category['name']}")
    if product:
        text = text.replace("{PRODUCT_TITLE}", f"{product['name']}")
        text = text.replace("|", f"{template['delimiter']}")
        text = text.replace("{PRODUCT_PRICE}", f"{product['price']} {product['currency']}")
        # text = text.replace("[PRODUCT_DISCOUNT]", f"{product['discount']}")
        if product['amount'] == 0:
            text = text.replace("{PRODUCT_DESIGN_COUNT}", f"{absent_product_text}")
        elif product['type'] == 'uniqueFile' or product['type'] == "uniqueGift" or product['type'] == "uniqueProduct":
            text = text.replace("{PRODUCT_DESIGN_COUNT}", f"{_('Кол-во:', await get_language(message.from_user.id))} "
                                                          f"{product['amount']} {_('шт.', await get_language(message.from_user.id))}")
        else:
            text = text.replace("{PRODUCT_DESIGN_COUNT}", f"{nonunique_product_text}")
    return text + "\n"


async def generate_product_count_template(user_id, product_id):
    user = get_user_from_db(user_id)
    product = get_product_from_db(product_id, user_id)
    localization = user['localization']
    template = get_template_from_db(f"{localization}/product_count")
    min_count = product["min_count"]
    if min_count is None:
        min_count = 0
    template["template"] = template["template"].replace("{PRODUCT_MIN_COUNT}", str(min_count))
    max_count = product["max_count"]
    if max_count is None:
        max_count = product["amount"]
    template["template"] = template["template"].replace("{PRODUCT_MAX_SMART_COUNT}", str(max_count))
    return template["template"]


async def generate_main_panel_markup(user_id, isTest = False, lang = None):
    user = get_user_from_db(user_id)
    if isTest:
        localization = lang
    else:
        localization = user['localization']
    template = get_template_from_db(f'{localization}/main_panel')
    if template is None:
        template = get_template_from_db(f'en/main_panel')
        if template is None:
            return None
    return await parse_reply_keyboard_markup(template['buttons'])

async def generate_profile_template(user_id):
    print(user_id)
    user = get_user_from_db(user_id)
    localization = user['localization']
    template = get_template_from_db(f'{localization}/profile')
    if template is None:
        template = get_template_from_db(f'en/profile')
        if template is None:
            template = "Language not configured. Contact the bot administrator."
        else:
            template = template['template']
    else:
        template = template['template']
    if user['first_name'] is None:
        template = template.replace('{FIRST_NAME}', _('отсутствует', await get_language(user_id)))
    else:
        template = template.replace('{FIRST_NAME}', user['first_name'])
    if user['last_name'] is None:
        template = template.replace('{SECOND_NAME}', _('отсутствует', await get_language(user_id)))
    else:
        template = template.replace('{SECOND_NAME}', user['last_name'])
    template = template.replace('{USER_TELEGRAM_ID}', str(user['id']))
    template = template.replace('{USERNAME}', user['nickname'])
    # {NAME}
    template = template.replace('{USER_ID}', str(user['user_id']))
    template = template.replace('{BALANCE}', str(user['balance']))
    # {BALANCE_WITHOUT_CURRENCY}
    template = template.replace('{BOT_USER_CREATED_DATETIME}', str(user['date_registration']))
    template = template.replace('{REF_LINK}', str(user['ref_link']))
    # {STATUS}
    # {SECRET_KEY}
    # {COUNT_ORDER}
    # {SUM_ORDER}
    return template


async def generate_catalog_template(id_catalog):
    category = get_category_from_db(id_catalog)
    template = category['template']
    template = template.replace('{CATEGORY_TITLE}', category['name'])
    if '{CATEGORY_PARENT_TITLE}':
        if category['parent_id'] is not None:
            parent_name = (get_category_from_db(category['parent_id']))['name']
            template = template.replace('{CATEGORY_PARENT_TITLE}', parent_name)
    template = template.replace('{ATTRIBUTE-DESCRIPTION}', category['description'])
    template = template.replace('\\n', '\n')
    return template


async def generate_product_template(user_id, id_product, category_count=1):
    data = get_product_from_db(id_product, user_id)
    if data["amount"] != 0:
        template = data['template']
    else:
        user = get_user_from_db(user_id)
        localization = user['localization']
        template = get_template_from_db(f'{localization}/empty_product')
        if template is None:
            template = get_template_from_db(f'en/empty_product')
            if template is None:
                template = "Language not configured. Contact the bot administrator."
            else:
                template = template['template']
        else:
            template = template['template']

    template = template.replace("{CATEGORY_TITLE}", data['name'])

    if "{CATEGORY_PARENT_TITLE}" in template:
        template = template.replace("{CATEGORY_PARENT_TITLE}", get_category_from_db(data['id_category'])['name'])

    # CATEGORY_PARENT_PARENT_TITLE
    if "{CATEGORY_PARENT_PARENT_TITLE}" in template:
        parent = get_category_from_db(data['id_category'])
        parent_parent = get_category_from_db(parent['id_category'])
        template = template.replace("{CATEGORY_PARENT_PARENT_TITLE}", parent_parent['name'])

    # CATEGORY_PARENT_PARENT_PARENT_TITLE
    if "{CATEGORY_PARENT_PARENT_PARENT_TITLE}" in template:
        parent = get_category_from_db(data['id_category'])
        parent_parent = get_category_from_db(parent['id_category'])
        parent_parent_parent = get_category_from_db(parent_parent['id_category'])
        template = template.replace("{CATEGORY_PARENT_PARENT_PARENT_TITLE}", parent_parent_parent['name'])

    # CATEGORY_PARENT_PARENT_PARENT_PARENT_TITLE
    if "{CATEGORY_PARENT_PARENT_PARENT_PARENT_TITLE}" in template:
        parent = get_category_from_db(data['id_category'])
        parent_parent = get_category_from_db(parent['id_category'])
        parent_parent_parent = get_category_from_db(parent_parent['id_category'])
        parent_parent_parent_parent = get_category_from_db(parent_parent_parent['id_category'])
        template = template.replace("{CATEGORY_PARENT_PARENT_PARENT_PARENT_TITLE}", parent_parent_parent_parent['name'])

    template = template.replace("{CATEGORY_PRICE}", f"{str(data['price'])} {str(data['currency'])}")
    # CATEGORY_DISCOUNT - реализовать
    if data["amount"] > 0:
        template = template.replace("{CATEGORY_COUNT}", str(category_count))
    else:
        template = template.replace("{CATEGORY_COUNT}", "0")
    # CATEGORY_DESIGN_COUNT - уточнить
    template = template.replace("{CATEGORY_COUNT_PRODUCT}", str(data['amount']))
    # CATEGORY_COUNT_PRODUCT и CATEGORY_COUNT разница?
    # CATEGORY_MIN_COUNT - реализовать
    # CATEGORY_MAX_COUNT - реализовать
    template = template.replace("{ATTRIBUTE-DESCRIPTION}", data['description'])
    # ATTRIBUTE-INSTRUCTION - реализовать

    # FIRST_NAME
    # SECOND_NAME
    # USER_TELEGRAM_ID
    # USERNAME
    # NAME
    # BALANCE_TYPE_ID
    # BALANCE_TYPE_TITLE
    # ITEM_ID
    # ITEM_TITLE
    # ITEM_GROUP_ID
    # ITEM_GROUP_TITLE
    # ITEM_DATA
    # USER_ID
    # BALANCE
    # BALANCE_WITHOUT_CURRENCY
    # BOT_USER_CREATED_DATETIME
    # ORDER_ID
    # ORDER_TIME
    # ORDER_PRICE
    # ORDER_COUNT
    # COUNT
    # ORDER_STATUS
    # COUPON_INFO
    # TIME
    # TIME_END

    template = template.replace('\\n', '\n')
    return template


async def generate_history_payments_template(user_id, page, message):
    data = get_history_payments_from_db(user_id)
    template = get_template_from_db(f"{await get_language(user_id)}/history_of_deposits")
    if template is None:
        template = get_template_from_db("en/history_of_deposits")
    if template is None:
        return "No language, contact to manager"
    count_on_page = int(template["settings"]["count_on_page"])
    template_history = template["settings"]["template"]
    template = template["template"]
    format_string = '%Y-%m-%d %H:%M:%S'
    history_text = ""
    if len(data) % count_on_page == 0:
        page_count = len(data) // count_on_page
    else:
        page_count = len(data) // count_on_page + 1

    for i in range((page-1)*count_on_page, page*count_on_page):
        if i >= len(data):
            break
        tmp_text = template_history.replace("{ID}", str(data[i]["id_payments"]))
        tmp_text = tmp_text.replace("{AMOUNT}", str(data[i]["amount"]))
        tmp_text = tmp_text.replace("{STATUS}", str(data[i]["status"]))
        tmp_text = tmp_text.replace("{PAYMENT_TYPE}", str("SYSTEM"))

        history_text += tmp_text + "\n\n"
    history_text = history_text[:-2]
    template = template.replace("{COUNT}", str(len(data)))
    template = template.replace("{HISTORY_INFO}", str(history_text))
    template = template.replace("{PAGE_INFO}", f"{page}/{page_count}")

    # result = f"{_('Всего у Вас пополнений', await get_language(message.from_user.id))}: {len(data)}\n➖➖➖➖➖➖➖➖➖➖➖➖\n"
    # if page == len(data) // 3 + 1:
    #     for i in range(page * 3 - 3, len(data)):
    #         text = f"💡{_('Пополнение', await get_language(message.from_user.id))} №{data[i]['id_payments']}\n" \
    #                f"💰{_('Итоговая сумма', await get_language(message.from_user.id))}: {data[i]['amount']}\n" \
    #                f"🕐{_('Время заказа', await get_language(message.from_user.id))}: {data[i]['date'].strftime(format_string)}\n" \
    #                f"❗{_('Статус', await get_language(message.from_user.id))}: {data[i]['status']}\n\n"
    #         # f"Способ пополнений: SYSTEM
    #         result += text
    # else:
    #     for i in range(page * 3 - 3, (page * 3 - 3) + 3):
    #         text = f"💡{_('Пополнение', await get_language(message.from_user.id))} №{data[i]['id_payments']}\n" \
    #                f"💰{_('Итоговая сумма', await get_language(message.from_user.id))}: {data[i]['amount']}\n" \
    #                f"🕐{_('Время заказа', await get_language(message.from_user.id))}: {data[i]['date'].strftime(format_string)}\n" \
    #                f"❗{_('Статус', await get_language(message.from_user.id))}: {data[i]['status']}\n\n"
    #         # f"Способ пополнений: SYSTEM\n➖➖➖➖➖➖➖➖➖➖➖➖\n"
    #
    #         result += text
    # result += f"{_('Страница', await get_language(message.from_user.id))} {page} " \
    #           f"{_('из', await get_language(message.from_user.id))} {len(data) // 3 + 1}"
    return template, page_count


async def generate_history_order_template(user_id, page):
    data = get_history_order_from_db(user_id)
    format_string = '%Y-%m-%d %H:%M:%S'
    language = await get_language(user_id)
    result = f"{_('Всего у Вас заказов', language )}: {len(data)}\n"
    if page == len(data) // 3 + 1:
        for i in range(page * 3 - 3, len(data)):
            text = f"➖➖➖➖➖➖➖➖➖➖➖➖\n" \
                   f"💡{_('Заказ', language)} №{data[i]['id']}\n" \
                   f"🕐{_('Время заказа', language)}: {data[i]['time'].strftime(format_string)}\n" \
                   f"💰{_('Итоговая сумма', language)}: {data[i]['price']}\n" \
                   f"❗{_('Статус', language)}: {data[i]['status']}" \
                   f"\n➖➖➖➖➖➖➖➖➖➖➖➖\n"
            result += text
    else:
        for i in range(page * 3 - 3, (page * 3 - 3) + 3):
            text = f"➖➖➖➖➖➖➖➖➖➖➖➖\n" \
                   f"💡{_('Заказ', language)} №{data[i]['id']}\n" \
                   f"🕐{_('Время заказа', language)}: {data[i]['time'].strftime(format_string)}\n" \
                   f"💰{_('Итоговая сумма', language)}: {data[i]['price']}\n" \
                   f"❗{_('Статус', language)}: {data[i]['status']}" \
                   f"\n➖➖➖➖➖➖➖➖➖➖➖➖\n"

            result += text
    result += f"{_('Страница', language)} {page} " \
              f"{_('из', language)} {len(data) // 3 + 1}"
    return result, len(data)
