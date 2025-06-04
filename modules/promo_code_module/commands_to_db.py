from config import telegram_token
from postgres.postgres_handler import postgress_select_one, postgress_do_querry


def get_promocode(name):
    return postgress_select_one("SELECT * FROM promo_codes WHERE token = %s AND name = %s;",
                                    (telegram_token, name,))


def check_new_user(user_id):
    result = postgress_select_one("SELECT * FROM orders WHERE token = %s AND buyer = %s AND status = %s;",
                                    (telegram_token, str(user_id), 'Complete'))
    if result is None:
        return True
    else:
        return False

def check_repeat(user_id, promo_code_id):
    result = postgress_select_one("SELECT * FROM promo_codes_history WHERE token = %s AND user_id = %s AND promo_code_id = %s;",
                                  (telegram_token, int(user_id), promo_code_id))
    if result is None:
        return False
    else:
        return True

def add_balance(user_id, sum):
    postgress_do_querry("UPDATE users SET balance = balance + %s WHERE token = %s AND id = %s",
                        (sum, telegram_token, int(user_id)))

def save_in_history(user_id, sum, product_name, date, promo_code_id):
    postgress_do_querry \
        ("INSERT INTO promo_codes_history (token, user_id, sum, product_name, date, promo_code_id) "
         "VALUES (%s, %s, %s, %s, %s, %s)",(telegram_token, int(user_id), sum, product_name, date, promo_code_id,))

def reduce_remaining_uses_promo_code(id):
    postgress_do_querry("UPDATE promo_codes SET remaining_uses = remaining_uses - 1 WHERE token = %s AND id = %s",
                        (telegram_token, id))

