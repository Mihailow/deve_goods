import sys

import psycopg2
import psycopg2.extras
from config import db_name


#sys.path.append("/home/f6d0q9vel074gx96j3ew/global_config")
sys.path.append(r"C:\global_config")
#sys.path.append(r"C:\Users\Денис\Desktop\dvbot\global_config")
from global_config_bot import host, user, password, db_name_main

DB_HOST = "localhost"
DB_NAME = db_name
MAIN_DB_NAME = db_name_main
DB_USER = "postgres"
DB_PASS = "postgres"
#DB_PASS = "gg360gg"
#DB_PASS = "F1n93R5@R3Hur71n9"
conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
conn_main = psycopg2.connect(dbname=db_name_main, user=DB_USER, password=DB_PASS, host=DB_HOST)

def postgress_do_querry(querry, params, is_main = False):
    if is_main:
        cursor = conn_main.cursor(cursor_factory=psycopg2.extras.DictCursor)
    else:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute(querry, params)
    conn.commit()
    cursor.close()
    return None


def postgress_select_one(querry, params, is_main=False):
    if is_main:
        cursor = conn_main.cursor(cursor_factory=psycopg2.extras.DictCursor)
    else:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute(querry, params)
    result = cursor.fetchone()
    if result:
        result = dict(result)
    conn.commit()
    cursor.close()
    return result


def postgress_select_all(querry, params, is_main=False):
    if is_main:
        cursor = conn_main.cursor(cursor_factory=psycopg2.extras.DictCursor)
    else:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute(querry, params)
    results = cursor.fetchall()
    if results:
        res = []
        for r in results:
            res.append(dict(r))
        results = res
    conn.commit()
    cursor.close()
    return results