from config import telegram_token
from postgres.postgres_handler import postgress_select_all, postgress_do_querry, postgress_select_one


async def get_mailling_from_db(mailing_id):
    return postgress_select_one(f"select * from mailings where mailing_id = %s AND token = %s;",
                                (int(mailing_id), telegram_token))

async def update_mailling_in_db(text, name_mailing, id_mailing):
    postgress_do_querry("UPDATE mailings SET mailing_text = %s, mailing_name = %s WHERE mailing_id = %s AND token = %s;",
                        (text,name_mailing, id_mailing,telegram_token))

async def get_all_mailling_from_db():
    return postgress_select_all(f"select mailing_name, mailing_id from mailings where token = %s;",
                                (telegram_token,))

async def get_all_userid_from_db():
    return postgress_select_all(f"SELECT id FROM users WHERE token = %s;",
                                (telegram_token,))

async def set_mailing_media_array_in_db(info):
    postgress_do_querry(
        "UPDATE mailings SET mailing_media_array = %s WHERE mailing_id = %s AND token = %s",
        (info['media'], info['id_mailing'], telegram_token))


async def update_mailling_users_count_in_db(isExcept):
    if isExcept:
        postgress_do_querry(
            "UPDATE mailings SET mailing_error_sent = mailing_error_sent + 1, "
            "mailing_total_sent = mailing_total_sent + 1 WHERE token = %s;",(telegram_token,))
    else:
        postgress_do_querry(
            "UPDATE mailings SET mailing_ok_sent = mailing_ok_sent + 1, "
            "mailing_total_sent = mailing_total_sent + 1 WHERE token = %s;",(telegram_token,))


async def add_mailing_complete_in_db():
    postgress_do_querry(
        "UPDATE mailings SET mailing_complete = mailing_complete + 1 WHERE token = %s;",
        (telegram_token,))


async def delete_mailling_from_db(id_mailing):
    postgress_do_querry(
        "DELETE FROM mailings WHERE mailing_id = %s AND token = %s",
        (id_mailing,telegram_token,))
