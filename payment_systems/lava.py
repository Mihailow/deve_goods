from LavaBusiness import AioLava
from postgres import commands_to_db
from datetime import datetime
import aioschedule
import asyncio

from misc import bot, dp

SECRET_KEY = "TEST"
PROJECT_ID = "TEST"

api = AioLava(SECRET_KEY, PROJECT_ID)


class LavaPayment:

    @classmethod
    async def create_payment(cls, user_id: int, amount: float, comment: str):
        """
        Создание платежа
        :param user_id:
        :param amount:
        :param comment:
        :return:
        """

        async def check_payment(check_job):
            """
            Проверяем, что платеж оплачен и не был просрочен
            :return:
            """

            nonlocal stop_checking
            if await cls.is_payment_paid(invoice):
                aioschedule.cancel_job(check_job)
                await commands_to_db.update_payment(comment=comment, amount=amount, user_id=user_id,
                                              payment_status="completed")
                state = dp.get_current().current_state(user=user_id)
                await state.finish()
                await bot.send_message(chat_id=user_id,
                                       text=f"[✓] Вы успешно оплатили счет. На баланс зачислено {amount} рублей.")
                return
            past_seconds = (datetime.now() - created_at).seconds
            past_minutes = past_seconds // 60
            past_hours = past_minutes // 60

            if past_hours >= 1:
                stop_checking = True
                await commands_to_db.update_payment(comment=comment, amount=amount, user_id=user_id,
                                              payment_status="canceled")
                state = dp.get_current().current_state(user=user_id)
                await state.finish()
                await bot.send_message(chat_id=user_id,
                                       text="[!] Вы не оплатили счёт в течение часа. Платеж был отклонен.")

        async def payment_scheduler():
            check_job = aioschedule.every(10).seconds.do(lambda: check_payment(check_job))
            while not stop_checking:
                await aioschedule.run_pending()
                await asyncio.sleep(5)

        print(amount, comment)
        invoice = await api.create_invoice(amount)
        created_at = await commands_to_db.add_payment(comment=comment, amount=amount, user_id=user_id)
        stop_checking = False

        asyncio.create_task(payment_scheduler())

        return invoice

    @classmethod
    async def get_payment_link(cls, invoice):
        """
        Получение ссылки для оплаты
        :param payment:
        :return:
        """
        return invoice.url

    @classmethod
    async def is_payment_paid(cls, invoice):
        """
        Проверка оплачен ли платеж
        :param invoice:
        :return:
        """
        status = await api.invoice_status(invoice.invoice_id)
        return status == 'success'