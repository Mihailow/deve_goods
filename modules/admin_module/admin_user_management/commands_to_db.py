from config import telegram_token
from postgres.postgres_handler import postgress_select_one, postgress_do_querry


async def find_user_in_db(method, text):
    req = postgress_select_one(f"SELECT * FROM users WHERE token = %s AND {method} = %s;",
                               (telegram_token, text,))
    print(req)
    return req
