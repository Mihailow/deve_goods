from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta

from LolzteamApi import LolzteamApi

from postgres import commands_to_db
from misc import bot, dp, payments_scheduler


lolz_token = 'df8d4b25b37a395aa9fbefe82c0709759be68c78'
lolz_user_id = 7620848
lolz_username = 'bram_mi'

api = LolzteamApi(lolz_token)


class LolzteamPayment:

    @classmethod
    async def create_payment(cls, user_id: int, amount: float, comment: str):

        async def check_payment():
            if await cls.is_payment_paid(comment, amount):
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

        payment_url = api.market.payments.generate_link(amount=amount, username=lolz_username, comment=comment)

        await commands_to_db.add_payment(comment=comment, user_id=user_id, amount=amount)

        scheduler.add_job(check_payment,
                          trigger=IntervalTrigger(seconds=10),
                          id=comment)

        return payment_url

    @classmethod
    async def get_payment_link(cls, payment_url):
        return payment_url

    @classmethod
    async def is_payment_paid(cls, comment, amount):
        invoice = api.market.payments.history(user_id=lolz_user_id, operation_type='income', pmin=amount, pmax=amount,
                                              comment=comment)
        if "errors" not in invoice:
            if not invoice["payments"]:
                return False
            else:
                return True
        return False