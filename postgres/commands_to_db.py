from datetime import datetime
from config import telegram_token, db_name
from postgres.postgres_handler import postgress_select_one, postgress_do_querry, postgress_select_all

async def add_payments_to_db(idUser, amount, date, comment):
    pass
    #try:
    #    connection = await connect_to_db()
    #    async with connection.transaction():
    #        query = f"INSERT INTO payments (token, id_user, amount, status, comment, date) VALUES ('{telegram_token}', '{idUser}', '{amount}', 'awaiting', '{comment}', '{date}');"
    #        await connection.execute(query)
    #except Exception as ex:
    #    print(f"[INFO] Error while working with PostgreSQL.\n{ex}")


async def receive_awaiting_payments_from_db():
    pass
    #try:
    #    connection = await connect_to_db()
    #    async with connection.transaction():
    #        query = f"SELECT * FROM payments WHERE token = '{telegram_token}' AND status = 'awaiting';"
    #        result = await connection.fetch(query)
    #        return result
    #except Exception as ex:
    #    print(f"[INFO] Error while working with PostgreSQL.\n{ex}")


async def change_payments_status_in_db(paymentID, status):
    pass
    #try:
    #    connection = await connect_to_db()
    #    async with connection.transaction():
    #        query = f"UPDATE payments SET status = '{status}' WHERE id_payments = '{paymentID}' AND token = '{telegram_token}';"
    #        await connection.execute(query)
    #except Exception as ex:
    #    print(f"[INFO] Error while working with PostgreSQL.\n{ex}")

user_language = dict()

async def get_language(user_id):
    global user_language
    try:
        if str(user_id) not in user_language.keys():
            result = postgress_select_one("SELECT localization FROM users WHERE token = %s AND id = %s;",
                                          (telegram_token, user_id,))
            # Проверить почему иногда возвращается NoneType
            user_language[str(user_id)] = result['localization']
            return result['localization']
        else:
            return user_language[str(user_id)]
    except Exception as ex:
        # print(f"[INFO] Error while working with PostgreSQL.\n{ex}")
        return "en"

# --------------------------------

def CheckPayComment(comment):
    if postgress_select_one("SELECT comment FROM payments WHERE token=%s AND comment=%s",
                            (telegram_token, str(comment),)) is None:
        return True
    return False


def InsertPay(id_user, amount, comment, system, additionally=None):
    postgress_do_querry \
        ("INSERT INTO payments (token, id_user, amount, status, comment, date, system, additionally) "
         "VALUES (%s, %s, %s, 'formed', %s, NOW(), %s, %s)",
         (telegram_token, id_user, amount, comment, system, additionally,))


def CheckPay(ok):
    if ok:
        return postgress_select_all(
            "SELECT * FROM payments WHERE NOW()-date < interval '5 minute' AND status = 'formed'"
            "AND token = %s", (telegram_token,))
    return postgress_select_all("SELECT * FROM payments WHERE NOW()-date > interval '5 minute' AND status = 'formed'"
                                "AND token = %s", (telegram_token,))


def UpdatePay(comment, user_id=None, amount=None, ok=True):
    if ok:
        postgress_do_querry("UPDATE payments SET status = 'completed' WHERE comment = %s AND token = %s",
                            (comment, telegram_token,))
        postgress_do_querry("UPDATE users SET balance = balance+%s WHERE id = %s AND token = %s",
                            (amount, user_id, telegram_token,))
    else:
        postgress_do_querry("UPDATE payments SET status = 'canceled' WHERE comment = %s AND token = %s",
                            (comment, telegram_token,))


def GetPaymentSystemInfo(name):
    return postgress_select_one("SELECT * FROM connected_payment_systems WHERE token = %s AND name = %s",
                                (telegram_token, name,))


def get_template_from_db(path):
    return postgress_select_one("SELECT * FROM templates WHERE token = %s AND path = %s;",
                                (telegram_token, path,))
def get_user_from_db(user_id):
    _ = postgress_select_one("SELECT * FROM users WHERE token = %s AND id = %s;",
                             (telegram_token, user_id,))
    return _

