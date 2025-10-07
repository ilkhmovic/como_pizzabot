import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiohttp import web
from hashlib import md5
import re
from datetime import datetime

from handlers import router
from db import (
    init_db, get_order_by_id, update_order_status, 
    get_user_data, get_user_language, get_order_items_by_id
)
from keyboards import get_main_keyboard, get_text

# --- KONFIGURATSIYA ---
# Railway environment variables dan olish
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8201136862:AAH91yLSxrTbpO2LSNZ1lu40BivDVTsQWQ4")
PORT = int(os.environ.get("PORT", 8000))
WEBHOOK_HOST = os.environ.get("RAILWAY_STATIC_URL", "https://comopizzabot-production.up.railway.app")

WEBHOOK_PATH = '/webhook'
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

# Click Merchant kabinetidan olingan ma'lumotlar
SECRET_KEY = '4krNcqcYdfSpGD'
SERVICE_ID = '83881'
MERCHANT_ID = '46627'
ADMINS = [7798312047, 7720794522]
DELIVERY_FEE = 100

# --- BOT VA DISPATCHER ---
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
dp.include_router(router)

# --- CLICK YORDAMCHI FUNKSIYALARI ---
def escape_markdown_v2(text):
    """MarkdownV2 formatidagi maxsus belgilarni 'escape' qiladi."""
    if text is None:
        return ""
    text = str(text)
    escape_chars = r'_*[]()~`>#+ -=|{. !}'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

def check_click_request(request_data: dict, action: str) -> bool:
    """Click so'rovining to'g'riligini (md5 hash) tekshiradi."""
    
    try:
        if action == 'prepare':
            data = f"{request_data.get('click_trans_id')}{SERVICE_ID}{SECRET_KEY}{request_data.get('merchant_trans_id')}{request_data.get('amount')}{request_data.get('action')}{request_data.get('sign_time')}"
        elif action == 'complete':
            data = f"{request_data.get('click_trans_id')}{SERVICE_ID}{SECRET_KEY}{request_data.get('merchant_trans_id')}{request_data.get('amount')}{request_data.get('action')}{request_data.get('sign_time')}"
        else:
            return False
            
        generated_sign = md5(data.encode('utf-8')).hexdigest()
        return generated_sign == request_data.get('sign_string')
    except Exception as e:
        logging.error(f"Click signature tekshirishda xato: {e}")
        return False

async def handle_click_prepare(request):
    """Click to'lovni tayyorlash (Prepare) so'rovini qayta ishlaydi."""
    try:
        data = await request.json()
        logging.info(f"Click PREPARE so'rovi: {data}")

        if not check_click_request(data, 'prepare'):
            return web.json_response({
                "error": -1,
                "error_note": "SIGNATURE_CHECK_FAILED"
            })
            
        order_id = data.get('merchant_trans_id')
        amount = float(data.get('amount'))
        order = get_order_by_id(order_id)
        
        if not order:
             return web.json_response({
                 "error": -4, 
                 "error_note": "ORDER_NOT_FOUND"
             })
            
        total_price = float(order[2]) 
        
        if abs(total_price - amount) > 0.01: 
             return web.json_response({
                 "error": -2, 
                 "error_note": "INCORRECT_AMOUNT"
             })

        if order[4] != 'Pending':
             return web.json_response({
                 "error": -5, 
                 "error_note": "ALREADY_PAID"
             })
            
        merchant_prepare_id = order_id 
        update_order_status(order_id, 'Preparing')

        return web.json_response({
            "click_trans_id": data.get('click_trans_id'), 
            "merchant_trans_id": order_id,
            "merchant_prepare_id": merchant_prepare_id, 
            "error": 0, 
            "error_note": "Success"
        })

    except Exception as e:
        logging.error(f"Click Prepare error: {e}")
        return web.json_response({
            "error": -1, 
            "error_note": f"System error: {e}"
        })

