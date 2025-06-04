import traceback
from typing import List

from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text

from main import MyStates, bot, dp
from modules.admin_module.admin_mailings.commands_to_db import get_mailling_from_db, get_all_mailling_from_db, \
    update_mailling_in_db, get_all_userid_from_db, set_mailing_media_array_in_db, update_mailling_users_count_in_db, \
    add_mailing_complete_in_db, delete_mailling_from_db
from modules.admin_module.admin_mailings.keyboards import get_main_mailings_keyboards
from modules.admin_module.admin_mailings.mailingsSystems import check_file_type
from postgres.commands_to_db import get_language
from translations import _
from aiogram import types

@dp.callback_query_handler(Text(startswith='mailing@'))  # Обработчик кнопок с рассылками
async def current_mailing(call: types.CallbackQuery, state: FSMContext):
    await call.answer("")
    mailing_id = int(call.data.split('@')[1])
    await state.update_data(id_mailing=mailing_id)
    keyboard = await get_main_mailings_keyboards(call)
    mailing = await get_mailling_from_db(mailing_id)
    await call.message.answer(f"{_('Статус', call.from_user.language_code)}: ⚫ {mailing['mailing_status']} ⚫\n"
                              f"{_('Создано', call.from_user.language_code)}: {mailing['mailing_create_date']}\n"
                              f"{_('Завершено', call.from_user.language_code)}: {mailing['mailing_complete']}\n"
                              f"➖➖➖ {_('Информация', call.from_user.language_code)}:➖➖➖\n"
                              f"{_('Всего отправлено', call.from_user.language_code)}: {mailing['mailing_total_sent']}\n"
                              f"{_('Успешно', call.from_user.language_code)}: {mailing['mailing_ok_sent']}\n"
                              f"{_('С ошибкой', call.from_user.language_code)}: {mailing['mailing_error_sent']}\n"
                              f"➖➖➖➖➖➖➖➖➖➖➖➖", reply_markup=keyboard)

async def get_mailing(id):
    info = await get_mailling_from_db(id)
    mailing = dict()
    mailing['bot_token'] = info[0]
    mailing['id'] = info[1]
    mailing['name'] = info[2]
    mailing['text'] = info[3]
    mailing['media'] = info[4]
    return mailing


@dp.message_handler(state=MyStates.change_media_state, is_media_group=False,
                    content_types=['photo', 'animation', 'video'])
async def change_mailing_media(message: types.Message, state: FSMContext):
    await message.answer("")
    info = await state.get_data()
    mailing = await get_mailling_from_db(info['id_mailing'])
    if check_file_type(message) == 'photo':  # ЕСЛИ ЮЗЕР ПРИСЛАЛ ФОТКУ
        await state.update_data(media=message.photo[-1].file_id + '@@' + 'photo')
        file_inf = await state.get_data()
        await bot.send_photo(chat_id=message.from_user.id, photo=file_inf['media'].split('@@')[0],
                             caption=mailing['text'])
    elif check_file_type(message) == 'animation':  # ЕСЛИ ЮЗЕР ПРИСЛАЛ ГИФКУ
        await state.update_data(media=message.animation.file_id + '@@' + 'animation')
        await state.update_data(caption=message.caption)
        file_inf = await state.get_data()
        await bot.send_animation(chat_id=message.from_user.id, animation=file_inf['media'].split('@@')[0],
                                 caption=mailing['text'])
    elif check_file_type(message) == 'video':  # ЕСЛИ ЮЗЕР ПРИСЛАЛ ВИДЕО
        await state.update_data(media=message.video.file_id + '@@' + 'video')
        await state.update_data(caption=message.caption)
        file_inf = await state.get_data()
        await bot.send_video(chat_id=message.from_user.id, video=file_inf['media'].split('@@')[0],
                             caption=mailing['text'])
    buttons = [
        types.InlineKeyboardButton(text=_('Да', await get_language(message.from_user.id)), callback_data='confirm_change_media'),
        types.InlineKeyboardButton(text=_('Нет', await get_language(message.from_user.id)), callback_data='refuse_change_media')
    ]
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(*buttons)
    await message.answer(_('Всё верно?', await get_language(message.from_user.id)), reply_markup=keyboard)