def update_language(user_id, lang):
    postgress_do_querry("UPDATE users SET localization = %s WHERE token = %s AND id = %s;",
                        (lang, telegram_token, user_id,))
    user_language[str(user_id)] = lang


# Функция для добавления нового пользователя в базу данных
def add_new_user_to_db(user_id, username, first_name, last_name, localization):
    postgress_do_querry(
            "call insert_user(%s, %s, %s, %s, %s, %s, %s);",
            (telegram_token, user_id, username, first_name, last_name, datetime.now(), localization,))


def update_user_status_in_db(user_id, status):

    postgress_do_querry("UPDATE users SET status = %s WHERE token = %s AND id = %s;",
                        (status, telegram_token, user_id,))


def get_bot_subs():
    return postgress_select_all("SELECT chat_link, chat_id FROM bot_subs WHERE token = %s",
                                (telegram_token,))


def get_all_products_from_db(user_id):
    user = get_user_from_db(user_id)
    return postgress_select_all("select * from products left join products_language_settings "
                                "on products_language_settings.id = products.id "
                                "where token = %s and products_language_settings.language = %s ;",
                                (telegram_token, user["localization"]))

def get_all_categories_from_db():
    return postgress_select_all("SELECT * FROM categories WHERE token = %s;",
                                (telegram_token,))


def get_sub_categories_from_db(parent_id):
    return postgress_select_all(f"SELECT * FROM categories WHERE token = %s AND parent_id = %s;",
                                (telegram_token, int(parent_id),))


def get_products_from_db(id_category, user_id):
    id_category = int(id_category)
    user = get_user_from_db(user_id)
    return postgress_select_all("select * from products left join products_language_settings "
                                "on products_language_settings.id = products.id "
                                "where token = %s and products_language_settings.language = %s AND id_category = %s;",
                                (telegram_token, user["localization"], id_category))


def get_category_from_db(id_category):
    return postgress_select_one(f"SELECT * FROM categories WHERE token = %s AND id = %s;",
                                (telegram_token, id_category,))


def get_categories_from_db():
    return postgress_select_all(f"SELECT * FROM categories WHERE token = %s AND parent_id is NULL;",
                                (telegram_token,))


def get_product_from_db(id_product, user_id):
    id_product = int(id_product)
    user = get_user_from_db(user_id)

    product = postgress_select_one("select * from products left join products_language_settings "
                                   "on products_language_settings.id = products.id "
                                   "where token = %s and products_language_settings.language = %s AND products.id = %s;",
                                   (telegram_token, user["localization"], id_product))

    if "non" in product["type"] or "service" in product["type"]:
        path = "nonunique_product"
    else:
        path = "unique_product"

    localization = user['localization']
    template = get_template_from_db(f'{localization}/{path}')
    if template is None:
        template = get_template_from_db(f'en/{path}')
    if template is not None:
        product["template"] = template["template"]
        product["buttons"] = template["buttons"]

    return product


def get_settings_from_db():
    return postgress_select_one(f"SELECT * FROM settings WHERE token = %s;",
                                (telegram_token,))
    # template = get_template_from_db(f'en/settings')
    # template = template['settings']
    # return template


def get_bot_settings():
    return postgress_select_one(f"SELECT * FROM bots WHERE token = %s;",
                                (telegram_token,), True)


def get_admin_list():
    result = postgress_select_one(f"SELECT admins FROM bots WHERE token = %s;",
                                  (telegram_token,), True)
    users = postgress_select_all("SELECT id FROM users WHERE token = %s AND status = 'manager';",
                                   (telegram_token,))
    for user in users:
        if str(user["id"]) not in result['admins']:
            result['admins'].append(str(user["id"]))
    return list(map(int, result['admins']))



def insert_new_settings():
    postgress_do_querry("INSERT INTO bots (token, status, notif_new_user, notif_new_order) "
                        "VALUES (%s, true, false, false);",
                        (telegram_token,), True)


