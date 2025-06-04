from datetime import datetime
import asyncpg
import psycopg2
from config import telegram_token, db_name
from postgres.postgres_handler import postgress_select_one, postgress_do_querry, postgress_select_all

def add_favorite(id_good, buyer):
    return postgress_do_querry("INSERT INTO favorite_goods (token, buyer, id_good) "
                        "VALUES (%s, %s, %s);",
                        (telegram_token, buyer, id_good))


def del_favorite(id_good, buyer):
    return postgress_do_querry(f"DELETE FROM favorite_goods WHERE id_good = %s AND buyer = %s ", (id_good, str(buyer)))

def check_fav(id_good, buyer):
    fav = []

    result = postgress_select_all(f"SELECT * FROM favorite_goods WHERE buyer = %s AND id_good = %s;", (str(buyer), str(id_good)))
    for line in result:
        fav.append(line['id_good'])
    if fav != []:
        return True
    else:
        return False

check_fav(55, 1339073198)

def show_favourite(buyer):
    fav = []
    result = postgress_select_all(f"SELECT * FROM favorite_goods WHERE buyer = %s;",(str(buyer),))
    for line in result:
        fav.append(line['id_good'])
    print(fav)
    return fav



def show_order(id):
    return postgress_select_one(f"SELECT * FROM orders WHERE id = %s;",
                                (id,))


def show_product(id):
    return postgress_select_one(f"SELECT * FROM products WHERE id = %s;",
                                (id,))