import aiohttp
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta

from postgres import commands_to_db
from misc import bot, dp, scheduler

PROJECT_ID = 00
SECRET_KEY = 'test'

class P2PKassaPayment:
    
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
                
        create_invoice_url = 'https://p2pkassa.online/api/v1/link'
        
        data = {
            'project_id':PROJECT_ID,
            'order_id':comment,
            'amount':amount,
            'apikey':SECRET_KEY
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(create_invoice_url, data=data) as resp:
                resp = await resp.json(content_type=None)
                
                payment_id = resp['id']
                payment_url = resp['link']
                
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
        check_payment_url = 'https://p2pkassa.online/api/v1/getPayment'
        
        data = {
            'id':payment_id,
            'project_id':PROJECT_ID,
            'apikey':SECRET_KEY
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(check_payment_url, data=data) as resp:
                resp = await resp.json(content_type=None)
                
                status = resp['status']
                
        return status == 'paid'