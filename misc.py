# Инициализация бота и диспетчера
import datetime
import sys

from aiogram.types import InputMediaVideo, InputMediaAnimation, InputMediaPhoto, InputMediaDocument
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher.filters import BoundFilter
from aiogram.dispatcher.handler import CancelHandler
from aiogram.dispatcher.middlewares import BaseMiddleware
from pytz import timezone

from config import telegram_token
from modules.admin_module.admin_mailings.mailingsSystems import AlbumMiddleware
from aiogram.dispatcher.filters.state import StatesGroup, State

from postgres.commands_to_db import get_all_active_users_id_from_db, get_admin_list, get_all_banned_users_id_from_db, \
    get_bot_settings, insert_new_settings, get_language, get_bot_subs, get_settings_from_db, get_actions_from_db, \
    get_user_from_db, get_template_from_db, add_new_user_to_db, get_all_inactive_users_id_from_db, \
    get_all_unverified_users_id_from_db, update_user_status_in_db
from translations import _

# sys.path.append("/home/f6d0q9vel074gx96j3ew/global_config")
sys.path.append(r"C:\global_config")

bot = Bot(token=telegram_token)
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(AlbumMiddleware())
dp.middleware.setup(LoggingMiddleware())
active_users = get_all_active_users_id_from_db()
admins_users = get_admin_list()
blocked_users = get_all_banned_users_id_from_db()
inactive_users = get_all_inactive_users_id_from_db()
unverified_users = get_all_unverified_users_id_from_db()
last_mailing_id = [0]
payments_scheduler = AsyncIOScheduler()

name_and_action_reply_button = {}
message_action_dictionary = {}  # message:text

settings = get_settings_from_db()
if settings and settings['settings'] and 'input_field_placeholder' in settings['settings']:
    input_field_placeholder = settings['settings']['input_field_placeholder']
else:
    input_field_placeholder = "Write a message..."

settings = get_bot_settings()
if settings is None:
    insert_new_settings()
    bot_enabled = True
    user_notification = False
    order_notification = False
else:
    bot_enabled = settings['status']
    user_notification = settings['notif_new_user']
    order_notification = settings['notif_new_order']

class CheckBotStatusMiddleware(BaseMiddleware):
    async def on_pre_process(self, user_id, username, first_name, last_name, language_code):
        add_new_user_to_db(user_id, username, first_name, last_name, language_code)
        if user_id in blocked_users:
            raise CancelHandler()
        if user_id in inactive_users:
            await update_user_status(user_id, "unverified")
        if user_id not in active_users and user_id not in unverified_users and user_id not in admins_users:
            await update_user_status(user_id, "unverified")
        settings = get_settings_from_db()
        if settings["time_work_begin"] and settings["time_work_end"] and settings["time_zone"]:
            if user_id not in admins_users:
                difference = datetime.timedelta(hours=round(settings["time_zone"]),
                                                minutes=round(settings["time_zone"] % 1 * 100))
                now = datetime.datetime.now(timezone('UTC')) + difference
                if now.time() < settings["time_work_begin"] or now.time() > settings["time_work_end"]:
                    await generate_and_send_default_message(user_id, 'unavailable_on_time')
                    raise CancelHandler()
        if not bot_enabled and user_id not in admins_users:
            await bot.send_message(user_id, _("Извините, бот временно выключен.", await get_language(user_id)))
            raise CancelHandler()
    async def on_pre_process_message(self, message: types.Message, data: dict):
        await self.on_pre_process(message.from_user.id,
                                  message.from_user.username,
                                  message.from_user.first_name,
                                  message.from_user.last_name,
                                  message.from_user.language_code)

    async def on_pre_process_callback_query(self, callback_query: types.CallbackQuery, data: dict):
        await callback_query.answer()
        await self.on_pre_process(callback_query.from_user.id,
                                  callback_query.from_user.username,
                                  callback_query.from_user.first_name,
                                  callback_query.from_user.last_name,
                                  callback_query.from_user.language_code)


