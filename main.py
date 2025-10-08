import asyncio
import logging
import os
import requests
import json
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
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8201136862:AAH91yLSxrTbpO2LSNZ1lu40BivDVTsQWQ4")
PORT = int(os.environ.get("PORT", 10000))
WEBHOOK_HOST = os.environ.get("WEBHOOK_HOST", "https://como-pizzabot1.onrender.com")

WEBHOOK_PATH = '/webhook'
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

# Click sozlamalari
SECRET_KEY = '4krNcqcYdfSpGD'
SERVICE_ID = '83881'
MERCHANT_ID = '46627'
ADMINS = [7798312047, 7720794522]

# --- BOT VA DISPATCHER ---
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
dp.include_router(router)

# Log sozlamalari
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- FISKALIZATSIYA FUNKSIYALARI ---
async def fiscalize_receipt(order_id: int, amount: float, phone_number: str = "") -> dict:
    """
    Click fiskalizatsiya API orqali chek yaratadi
    """
    try:
        # Buyurtma ma'lumotlarini olish
        order_items = get_order_items_by_id(order_id)
        if not order_items:
            logging.error(f"Fiskalizatsiya: Buyurtma {order_id} uchun mahsulotlar topilmadi")
            return {"success": False, "error": "No order items"}

        # Fiskalizatsiya uchun mahsulotlar ro'yxatini tayyorlash
        items = []
        for item in order_items:
            product_name, quantity, price = item
            items.append({
                "name": product_name,
                "price": price,
                "quantity": quantity,
                "total": price * quantity,
                "vat_percent": 15  # QQS 15%
            })

        # Fiskalizatsiya so'rovi uchun ma'lumotlar
        fiscal_data = {
            "service_id": int(SERVICE_ID),
            "merchant_id": int(MERCHANT_ID),
            "order_id": order_id,
            "amount": amount,
            "phone_number": phone_number or "998901234567",
            "items": items,
            "timestamp": datetime.now().isoformat()
        }

        # Click fiskalizatsiya API ga so'rov
        response = requests.post(
            "https://api.click.uz/v2/merchant/fiscal/receipt",
            json=fiscal_data,
            headers={
                "Content-Type": "application/json",
                "Auth": f"{MERCHANT_ID}:{SECRET_KEY}"
            },
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            if result.get('status') == 0:  # 0 - muvaffaqiyatli
                logging.info(f"Fiskalizatsiya muvaffaqiyatli: Order {order_id}, Receipt ID: {result.get('receipt_id')}")
                return {"success": True, "receipt_id": result.get('receipt_id')}
            else:
                error_msg = result.get('error_msg', 'Noma lum xato')
                logging.error(f"Fiskalizatsiya xatosi: {error_msg}")
                return {"success": False, "error": error_msg}
        else:
            logging.error(f"Fiskalizatsiya HTTP xatosi: {response.status_code} - {response.text}")
            return {"success": False, "error": f"HTTP {response.status_code}"}

    except Exception as e:
        logging.error(f"Fiskalizatsiya jarayonida xato: {e}")
        return {"success": False, "error": str(e)}

async def process_order_fiscalization(order_id: int):
    """Buyurtma uchun fiskalizatsiyani amalga oshiradi"""
    try:
        order = get_order_by_id(order_id)
        if not order:
            logging.error(f"Fiskalizatsiya: Buyurtma {order_id} topilmadi")
            return False

        user_id = order[1]
        amount = order[2]  # total_price
        
        # Foydalanuvchi ma'lumotlarini olish
        user_data = get_user_data(user_id)
        phone_number = user_data[1] if user_data and user_data[1] else ""

        # Fiskalizatsiyani amalga oshirish
        fiscal_result = await fiscalize_receipt(order_id, amount, phone_number)

        # Adminlarga xabar berish
        for admin_id in ADMINS:
            if fiscal_result["success"]:
                await bot.send_message(
                    admin_id,
                    f"Fiskalizatsiya muvaffaqiyatli:\n"
                    f"Buyurtma: #{order_id}\n"
                    f"Summa: {amount} UZS\n"
                    f"Chek ID: {fiscal_result.get('receipt_id', 'Noma lum')}\n"
                    f"Tel: {phone_number or 'Noma lum'}"
                )
            else:
                await bot.send_message(
                    admin_id,
                    f"Fiskalizatsiya xatosi:\n"
                    f"Buyurtma: #{order_id}\n"
                    f"Summa: {amount} UZS\n"
                    f"Xato: {fiscal_result.get('error', 'Noma lum')}\n"
                    f"Iltimos, qo'lda fiskalizatsiya qiling!"
                )

        return fiscal_result["success"]

    except Exception as e:
        logging.error(f"Fiskalizatsiya jarayonida xato: {e}")
        return False

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
        received_sign = request_data.get('sign_string', '')
        
        logging.info(f"Signature tekshirish: Generated={generated_sign}, Received={received_sign}")
        
        return generated_sign == received_sign
    except Exception as e:
        logging.error(f"Signature tekshirish xatosi: {e}")
        return False

async def handle_click_prepare(request):
    """Click to'lovni tayyorlash (Prepare) so'rovini qayta ishlaydi."""
    try:
        data = await request.json()
        logging.info(f"CLICK PREPARE SO'ROVI QABUL QILINDI")
        logging.info(f"Ma'lumotlar: {json.dumps(data, indent=2)}")
        
        # Signature tekshirish
        if not check_click_request(data, 'prepare'):
            logging.error("SIGNATURE TEKSHIRISH XATOSI")
            return web.json_response({
                "error": -1,
                "error_note": "SIGNATURE_CHECK_FAILED"
            })
            
        order_id = data.get('merchant_trans_id')
        amount = float(data.get('amount'))
        
        logging.info(f"Buyurtma ID: {order_id}, Summa: {amount}")
        
        # Buyurtmani tekshirish
        order = get_order_by_id(order_id)
        if not order:
            logging.error(f"BUYURTMA TOPILMADI: {order_id}")
            return web.json_response({
                "error": -4, 
                "error_note": "ORDER_NOT_FOUND"
            })
            
        total_price = float(order[2])
        logging.info(f"Bazadagi summa: {total_price}, Kelgan summa: {amount}")
        
        # Summa tekshirish
        if abs(total_price - amount) > 1:  # 1 so'm farqga ruxsat
            logging.error(f"SUMMA MOS KELMAYDI: Bazada {total_price}, Kelgan {amount}")
            return web.json_response({
                "error": -2, 
                "error_note": "INCORRECT_AMOUNT"
            })

        # Holat tekshirish
        if order[4] != 'Pending':
            logging.error(f"BUYURTMA HOLATI: {order[4]}")
            return web.json_response({
                "error": -5, 
                "error_note": "ALREADY_PAID"
            })
            
        # Holatni yangilash
        update_order_status(order_id, 'Preparing')
        logging.info(f"PREPARE MUVAFFAQIYATLI: {order_id}")

        return web.json_response({
            "click_trans_id": data.get('click_trans_id'), 
            "merchant_trans_id": order_id,
            "merchant_prepare_id": order_id, 
            "error": 0, 
            "error_note": "Success"
        })

    except Exception as e:
        logging.error(f"PREPARE XATOSI: {str(e)}")
        import traceback
        logging.error(f"XATO TAFSILOTLARI: {traceback.format_exc()}")
        return web.json_response({
            "error": -1, 
            "error_note": f"System error: {str(e)}"
        })

async def handle_click_complete(request):
    """Click to'lovni yakunlash (Complete) so'rovini qayta ishlaydi."""
    try:
        data = await request.json()
        logging.info(f"CLICK COMPLETE SO'ROVI QABUL QILINDI")
        logging.info(f"Ma'lumotlar: {json.dumps(data, indent=2)}")
        
        # Signature tekshirish
        if not check_click_request(data, 'complete'):
            logging.error("SIGNATURE TEKSHIRISH XATOSI")
            return web.json_response({
                "error": -1, 
                "error_note": "SIGNATURE_CHECK_FAILED"
            })
            
        order_id = data.get('merchant_trans_id')
        amount = float(data.get('amount'))
        error_code = int(data.get('error', -1))
        
        logging.info(f"Complete: Order {order_id}, Amount {amount}, Error {error_code}")
        
        # Buyurtma tekshirish
        order = get_order_by_id(order_id)
        if not order:
            logging.error(f"BUYURTMA TOPILMADI: {order_id}")
            return web.json_response({
                "error": -4, 
                "error_note": "ORDER_NOT_FOUND"
            })

        # Summa tekshirish
        total_price = float(order[2])
        if abs(total_price - amount) > 1:
            logging.error(f"SUMMA MOS KELMAYDI: Bazada {total_price}, Kelgan {amount}")
            return web.json_response({
                "error": -2, 
                "error_note": "INCORRECT_AMOUNT"
            })
            
        if error_code == 0:
            user_id = order[1]
            
            # To'lov allaqachon amalga oshirilganligini tekshirish
            if order[4] == 'Paid':
                logging.warning(f"TO'LOV ALLAQACHON AMALGA OSHIRILGAN: {order_id}")
                return web.json_response({
                    "error": -5, 
                    "error_note": "ALREADY_PAID"
                })
            
            # To'lovni yakunlash
            update_order_status(order_id, 'Paid')
            logging.info(f"TO'LOV MUVAFFAQIYATLI: {order_id}")
            
            # FISKALIZATSIYANI ISHGA TUSHIRISH
            fiscal_success = await process_order_fiscalization(order_id)
            
            # Foydalanuvchiga xabar
            user_lang = get_user_language(user_id)
            message_text = get_text(user_lang, 'PAYMENT_SUCCESS').format(order_id=order_id)
            
            # Agar fiskalizatsiya muvaffaqiyatli bo'lsa, qo'shimcha xabar
            if fiscal_success:
                message_text += "\n\nChek fiskalizatsiya qilindi. Elektron chek telefondagi Click ilovasida ko'rinadi."
            
            await bot.send_message(
                user_id, 
                message_text, 
                reply_markup=get_main_keyboard(user_lang)
            )
            
            # Adminlarga xabar
            user_data = get_user_data(user_id)
            user_phone = user_data[1] if user_data and user_data[1] else "Noma'lum"
            user_name = order[6] if len(order) > 6 else "Foydalanuvchi"
            
            admin_msg = f"TO'LOV MUVAFFAQIYATLI:\n"
            admin_msg += f"Buyurtma ID: {order_id}\n"
            admin_msg += f"Summa: {int(amount)} UZS\n"
            admin_msg += f"Foydalanuvchi: {user_name}\n"
            admin_msg += f"Tel: {user_phone}\n"
            admin_msg += f"Fiskalizatsiya: {'Muvaffaqiyatli' if fiscal_success else 'Xatolik'}"
            
            for admin_id in ADMINS:
                await bot.send_message(admin_id, admin_msg)
            
            return web.json_response({
                "click_trans_id": data.get('click_trans_id'), 
                "merchant_trans_id": order_id,
                "merchant_confirm_id": data.get('merchant_prepare_id'), 
                "error": 0, 
                "error_note": "Success"
            })
            
        else:
            # To'lov bekor qilindi
            update_order_status(order_id, 'Canceled')
            user_id = order[1]
            user_lang = get_user_language(user_id)
            
            logging.warning(f"TO'LOV BEKOR QILINDI: {order_id}, Error: {error_code}")
            
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
        logging.error(f"COMPLETE XATOSI: {str(e)}")
        import traceback
        logging.error(f"XATO TAFSILOTLARI: {traceback.format_exc()}")
        return web.json_response({
            "error": -1, 
            "error_note": f"System error: {str(e)}"
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
    logging.info("Bot ishga tushmoqda...")
    
    # Database ni ishga tushirish
    try:
        init_db()
        logging.info("Database ishga tushdi")
    except Exception as e:
        logging.error(f"Database xatosi: {e}")
    
    # Webhook ni o'rnatish
    try:
        await bot.delete_webhook()
        await bot.set_webhook(url=WEBHOOK_URL, drop_pending_updates=True)
        logging.info(f"Webhook o'rnatildi: {WEBHOOK_URL}")
    except Exception as e:
        logging.error(f"Webhook xatosi: {e}")
    
    # Web server yaratish
    app = web.Application()
    
    app.add_routes([
        web.post(WEBHOOK_PATH, handle_telegram),
        web.post('/click/prepare', handle_click_prepare),
        web.post('/click/complete', handle_click_complete),
        web.get('/', lambda request: web.Response(text='BOT ISHLAYAPTI!'))
    ])
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    
    logging.info(f"Server {PORT}-portda ishga tushdi")
    logging.info("Bot tayyor!")
    
    # Server doimiy ishlashi
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
