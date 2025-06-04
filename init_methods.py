import json

from postgres.postgres_handler import postgress_do_querry


db_name = None
translate = None
def generate_start_lang_template(telegram_token, db_name, lang):

    text_array = [
        "All Categories",
        "Products availability",
        "About store",
        "Profile",
        "Rules",
        "Help",
        "About service"
    ]
    text_array = [translate(i,'en',lang) for i in text_array]

    buttons = {"buttons": [
        [
            {
                "type": "action",
                "action": "all_categories",
                "text": text_array[0],
                "additional": ""
            },
            {
                "type": "action",
                "action": "products_availability",
                "text": text_array[1],
                "additional": ""
            }
        ],
        [
            {
                "type": "action",
                "action": "about_store",
                "text": text_array[2],
                "additional": ""
            },
            {
                "type": "action",
                "action": "profile",
                "text": text_array[3],
                "additional": ""
            }
        ],
        [
            {
                "type": "action",
                "action": "rules",
                "text": text_array[4],
                "additional": ""
            },
            {
                "type": "action",
                "action": "help",
                "text": text_array[5],
                "additional": ""
            },
            {
                "type": "action",
                "action": "about_service",
                "text": text_array[6],
                "additional": ""
            }
        ]
    ]}
    buttons = json.dumps(buttons)
    settings = {"preview": False, "protected": False, "silent": False}
    settings = json.dumps(settings)

    template_greetings = translate("Welcome to the store", 'en', lang)
    template_profile = translate("❤️ Name: {FIRST_NAME}\nID: {USER_TELEGRAM_ID}\n💰 Balance: {BALANCE}", "en", lang)

    postgress_do_querry("INSERT INTO templates (token, template, path, buttons, settings)"
                        "VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING",
                        (telegram_token, template_greetings, f"{lang}/greetings", buttons, settings), db_name=db_name)

    postgress_do_querry("INSERT INTO templates (token, template, path, buttons, settings)"
                        "VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING",
                        (telegram_token, template_profile, f"{lang}/profile", None, settings), db_name=db_name)

    postgress_do_querry("INSERT INTO settings (token) VALUES (%s) ON CONFLICT DO NOTHING",(telegram_token,), db_name=db_name)
