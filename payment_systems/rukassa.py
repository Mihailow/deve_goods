import aiohttp
import json
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta

from postgres import commands_to_db
from misc import bot, dp, scheduler

rukassa_token = "a709237437d7cb23c7ed49d688896620"
rukassa_id = "1338"


class RukassaPayment:

    @classmethod
    async def create_payment(cls, user_id: int, amount: float, comment: str):

        async def check_payment():
            if await cls.is_payment_paid(payment_id=payment_id):
                scheduler.remove_job(job_id=comment)
                await commands_to_db.update_payment(comment=comment, amount=amount, user_id=user_id,
                                                    payment_status="completed")
                state = dp.get_current().current_state(user=user_id)
                await state.finish()
                await bot.send_message(chat_id=user_id,
                                       text=f"[✓] Вы успешно оплатили счет. На баланс зачислено {amount} рублей.")

            payment_date = await commands_to_db.PaymentDate(comment=comment)
            time_now = datetime.now()
            time_dif = abs(time_now - payment_date['date'])

            if time_dif >= timedelta(seconds=30):
                scheduler.remove_job(job_id=comment)
                await commands_to_db.update_payment(comment=comment, amount=amount, user_id=user_id,
                                                    payment_status="canceled")
                state = dp.get_current().current_state(user=user_id)
                await state.finish()
                await bot.send_message(chat_id=user_id,
                                       text="[!] Вы не оплатили счёт в течение часа. Платеж был отклонен.")

        async with aiohttp.ClientSession() as session:
            async with session.post('https://lk.rukassa.pro/api/v1/create',
                                    params={'shop_id': rukassa_id, 'order_id': comment, 'amount': amount,
                                            'token': rukassa_token}) as resp:
                response = await resp.read()
                invoice = json.loads(response)

        payment_url = invoice['url']
        payment_id = invoice['id']

        await commands_to_db.add_payment(comment=comment, user_id=user_id, amount=amount)

        scheduler.add_job(check_payment,
                          trigger=IntervalTrigger(seconds=10),
                          id=comment)

        return payment_url

    @classmethod
    async def get_payment_link(cls, payment_url):
        return payment_url

    @classmethod
    async def is_payment_paid(cls, payment_id):
        url = 'https://lk.rukassa.pro/api/v1/getPayInfo'
        async with aiohttp.ClientSession() as session:
            async with session.post(url,
                                    params={'id': payment_id, 'shop_id': rukassa_id, 'token': rukassa_token}) as resp:
                response = await resp.read()
                json_str = json.loads(response)
                status = json_str['status']
                return status == 'PAID'