def add_malling_to_db(media, caption, name_mailing):
    if media is not None:
        if caption is not None:
            postgress_do_querry("insert into mailings(bot_token, mailing_name, mailing_text, mailing_media_array, "
                                "mailing_create_date, mailing_status) values(%s, %s, %s, %s, %s, %s);",
                                (telegram_token, name_mailing, caption, media,
                                 datetime.now().strftime('%d.%m.%y %I:%M:%S', 'Черновик'), True))
        else:
            postgress_do_querry("insert into mailings(bot_token, mailing_name, mailing_media_array, "
                                "mailing_create_date, mailing_status) values(%s, %s, %s, %s, %s);",
                                (telegram_token, name_mailing, media,
                                 datetime.now().strftime('%d.%m.%y %I:%M:%S', 'Черновик'), True))
    else:
        postgress_do_querry("insert into mailings(bot_token, mailing_name, mailing_text, "
                            "mailing_create_date, mailing_status) values(%s, %s, %s, %s, %s);",
                            (telegram_token, name_mailing, caption,
                             datetime.now().strftime('%d.%m.%y %I:%M:%S', 'Черновик'), True))


def get_all_active_users_id_from_db():
    ids = []
    result = postgress_select_all(f"SELECT id FROM users WHERE token = %s AND status = 'active';", (telegram_token,))
    for line in result:
        ids.append(line['id'])
    return ids


def get_all_inactive_users_id_from_db():
    ids = []
    result = postgress_select_all(f"SELECT id FROM users WHERE token = %s AND status = 'inactive';", (telegram_token,))
    for line in result:
        ids.append(line['id'])
    return ids


def get_all_unverified_users_id_from_db():
    ids = []
    result = postgress_select_all(f"SELECT id FROM users WHERE token = %s AND status = 'unverified';", (telegram_token,))
    for line in result:
        ids.append(line['id'])
    return ids


def get_all_banned_users_id_from_db():
    ids = []
    result = postgress_select_all(f"SELECT id FROM users WHERE token = %s AND status = 'blocked';", (telegram_token,))
    for line in result:
        ids.append(line['id'])
    return ids

def get_parent_id(telegram_token, id):
    id = int(id)
    result = postgress_select_one(f"SELECT parent_id FROM categories WHERE token = %s AND id = %s;",
                                  (telegram_token, id))
    return result['parent_id']

def get_list_payment_systems_from_db():
    return postgress_select_all(f"SELECT name FROM connected_payment_systems WHERE token = %s;", (telegram_token,))

def balance_increase_in_db(id, count):
    postgress_do_querry("UPDATE users SET balance = balance + %s WHERE id = %s AND token = %s;",
                        (count,id,telegram_token,))

def get_order_from_db(idOrder):
    return postgress_select_one(f"SELECT * FROM orders WHERE token = %s AND id = %s;",
                                (telegram_token,idOrder))

def add_order_to_db(buyer, time, price, count, status, product_id, promo, balance_price):
    buyer = str(buyer)
    postgress_do_querry("INSERT INTO orders (token, buyer, time, price, count, status, product_id, promo, balance_price) "
                        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);",
                        (telegram_token, buyer, time, price, count, status, product_id, promo, balance_price))

def get_order_id_from_db(buyer, time, price, count, status):
    buyer = str(buyer)
    return postgress_select_one(f"SELECT id FROM orders WHERE token = %s AND buyer = %s AND "
                                f"time = %s AND price = %s AND count = %s AND status = %s;",
                                (telegram_token, buyer, time, price, count, status))

def change_order_status_in_db(orderID, status):
    postgress_do_querry("UPDATE orders SET status = %s WHERE id = %s AND token = %s;",
                        (status, orderID, telegram_token,))

def update_product_in_db(field, content, id):
    postgress_do_querry(f"UPDATE products SET {field} = %s WHERE id = %s AND token = %s;",
                        (content, id, telegram_token,))

def delete_all_product_data_from_db(productID):
    postgress_do_querry(f"DELETE FROM product_data WHERE id_product = {productID}",(productID,))

