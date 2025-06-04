from config import telegram_token
from postgres.postgres_handler import postgress_do_querry, postgress_select_all, postgress_select_one


def add_product_to_basket_in_db(user_id, product_id, count):
    postgress_do_querry("INSERT INTO baskets (token, user_id, product_id, count)"
                "VALUES (%s, %s, %s, %s);",(telegram_token, user_id, product_id, count))

def get_user_basket_from_db(user_id):
    result = postgress_select_all(f"SELECT * FROM baskets WHERE token = %s and user_id = %s;",
                                  (telegram_token,user_id))
    return result

def get_product_data_from_db(id):
    result = postgress_select_one(f"SELECT name,price,currency FROM products WHERE token = %s and id = %s;",
                                  (telegram_token, id))
    return result

def clean_basket_in_db(user_id):
    postgress_do_querry("DELETE FROM baskets WHERE user_id = %s AND token = %s",(user_id, telegram_token))