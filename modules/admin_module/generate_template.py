from modules.admin_module.commands_to_db import get_count_and_sum_orders_by_period, get_count_registered_users_by_period
from postgres.commands_to_db import get_language
from translations import _


async def generate_admin_menu_template(message):
    today_order_count, today_order_sum = await get_count_and_sum_orders_by_period('today')
    week_order_count, week_order_sum = await get_count_and_sum_orders_by_period('1 week')
    month_order_count, month_order_sum = await get_count_and_sum_orders_by_period('1 month')
    yesterday_order_count, yesterday_order_sum = await get_count_and_sum_orders_by_period('1 day')

    last_week_order_count, last_week_order_sum = await get_count_and_sum_orders_by_period('lastWeek')
    last_month_order_count, last_month_order_sum = await get_count_and_sum_orders_by_period('lastMonth')

    two_days_ago_order_count, two_days_ago_order_sum = await get_count_and_sum_orders_by_period('2 day', '1 day')
    two_week_ago_order_count, two_week_ago_order_sum = await get_count_and_sum_orders_by_period('2 week', '1 week')
    two_month_ago_order_count, two_month_ago_order_sum = await get_count_and_sum_orders_by_period('twoMonthAgo')

    order_count, order_sum = await get_count_and_sum_orders_by_period()

    return f"""🥷<b>{_('Админ панель', await get_language(message.from_user.id))}</b>🥷

{_('Бот', await get_language(message.from_user.id))}: 
{_('Ник', await get_language(message.from_user.id))}: 
{_('Статус', await get_language(message.from_user.id))}: 
{_('Тариф', await get_language(message.from_user.id))}: 
{_('Создан', await get_language(message.from_user.id))}: 

<b>{_('Информация о пользователях', await get_language(message.from_user.id))}</b>:
{_('За день новых', await get_language(message.from_user.id))}: {await get_count_registered_users_by_period('1 day')}
{_('За неделю новых', await get_language(message.from_user.id))}:  {await get_count_registered_users_by_period('1 week')}
{_('За месяц новых', await get_language(message.from_user.id))}: {await get_count_registered_users_by_period('1 month')}
{_('Всего пользователей', await get_language(message.from_user.id))}: {await get_count_registered_users_by_period(period=None)}

{_('Активные', await get_language(message.from_user.id))}:
{_('Неактивные', await get_language(message.from_user.id))}:

<b>{_('Информация о заказах', await get_language(message.from_user.id))}</b>:
{_('За день новых', await get_language(message.from_user.id))}: {today_order_count} ({today_order_sum})₽
{_('За неделю новых', await get_language(message.from_user.id))}: {week_order_count} ({week_order_sum})₽
{_('За месяц новых', await get_language(message.from_user.id))}:  {month_order_count} ({month_order_sum})₽
{_('Вчера', await get_language(message.from_user.id))}: {yesterday_order_count} ({yesterday_order_sum})₽
{_('За прошлую неделю', await get_language(message.from_user.id))}: {last_week_order_count} ({last_week_order_sum})₽
{_('За прошлый месяц', await get_language(message.from_user.id))}: {last_month_order_count}  ({last_month_order_sum})₽
{_('Позавчера', await get_language(message.from_user.id))}: {two_days_ago_order_count}  ({two_days_ago_order_sum})₽
{_('За позапрошлую неделю', await get_language(message.from_user.id))}: {two_week_ago_order_count} ({two_week_ago_order_sum})₽
{_('За позапрошлый месяц', await get_language(message.from_user.id))}: {two_month_ago_order_count}  ({two_month_ago_order_sum})₽

{_('Всего заказов', await get_language(message.from_user.id))}: {order_count} ({order_sum})₽"""