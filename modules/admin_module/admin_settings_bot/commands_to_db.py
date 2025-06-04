from config import telegram_token
from postgres.postgres_handler import postgress_do_querry


def update_settings(setting_name, action):
    postgress_do_querry(f"UPDATE bots SET {setting_name} = %s WHERE token = %s",
                        (action, telegram_token,), True)