def add_product_data_to_db(productID, data, is_unique):
    try:
        for line in data:
            postgress_do_querry(f"INSERT INTO product_data (id_product, data, is_used, is_unique) "
                                f"VALUES (%s,%s,False,%s;", (productID, line, is_unique))
        return 1
    except Exception as ex:
        print(f"[INFO] Error while working with PostgreSQL.\n{ex}")
        return 0

def unload_unused_product_data_from_db(productID, count):
    try:
        result = []
        data = postgress_select_all(
            f"SELECT * FROM product_data WHERE id_product = %s AND is_used = False LIMIT %s;",(productID, count))
        if len(data) == 0:
            return []
        else:
            for line in data:
                postgress_do_querry(f"DELETE FROM product_data WHERE id = %s;", (line['id'],))
                result.append(line['data'])
            return result
    except Exception as ex:
        print(f"[INFO] Error while working with PostgreSQL.\n{ex}")
        return None

def get_history_order_from_db(user_id):
    user_id = str(user_id)
    return postgress_select_all(f"SELECT * FROM orders WHERE token = %s AND buyer = %s ORDER BY time DESC;",
                                    (telegram_token, user_id))

def get_history_payments_from_db(user_id):
    return postgress_select_all(f"SELECT * FROM payments WHERE token = %s AND id_user = %s ORDER BY date DESC;",
                                    (telegram_token, user_id))

def add_new_product_to_db(id_category, type, name, description, price):
    default_currency = "RUB"
    default_template = "📃 Товар: {CATEGORY_TITLE}\n" \
                       "💰 Цена: {CATEGORY_PRICE}\n" \
                       "📃 Описание: {ATTRIBUTE-DESCRIPTION}\n" \
                       "Выберите количество товара, которое хотите купить:"
    default_keyboard_operation_model = "ProductQuantitySelection"
    default_amount = 0
    default_isvisible = True
    postgress_do_querry("INSERT INTO products (id_category, type, name, description, "
                        "amount, price, currency, template, isvisible,token,keyboard_operation_model)"
                        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);",
                        (int(id_category), type, name, description, default_amount, float(price), default_currency,
                         default_template, default_isvisible, telegram_token, default_keyboard_operation_model,))

def get_products_by_name_from_db(name):
    return postgress_select_all(f"select * from products where name = %s AND token = %s;",(name, telegram_token))

def get_products_for_delivery_from_db(id, count, order_id, isUsedChange):
    result = postgress_select_all(f"SELECT * from product_data WHERE id_product = %s AND is_used = FALSE LIMIT %s",
                                (id, count))
    if isUsedChange == True:
        for line in result:
            postgress_do_querry(f"UPDATE product_data SET is_used = TRUE WHERE id = %s",(int(line['id']),))
            postgress_do_querry(f"UPDATE product_data SET order_id = %s WHERE id = %s",
                                (str(order_id), int(line['id']),))
    return result

def get_actions_from_db():
    result = postgress_select_all(f"SELECT * FROM actions WHERE token = %s;",(telegram_token,))
    postgress_do_querry(f"DELETE FROM actions WHERE token = %s;",(telegram_token,))
    return result

def get_status_bot_from_db():
    result = postgress_select_one(f"SELECT status FROM bots WHERE token = %s",(telegram_token,),True)
    return result['status']

def insert_mailings_history(users, template, success, name = None):
    postgress_do_querry("INSERT INTO mailings_history (token, mailing_name, users, template, success, date) "
                        "VALUES (%s, %s, %s, %s, %s, %s);",
                        (telegram_token, name, users, template, success,
                         datetime.now(),))

def get_mailings_planned_from_db(mailing_id):
    result = postgress_select_all(f"SELECT * FROM mailings_planned WHERE token = %s AND mailing_id > %s;",
                                  (telegram_token, mailing_id,))
    return result

def delete_mailings_planned_from_db(mailing_id):
    postgress_do_querry(f"DELETE FROM mailings_planned WHERE token = %s AND mailing_id = %s;",
                                  (telegram_token, mailing_id,))
async def get_payments_groups_from_db():
    result = postgress_select_one(f"SELECT id, name FROM payments_groups WHERE token = %s",(telegram_token,),True)
    return result['status']