async def handle_click_complete(request):
    """Click to'lovni yakunlash (Complete) so'rovini qayta ishlaydi."""
    try:
        data = await request.json()
        logging.info(f"Click COMPLETE so'rovi: {data}")
        
        if not check_click_request(data, 'complete'):
            return web.json_response({
                "error": -1, 
                "error_note": "SIGNATURE_CHECK_FAILED"
            })
            
        order_id = data.get('merchant_trans_id')
        amount = float(data.get('amount'))
        error_code = int(data.get('error', -1))
        order = get_order_by_id(order_id)
        
        if not order:
             return web.json_response({
                 "error": -4, 
                 "error_note": "ORDER_NOT_FOUND"
             })

        total_price = float(order[2])
        if abs(total_price - amount) > 0.01:
             return web.json_response({
                 "error": -2, 
                 "error_note": "INCORRECT_AMOUNT"
             })
            
        if error_code == 0:
            user_id = order[1]
            if order[4] == 'Paid':
                 return web.json_response({
                     "error": -5, 
                     "error_note": "ALREADY_PAID"
                 })
            
            # To'lovni yakunlash (Paid)
            update_order_status(order_id, 'Paid')
            
            # Foydalanuvchiga xabar yuborish
            user_lang = get_user_language(user_id)
            await bot.send_message(
                user_id, 
                get_text(user_lang, 'PAYMENT_SUCCESS').format(order_id=order_id), 
                reply_markup=get_main_keyboard(user_lang)
            )
            
            # Adminlarga xabar berish
            user_data = get_user_data(user_id)
            user_phone = user_data[1] if user_data and user_data[1] else "Noma'lum"
            user_name = order[6] if len(order) > 6 else "Foydalanuvchi"
            
            admin_msg = f"✅ CLICK TO'LOV MUVAFFAQIYATLI:\n"
            admin_msg += f"Buyurtma ID: **{order_id}**\n"
            admin_msg += f"Summa: **{int(amount)} UZS**\n"
            admin_msg += f"Foydalanuvchi: [{user_name}](tg://user?id={user_id})\n"
            admin_msg += f"Tel: `{user_phone}`"
            
            for admin_id in ADMINS:
                await bot.send_message(
                    admin_id, 
                    escape_markdown_v2(admin_msg), 
                    parse_mode='MarkdownV2'
                )
            
            return web.json_response({
                "click_trans_id": data.get('click_trans_id'), 
                "merchant_trans_id": order_id,
                "merchant_confirm_id": data.get('merchant_prepare_id'), 
                "error": 0, 
                "error_note": "Success"
            })
            
        else: # To'lov bekor qilindi
            update_order_status(order_id, 'Canceled')
            user_id = order[1]
            user_lang = get_user_language(user_id)
            await bot.send_message(
                user_id, 
                get_text(user_lang, 'PAYMENT_CANCELLED').format(order_id=order_id),
                reply_markup=get_main_keyboard(user_lang)
            )
            
            return web.json_response({
                "error": -9, 
                "error_note": "TRANSACTION_CANCELLED"
            })

    except Exception as e:
        logging.error(f"Click Complete error: {e}")
        return web.json_response({
            "error": -1, 
            "error_note": f"System error: {e}"
        })

# --- TELEGRAM WEBHOOK HANDLER ---
async def handle_telegram(request):
    try:
        update_data = await request.json()
        update = types.Update(**update_data)
        await dp.feed_update(bot, update)
        return web.Response(status=200)
    except Exception as e:
        logging.error(f"Telegram yangilanishini qayta ishlashda xato: {e}")
        return web.Response(status=500, text=f"Error: {e}")

# --- ASOSIY FUNKSIYA ---
async def main():
    logging.basicConfig(level=logging.INFO)
    
    # Database ni ishga tushirish
    try:
        init_db()
        print("✅ Database ishga tushdi")
    except Exception as e:
        print(f"❌ Database xatosi: {e}")
    
    # Webhook ni o'rnatish
    try:
        await bot.delete_webhook()
        await bot.set_webhook(url=WEBHOOK_URL, drop_pending_updates=True)
        print(f"✅ Webhook o'rnatildi: {WEBHOOK_URL}")
    except Exception as e:
        print(f"❌ Webhook xatosi: {e}")
    
    # Web server yaratish
    app = web.Application()
    
    app.add_routes([
        web.post(WEBHOOK_PATH, handle_telegram),
        web.post('/click/prepare', handle_click_prepare),
        web.post('/click/complete', handle_click_complete),
        web.get('/', lambda request: web.Response(text='🤖 COMO PIZZA BOT ISHLAYAPTI!'))
    ])
    
    # Railway PORT dan foydalanish
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    
    print(f"✅ Server {PORT}-portda ishga tushdi")
    print("🤖 Bot tayyor va ishga tushdi!")
    
    # Server doimiy ishlashi
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