async def generate_default_template(user_id, name, isTest=False, lang=None, is_reply=False):
    user = get_user_from_db(user_id)
    if isTest:
        localization = lang
    else:
        localization = user['localization']
    template = get_template_from_db(f'{localization}/{name}')
    if template is None:
        template = get_template_from_db(f'en/{name}')
        if template is None:
            markup = None
            settings = None
            media = None
            template = "Language not configured. Contact the bot administrator."
        else:
            if is_reply:
                markup = await parse_reply_keyboard_markup(template['buttons'])
            else:
                markup = await parse_inline_keyboard_markup(template['buttons'])
            settings = template['settings']
            media = template['media']
            template = template['template']
    else:
        if is_reply:
            markup = await parse_reply_keyboard_markup(template['buttons'])
        else:
            markup = await parse_inline_keyboard_markup(template['buttons'])
        settings = template['settings']
        media = template['media']
        template = template['template']

    template = await replace_tags_in_template(user_id, template, name)
    return template, markup, settings, media


async def parse_reply_keyboard_markup(content):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, input_field_placeholder=input_field_placeholder)
    if content is None:
        return markup
    content = content['buttons']
    for line in content:
        btns = []
        for btn in line:
            btns.append(types.KeyboardButton(btn['text']))
            name_and_action_reply_button[btn['text']] = btn['action']
            if btn['action'] in ['message', 'select_category', 'select_product']:
                message_action_dictionary[btn['text']] = btn['additional']
        markup.row(*btns)
    return markup


async def parse_inline_keyboard_markup(content):
    markup = types.InlineKeyboardMarkup()
    if content is None:
        return markup
    content = content['buttons']
    for line in content:
        btns = []
        for btn in line:
            if btn['action'] in ["message", "select_category", "select_product"]:
                btns.append(types.InlineKeyboardButton(btn['text'],
                                                       callback_data=f"action_handler_{btn['action']} {btn['text']}"))
            else:
                btns.append(types.InlineKeyboardButton(btn['text'], callback_data=f"action_handler_{btn['action']}"))
            name_and_action_reply_button[btn['text']] = btn['action']
            if btn['action'] in ['message', 'select_category', 'select_product']:
                message_action_dictionary[btn['text']] = btn['additional']
        markup.row(*btns)
    return markup


async def replace_tags_in_template(user_id, template, name):
    user = get_user_from_db(user_id)
    if name in ['greetings', 'dont_work_message']:
        if user['first_name'] is None:
            template = template.replace('{FIRST_NAME}', _('отсутствует', await get_language(user_id)))
            first_name = ""
        else:
            template = template.replace('{FIRST_NAME}', user['first_name'])
            first_name = user['first_name']
        if user['last_name'] is None:
            template = template.replace('{SECOND_NAME}', _('отсутствует', await get_language(user_id)))
            last_name = ""
        else:
            template = template.replace('{SECOND_NAME}', user['last_name'])
            last_name = user['last_name']
        template = template.replace('<br>', '\n')  # Перенос строки
        template = template.replace(' ', ' ')  # Не понял
        template = template.replace('&nbsp;', ' ')  # Не понял 2
        template = template.replace('{USER_TELEGRAM_ID}', str(user['id']))
        template = template.replace('{USERNAME}', first_name + " " + last_name)
        template = template.replace('{NAME}', str(user['nickname']))
        template = template.replace('{USER_ID}', str(user['user_id']))
        template = template.replace('{BALANCE}', str(user['balance']))  # Поправить чтобы брать валюту из БД deve_db
        template = template.replace('{BALANCE_WITHOUT_CURRENCY}', str(user['balance']))
        template = template.replace('{BOT_USER_CREATED_DATETIME}', str(user['date_registration']))

    if name == 'dont_work_message':
        settings = get_settings_from_db()
        if settings['time_work_begin'] is not None:
            template = template.replace('{TIME_WORK_BEGIN}', str(settings['time_work_begin']))
        if settings['time_work_end'] is not None:
            template = template.replace('{TIME_WORK_END}', str(settings['time_work_end']))
        if settings['time_zone'] is not None:
            template = template.replace('{TIME_ZONE}', str(settings['time_zone']))

    return template