@dp.message_handler(state=MyStates.change_media_state, is_media_group=True,
                    content_types=['photo', 'animation', 'video'])
async def change_mailing_mediat(message: types.Message, album: List[types.Message], state: FSMContext):
    media_group = types.MediaGroup()
    media = ''
    info = await state.get_data()
    mailing = await get_mailling_from_db(info['id_mailing'])
    text = mailing['mailing_text']
    for obj in album:
        if obj.photo:
            file_id = obj.photo[-1].file_id
        else:
            file_id = obj[obj.content_type].file_id
        try:
            media += file_id + '@@' + obj.content_type + ','
            # We can also add a caption to each file by specifying `"caption": "text"`
            media_group.attach({"media": file_id, "type": obj.content_type, "caption": text})
            text = None
        except ValueError:
            return await message.answer("This type of album is not supported by aiogram.")
    await state.update_data(media=media)
    buttons = [
        types.InlineKeyboardButton(text=_('Да', await get_language(message.from_user.id)), callback_data='confirm_change_media'),
        types.InlineKeyboardButton(text=_('Нет', await get_language(message.from_user.id)), callback_data='refuse_change_media')
    ]
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(*buttons)
    await bot.send_media_group(chat_id=message.from_user.id, media=media_group)
    # await send_file(media_group=media_group, chat_id=message.from_user.id, file_id=None, type_file=None)
    media_group.clean()
    # await message.answer_media_group(media_group)
    await message.answer(_('Всё верно?', await get_language(message.from_user.id)), reply_markup=keyboard)

@dp.callback_query_handler(text="mailing_button")  # Меню рассылок
async def mailing_func(call: types.CallbackQuery):
    await call.answer("")
    await bot.delete_message(call.message.chat.id, call.message.message_id)
    # await call.message.answer(f'Твой ID: {call.from_user.id}')
    buttons = [
        types.InlineKeyboardButton(text=_('Добавить рассылку', call.from_user.language_code),
                                   callback_data='add_mailing'),
        types.InlineKeyboardButton(text=_('Сформировать и запустить рассылку', call.from_user.language_code),
                                   callback_data='go_mailing')
    ]
    list_mailing_text = await get_all_mailling_from_db()
    count_mailing = 1
    for i in list_mailing_text:
        print(i)
        buttons.append(types.InlineKeyboardButton(text=f"⚫ {i['mailing_name']}",
                                                  callback_data=f"mailing@{i['mailing_id']}"))
    buttons.append(types.InlineKeyboardButton(text=_('Отмена', call.from_user.language_code),
                                              callback_data='backToAdminMenu'))
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(*buttons)
    await call.message.answer(f"{_('Добро пожаловать в меню управления рассылками', call.from_user.language_code)}!",
                              reply_markup=keyboard)

async def send_momental_mailing(state: FSMContext,
                                chat_id):  # функция отправки мгновенной рассылки (без добавления в бд)
    mailing = await state.get_data()
    if mailing['media'] is not None:
        if len(str(mailing['media']).split(',')) > 2:
            media = await media_group_formation(mailing['media'], mailing['caption'])
            await bot.send_media_group(chat_id=chat_id, media=media)
        else:
            if mailing['media'].split('@@')[1] == 'photo':
                await bot.send_photo(chat_id=chat_id, photo=mailing['media'].split('@@')[0], caption=mailing['caption'])
            elif mailing['media'].split('@@')[1] == 'animation':
                await bot.send_animation(chat_id=chat_id, animation=mailing['media'].split('@@')[0],
                                         caption=mailing['caption'])
            elif mailing['media'].split('@@')[1] == 'video':
                await bot.send_video(chat_id=chat_id, video=mailing['media'].split('@@')[0], caption=mailing['caption'])
    else:
        await bot.send_message(chat_id, text=str(mailing['caption']))

