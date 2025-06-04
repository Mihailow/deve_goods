from config import telegram_token
from postgres.postgres_handler import postgress_select_one


async def get_count_and_sum_orders_by_period(lower_limit=None, upper_limit=None):
    result = None
    if lower_limit is None and upper_limit is None:
        result = postgress_select_one(
            "SELECT COUNT(*), SUM(price) FROM orders WHERE token = %s AND status = 'Complete';",
            (telegram_token,))
    elif upper_limit is None:
        if lower_limit == 'today':
            result = postgress_select_one(
                f"SELECT COUNT(*), SUM(price) FROM orders WHERE token = %s AND "
                f"time >= CURRENT_DATE AND time < CURRENT_DATE + INTERVAL '1 day' AND "
                f"status = 'Complete';", (telegram_token,))
        elif lower_limit == 'lastMonth':
            result = postgress_select_one(
                f"SELECT COUNT(*), SUM(price) FROM orders WHERE token = %s AND "
                f"time >= date_trunc('month', CURRENT_DATE - interval '1 month') AND "
                f"time < date_trunc('month', CURRENT_DATE) AND status = 'Complete';", (telegram_token,))
        elif lower_limit == 'lastWeek':
            result = postgress_select_one(
                f"SELECT COUNT(*), SUM(price) FROM orders WHERE token = %s AND "
                f"time >= date_trunc('week', CURRENT_DATE - interval '1 week') AND "
                f"time < date_trunc('week', CURRENT_DATE) AND status = 'Complete';", (telegram_token,))
        elif lower_limit == 'twoMonthAgo':
            result = postgress_select_one(
                f"SELECT COUNT(*), SUM(price) FROM orders WHERE token = %s AND "
                f"time >= DATE_TRUNC('MONTH', CURRENT_DATE - INTERVAL '2 month') AND "
                f"time < DATE_TRUNC('MONTH', CURRENT_DATE - INTERVAL '1 month') AND "
                f"status = 'Complete';", (telegram_token,))
        else:
            if lower_limit == '1 week':
                result = postgress_select_one(
                    f"SELECT COUNT(*), SUM(price) FROM orders WHERE token = %s  AND "
                    f"time >= CURRENT_DATE - INTERVAL '1 week' AND time < CURRENT_DATE AND "
                    f"status = 'Complete';", (telegram_token,))
            if lower_limit == '1 month':
                result = postgress_select_one(
                    f"SELECT COUNT(*), SUM(price) FROM orders WHERE token = %s  AND "
                    f"time >= CURRENT_DATE - INTERVAL '1 month' AND time < CURRENT_DATE AND "
                    f"status = 'Complete';", (telegram_token,))
            if lower_limit == '1 day':
                result = postgress_select_one(
                    f"SELECT COUNT(*), SUM(price) FROM orders WHERE token = %s  AND "
                    f"time >= CURRENT_DATE - INTERVAL '1 day' AND time < CURRENT_DATE AND "
                    f"status = 'Complete';", (telegram_token,))
    else:
        if lower_limit == '2 day' and upper_limit == '1 day':
            result = postgress_select_one(
                f"SELECT COUNT(*), SUM(price) FROM orders WHERE token = %s AND "
                f"time >= CURRENT_DATE - INTERVAL '2 day' AND time < CURRENT_DATE - INTERVAL '1 day' AND "
                f"status = 'Complete';", (telegram_token,))

        if lower_limit == '2 week' and upper_limit == '1 week':
            result = postgress_select_one(
                f"SELECT COUNT(*), SUM(price) FROM orders WHERE token = %s AND "
                f"time >= CURRENT_DATE - INTERVAL '2 week' AND time < CURRENT_DATE - INTERVAL '1 week' AND "
                f"status = 'Complete';", (telegram_token,))
    if result['sum'] is None:
        result['sum'] = 0
    return result['count'], result['sum']

async def get_count_registered_users_by_period(period):
    if period is None:
        result = postgress_select_one(f"SELECT COUNT(*) FROM users WHERE token = %s;", (telegram_token,))
    else:
        if period == '1 day':
            result = postgress_select_one(f"SELECT COUNT(*) FROM users WHERE token = %s AND "
                                          f"date_registration >= NOW() - INTERVAL '1 day';", (telegram_token,))
        if period == '1 week':
            result = postgress_select_one(f"SELECT COUNT(*) FROM users WHERE token = %s AND "
                                          f"date_registration >= NOW() - INTERVAL '1 week';", (telegram_token,))
        if period == '1 month':
            result = postgress_select_one(f"SELECT COUNT(*) FROM users WHERE token = %s AND "
                                          f"date_registration >= NOW() - INTERVAL '1 month';", (telegram_token,))
    return result['count']