async def generate_and_send_default_message(user_id, name):
    template, markup, settings, media = await generate_default_template(user_id, name)
    if settings is not None:
        preview = settings['preview']
        protected = settings['protected']
        silent = settings['silent']
        if media is not None:
            try:
                media_group = []
                for current_media in media:
                    print(current_media)
                    current_media = current_media.replace(':8080/api/v1', '')
                    type = current_media.split('.')[-1]
                    if type in ['mp4', 'mov']:
                        media_group.append(InputMediaVideo(current_media, type='video'))
                    if type == 'gif':
                        media_group.append(InputMediaAnimation(current_media))
                    if type in ['png', 'jpeg']:
                        media_group.append(InputMediaPhoto(current_media))
                    if type in ['txt']:
                        media_group.append(InputMediaDocument(current_media))
                await bot.send_media_group(user_id, media_group)
            except Exception as Ex:
                print(Ex)
        await bot.send_message(user_id, text=template, reply_markup=markup, parse_mode='HTML',
                               disable_web_page_preview=preview,
                               protect_content=protected, disable_notification=silent)
    else:
        if media is not None:
            try:
                media_group = []
                for current_media in media:
                    current_media = current_media.replace(':8080/api/v1', '')
                    type = current_media.split('.')[-1]
                    if type == 'mp4': media_group.append(InputMediaVideo(current_media))
                    if type == 'gif': media_group.append(InputMediaAnimation(current_media))
                    if type in ['png', 'jpeg']: media_group.append(InputMediaPhoto(current_media))
                await bot.send_media_group(user_id, media_group)
            except Exception as Ex:
                print(Ex)
        await bot.send_message(user_id, template, reply_markup=markup, parse_mode='HTML', )


async def update_user_status(user_id, status):
    user = get_user_from_db(user_id)

    if user["status"] == "active":
        active_users.remove(user["id"])
    elif user["status"] == "admins":
        admins_users.remove(user["id"])
    elif user["status"] == "blocked":
        blocked_users.remove(user["id"])
    elif user["status"] == "inactive":
        inactive_users.remove(user["id"])
    elif user["status"] == "unverified":
        try:
            unverified_users.remove(user["id"])
        except:
            pass

    if status == "active":
        active_users.append(user["id"])
    elif status == "admins":
        admins_users.append(user["id"])
    elif status == "blocked":
        blocked_users.append(user["id"])
    elif status == "inactive":
        inactive_users.append(user["id"])
    elif status == "unverified":
        unverified_users.append(user["id"])
    update_user_status_in_db(user_id, status)

class IsSubscriber(BoundFilter):
    async def check(self, message: types.Message):
        if message.from_user.id in admins_users:
            return True
        subscribed = 0

        result = get_bot_subs()
        for chat in result:
            sub = await bot.get_chat_member(chat_id=chat['chat_id'], user_id=message.from_user.id)
            if sub.status != types.ChatMemberStatus.LEFT:
                subscribed += 1
            else:
                break
        if subscribed == len(result):
            return True
        else:
            buttons = []
            channel_numb = 1
            for channel in result:
                sub = await bot.get_chat_member(chat_id=channel['chat_id'], user_id=message.from_user.id)
                if sub.status != types.ChatMemberStatus.LEFT:
                    continue
                else:
                    buttons.append(
                        types.InlineKeyboardButton(text=f"{_('Канал', await get_language(message.from_user.id))} "
                                                        f"{channel_numb}", url=channel['chat_link']))
            keyboard = types.InlineKeyboardMarkup(row_width=1)
            keyboard.add(*buttons)
            await dp.bot.send_message(chat_id=message.from_user.id,
                                      text=_('Подпишитесь на телеграм чаты и повторите попытку ⬇',
                                             await get_language(message.from_user.id)),
                                      reply_markup=keyboard)
            raise CancelHandler()


dp.filters_factory.bind(IsSubscriber)
middleware = CheckBotStatusMiddleware()
dp.middleware.setup(middleware)
