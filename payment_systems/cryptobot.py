from aiocryptopay import AioCryptoPay, Networks
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta

from postgres import commands_to_db
from misc import bot, dp, scheduler

SECRET_KEY = 'test'

api = AioCryptoPay(SECRET_KEY, network=Networks.MAIN_NET)
asset = 'USDT'

class CrytobotPayment:
    
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
                
        invoice = await api.create_invoice(asset=asset,
                                     amount=await cls.get_crypto_bot_sum(amount=amount, currency=asset),
                                     description=comment)
        
        payment_url = invoice.pay_url
        payment_id = invoice.invoice_id
        
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
        invoice = await api.get_invoices(invoice_ids=payment_id)
        await api.close()
        
        status = invoice.status
        
        return status == 'paid'
    
    @classmethod
    async def get_crypto_bot_sum(cls, amount: float, currency: str):
        cryptopay = AioCryptoPay(SECRET_KEY)
        courses = await cryptopay.get_exchange_rates()
        await cryptopay.close()
        for course in courses:
            if course.source == currency and course.target == 'RUB':
                return amount / course.rate