@dp.callback_query_handler(text=['add_mailing'])
async def add_mailing(call: types.CallbackQuery):
    await call.answer("")
    await call.message.answer(_('Отправьте фото/медиа группу/гиф/текст для рассылки',
                                call.from_user.language_code))
    await MyStates.new_mailing_state.set()

@dp.message_handler(state=MyStates.new_mailing_state, is_media_group=False, content_types=['photo', 'animation',
                                                                                           'text', 'video'])
async def new_mail_without_media(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        if check_file_type(message) == 'photo':  # ЕСЛИ ЮЗЕР ПРИСЛАЛ ФОТКУ
            await state.update_data(media=message.photo[-1].file_id + '@@' + 'photo')
            await state.update_data(caption=message.caption)
            file_inf = await state.get_data()
            await bot.send_photo(chat_id=message.from_user.id, photo=file_inf['media'].split('@@')[0],
                                 caption=file_inf['caption'])
        elif check_file_type(message) == 'animation':  # ЕСЛИ ЮЗЕР ПРИСЛАЛ ГИФКУ
            await state.update_data(media=message.animation.file_id + '@@' + 'animation')
            await state.update_data(caption=message.caption)
            file_inf = await state.get_data()
            await bot.send_animation(chat_id=message.from_user.id, animation=file_inf['media'].split('@@')[0],
                                     caption=file_inf['caption'])
        elif check_file_type(message) == 'video':  # ЕСЛИ ЮЗЕР ПРИСЛАЛ ВИДЕО
            await state.update_data(media=message.video.file_id + '@@' + 'video')
            await state.update_data(caption=message.caption)
            file_inf = await state.get_data()
            await bot.send_video(chat_id=message.from_user.id, video=file_inf['media'].split('@@')[0],
                                 caption=file_inf['caption'])
        else:  # если юзер прислал просто текст
            await state.update_data(caption=message.text)
            await state.update_data(media=None)
            file_inf = await state.get_data()
            await message.answer(file_inf['caption'])
        buttons = [
            types.InlineKeyboardButton(text=_('Да', await get_language(message.from_user.id)),
                                       callback_data='confirm_add_mailing'),
            types.InlineKeyboardButton(text=_('Нет', await get_language(message.from_user.id)),
                                       callback_data='refuse_new_mailing')
        ]
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        keyboard.add(*buttons)
        await message.answer(_('Всё верно?', await get_language(message.from_user.id)), reply_markup=keyboard)
        # await message.answer("")


@dp.callback_query_handler(state=MyStates.new_mailing_state, text=['refuse_new_mailing'])  # ОТМЕНА НОВОЙ РАССЫЛКИ
async def refuse_mailing(call: types.CallbackQuery, state: FSMContext):
    await bot.send_message(call.message.chat.id, _('Рассылка была отменена', call.from_user.language_code),
                           parse_mode="HTML")
    await mailing_func(call)
    await state.reset_data()
    await state.finish()  # Выключаем состояние


async def media_group_formation(array, caption):  # формирование медиагруппы, на вход строка media из бд
    media = types.MediaGroup()
    text = caption
    for file in array.split(','):
        if file == '':
            continue
        media.attach({'media': file.split('@@')[0], 'type': file.split('@@')[1], 'caption': text})
        text = None
    return media


@dp.message_handler(state=MyStates.new_mailing_state, is_media_group=True, content_types=['photo',
                                                                                          'animation', 'video'])
async def new_mail_with_media(message: types.Message, album: List[types.Message], state: FSMContext):
    """This handler will receive a complete album of any type."""
    async with state.proxy() as data:
        media_group = types.MediaGroup()
        await state.update_data(caption=message.caption)
        media = ''
        text = message.caption
        for obj in album:
            if obj.photo:
                file_id = obj.photo[-1].file_id
            else:
                file_id = obj[obj.content_type].file_id
            try:
                media += file_id + '@@' + obj.content_type + ','
                # We can also add a caption to each file by specifying `"caption": "text"`
                media_group.attach({"media": file_id, "type": obj.content_type, "caption": text})
                text = None
            except ValueError:
                return await message.answer("This type of album is not supported by aiogram.")
        await state.update_data(media=media)
        buttons = [
            types.InlineKeyboardButton(text="Да", callback_data='confirm_add_mailing'),
            types.InlineKeyboardButton(text="Добавить текст", callback_data='add_text_to_mailing'),
            types.InlineKeyboardButton(text="Нет", callback_data='refuse_new_mailing')
        ]
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        keyboard.add(*buttons)
        await bot.send_media_group(chat_id=message.from_user.id, media=media_group)
        # await send_file(media_group=media_group, chat_id=message.from_user.id, file_id=None, type_file=None)
        media_group.clean()
        # await message.answer_media_group(media_group)
        await message.answer(f"{_('Всё верно?', await get_language(message.from_user.id))}\n"
                             f"{_('Если текст не отобразился, нажмите на кнопку -Добавить текст- ⬇', await get_language(message.from_user.id))}",
                             reply_markup=keyboard)

@dp.callback_query_handler(state=MyStates.new_mailing_state, text=['add_text_to_mailing'])
async def add_text_to_mailing(call: types.CallbackQuery):
    await call.answer("")
    await call.message.answer(_('Отправьте текст, который хотите добавить', call.from_user.language_code))
    await MyStates.add_text_state.set()


@dp.message_handler(state=MyStates.add_text_state, content_types=types.ContentType.TEXT)
async def add_text_to_mailing(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        await state.update_data(caption=message.text)
        inf = await state.get_data()
        text = inf['caption']
        media_group = types.MediaGroup()
        for obj in inf['media'].split(','):
            if obj == '':
                continue
            try:
                media_group.attach({"media": obj.split('@@')[0], "type": obj.split('@@')[1], "caption": text})
                text = None
            except ValueError:
                return await message.answer("This type of album is not supported by aiogram.")

        await bot.send_media_group(chat_id=message.from_user.id, media=media_group)
        buttons = [
            types.InlineKeyboardButton(text=_('Да', await get_language(message.from_user.id)), callback_data='confirm_add_mailing'),
            types.InlineKeyboardButton(text=_('Нет', await get_language(message.from_user.id)), callback_data='refuse_new_mailing')
        ]
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        keyboard.add(*buttons)
        media_group.clean()
        await message.answer(_('Всё верно?', await get_language(message.from_user.id)), reply_markup=keyboard)
        await state.set_state(MyStates.new_mailing_state.state)


@dp.callback_query_handler(state=MyStates.new_mailing_state,
                           text=['confirm_add_mailing'])  # ПОДТВЕРЖДЕНИЕ НОВОЙ РАССЫЛКИ
async def confirm_mailing(call: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        info = await state.get_data()
        if 'instant_mailing' in info.keys():
            if info['instant_mailing']:
                await start_mailing(call=call, state=state)
                await state.set_state(None)
                return

async def send_mailing(id, chat_id):  # на вход id рассылки из бд и id чата с юзером
    try:
        mailing = await get_mailing(id)
        if mailing['media'] is not None:
            if len(str(mailing['media']).split(',')) > 2:
                media = await media_group_formation(mailing['media'], mailing['text'])
                await bot.send_media_group(chat_id=chat_id, media=media)
            else:
                if mailing['media'].split('@@')[1] == 'photo':
                    await bot.send_photo(chat_id=chat_id, photo=mailing['media'].split('@@')[0],
                                         caption=mailing['text'])
                elif mailing['media'].split('@@')[1] == 'animation':
                    await bot.send_animation(chat_id=chat_id, animation=mailing['media'].split('@@')[0],
                                             caption=mailing['text'])
                elif mailing['media'].split('@@')[1] == 'video':
                    await bot.send_video(chat_id=chat_id, video=mailing['media'].split('@@')[0],
                                         caption=mailing['text'])
        else:
            await bot.send_message(chat_id, text=str(mailing['text']))
    except Exception as ex:
        print(ex)


@dp.callback_query_handler(text=['change_mailing'])  # кнопка изменить рассылку
async def change_mailing(call: types.CallbackQuery, state: FSMContext):
    info = await state.get_data()
    await send_mailing(info['id_mailing'], chat_id=call.from_user.id)
    buttons = [
        types.InlineKeyboardButton(text=f"{_('Текст', call.from_user.language_code)}",
                                   callback_data='change_mailing_text'),
        types.InlineKeyboardButton(text=f"{_('Медиа', call.from_user.language_code)}",
                                   callback_data='change_mailing_media')
    ]
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(*buttons)
    await call.message.answer(_('Что хотите изменить?', call.from_user.language_code), reply_markup=keyboard)


@dp.callback_query_handler(text=['change_mailing_media'])  # кнопка изменить медиа рассылки
async def change_media_button(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer(_('Отправьте новое медиа ⬇', call.from_user.language_code))
    await MyStates.change_media_state.set()


@dp.callback_query_handler(state=MyStates.change_media_state,
                           text=['confirm_change_media'])  # подтверждение изменения медиа
async def confirm_change_media(call: types.CallbackQuery, state: FSMContext):
    info = await state.get_data()
    await set_mailing_media_array_in_db(info)
    await call.message.answer(_('Изменения успешно сохранены ✅', call.from_user.language_code))
    await state.set_state(None)


@dp.callback_query_handler(state=MyStates.change_media_state,
                           text=['refuse_change_media'])  # кнопка отмены изменения медиа
async def refuse_change_media(call: types.CallbackQuery, state: FSMContext):
    await bot.delete_message(call.message.chat.id, call.message.message_id)
    await change_mailing(call=call, state=state)
    await state.set_state(None)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text=_('Вернуться в админ панель', call.from_user.language_code),
                                          callback_data='backToAdminPanel'))
    await call.message.answer(_('Рассылка была отменена', call.from_user.language_code), reply_markup=markup)


@dp.callback_query_handler(text=['go_mailing'])  # кнопка сразу запустить рассылку
async def change_text_button(call: types.CallbackQuery, state: FSMContext):
    await state.update_data(instant_mailing=True)
    await add_mailing(call=call)


@dp.callback_query_handler(text=['change_mailing_text'])  # кнопка изменить текст рассылки
async def change_text_button(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer(_('Отправьте новый текст ⬇', call.from_user.language_code))
    await MyStates.change_text_state.set()


@dp.message_handler(state=MyStates.change_text_state, content_types=types.ContentType.TEXT)
async def change_text_mailing(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        text = message.text
        name_mailing = ''
        count = 2
        for i in text.split():
            if count == 0:
                break
            name_mailing += i + ' '
            count -= 1
        await state.update_data(text=text)
        info = await state.get_data()
        mailing = await get_mailing(info['id_mailing'])  # сохранить старый текст на случай отмены изменения
        await state.update_data(old_text=mailing['text'])
        await state.update_data(old_name=mailing['name'])
        await update_mailling_in_db(text, name_mailing, info['id_mailing'])
        await send_mailing(info['id_mailing'], message.from_user.id)
        buttons = [
            types.InlineKeyboardButton(text=_('Да', await get_language(message.from_user.id)), callback_data='confirm_changes_button'),
            types.InlineKeyboardButton(text=_('Нет', await get_language(message.from_user.id)), callback_data='refuse_changes_button')
        ]
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        keyboard.add(*buttons)
        await message.answer(_('Всё верно?', await get_language(message.from_user.id)), reply_markup=keyboard)
        await state.set_state(None)


@dp.callback_query_handler(text=['confirm_changes_button'])  # кнопка подтверждения изменения текста
async def confirm_change_text(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer(_('Изменения успешно сохранены ✅', call.from_user.language_code))
    await mailing_func(call=call)
    await state.finish()


@dp.callback_query_handler(text=['refuse_changes_button'])  # кнопка отмены изменения текста
async def refuse_change_text(call: types.CallbackQuery, state: FSMContext):
    info = await state.get_data()  # нужно вернуть старое значение текста в бд
    await update_mailling_in_db(info['old_text'], info['old_name'], info['id_mailing'])
    await change_mailing(call=call, state=state)
    await call.message.answer(_('Рассылка была отменена', call.from_user.language_code))

@dp.callback_query_handler(text=['run_mailing'])  # ЗАПУСТИТЬ РАССЫЛКУ
async def start_mailing(call: types.CallbackQuery, state: FSMContext):
    await call.answer("")
    await state.update_data(ok_sent=0)
    await state.update_data(error_sent=0)
    info = await state.get_data()
    result = await get_all_userid_from_db()
    for user in result:
        try:
            if 'instant_mailing' in info.keys():  # если мгновенная рассылка, вызываем другую функцию отправки
                if info['instant_mailing']:
                    await send_momental_mailing(state=state, chat_id=user['id'])
                    await state.update_data(ok_sent=info['ok_sent'] + 1)
                    info = await state.get_data()
                    continue
            await send_mailing(info['id_mailing'], chat_id=user['id'])
            await update_mailling_users_count_in_db(False)
            info = await state.get_data()
            await state.update_data(ok_sent=info['ok_sent'] + 1)
            info = await state.get_data()
        except Exception as ex:
            print('Ошибка:\n', traceback.format_exc())
            await update_mailling_users_count_in_db(True)
            info = await state.get_data()
            await state.update_data(error_sent=info['error_sent'] + 1)
    if 'instant_mailing' in info.keys():  # если мгновенная рассылка, не обновляем завершено
        if not info['instant_mailing']:

            await add_mailing_complete_in_db()
            await call.message.answer(
                f"{_('Рассылка завершена', call.from_user.language_code)}!\n"
                f"{_('Успешно', call.from_user.language_code)}: {info['ok_sent']}.\n"
                f"{_('Неуспешно', call.from_user.language_code)}: {info['error_sent']}")
            await state.update_data(instant_mailing=False)
        else:
            await call.message.answer(
                f"{_('Рассылка завершена', call.from_user.language_code)}!\n"
                f"{_('Успешно', call.from_user.language_code)}: {info['ok_sent']}.\n"
                f"{_('Неуспешно', call.from_user.language_code)}: {info['error_sent']}")
            await state.update_data(instant_mailing=False)
            return
    await call.message.answer(f"{_('Рассылка завершена', call.from_user.language_code)}!\n"
                f"{_('Успешно', call.from_user.language_code)}: {info['ok_sent']}.\n"
                f"{_('Неуспешно', call.from_user.language_code)}: {info['error_sent']}")

@dp.callback_query_handler(text=['get_test_mailing'])  # получить тестовую рассылку
async def get_test_mailing(call: types.CallbackQuery, state: FSMContext):
    info = await state.get_data()
    await send_mailing(info['id_mailing'], chat_id=call.from_user.id)
    await call.answer("")


@dp.callback_query_handler(text=['delete_mailing'])  # удалить рассылку
async def get_test_mailing(call: types.CallbackQuery, state: FSMContext):
    info = await state.get_data()
    await delete_mailling_from_db(info['id_mailing'])
    await call.message.answer(_('Рассылка успешно удалена ✅', call.from_user.language_code))
    await mailing_func(call=call)


