import asyncio
import logging
import os
import requests
import json
from decimal import Decimal, ROUND_HALF_UP
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
PORT = int(os.environ.get("PORT", 8000))
WEBHOOK_HOST = os.environ.get("WEBHOOK_HOST", "https://como-pizzabot1.onrender.com")
WEBHOOK_PATH = '/webhook'
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

# Click sozlamalari
SECRET_KEY = '4krNcqcYdfSpGD'  # Click tizimidan olingan maxfiy kalit
SERVICE_ID = '83881'
MERCHANT_ID = '46627'
MERCHANT_USER_ID = '65032'  # Yangi qo'shilgan
ADMINS = [7798312047, 7720794522]

# --- BOT VA DISPATCHER ---
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
dp.include_router(router)

# Log sozlamalari
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def parse_click_data(request):
    """Click so'rovini JSON yoki form-data formatida parse qiladi"""
    try:
        content_type = request.headers.get('Content-Type', '').lower()
       
        if 'application/json' in content_type:
            data = await request.json()
            logger.info(f"🟡 JSON DATA QABUL QILINDI: {data}")
            return data
        elif 'application/x-www-form-urlencoded' in content_type:
            post_data = await request.post()
            data = dict(post_data)
            logger.info(f"🟡 FORM-DATA QABUL QILINDI: {data}")
            return data
        else:
            try:
                data = await request.json()
                logger.info(f"🟡 JSON (auto) QABUL QILINDI: {data}")
                return data
            except:
                try:
                    post_data = await request.post()
                    data = dict(post_data)
                    logger.info(f"🟡 FORM-DATA (auto) QABUL QILINDI: {data}")
                    return data
                except Exception as e:
                    logger.error(f"🔴 IKKALA USULDA HAM XATO: {e}")
                    try:
                        body = await request.text()
                        logger.info(f"🟡 RAW BODY: {body}")
                        if body:
                            data = json.loads(body)
                            return data
                        else:
                            return {}
                    except:
                        return {}
               
    except Exception as e:
        logger.error(f"🔴 DATA PARSE XATOSI: {e}")
        return {}

def check_click_request(request_data: dict, action: str) -> bool:
    """Click to'lov so'rovining imzosini (signature) tekshiradi."""
    try:
        logger.info(f"🟡 SIGNATURE TEKSHIRISH: {action}")

        # --- Ma'lumotlarni olish ---
        click_trans_id = str(request_data.get('click_trans_id', '')).strip()
        merchant_trans_id = str(request_data.get('merchant_trans_id', '')).strip()

        # Amountni Click talabiga binoan har doim ikki kasr bilan formatlaymiz
        # (Click sign hisobida ham ko'pincha 2 kasr ishlatiladi)
        raw_amount = str(request_data.get('amount', '0')).strip()
        try:
            # float->format to ensure "1100" -> "1100.00" and "1100.0" -> "1100.00"
            amount = "{:.2f}".format(float(raw_amount))
        except Exception as e:
            logger.error(f"🔴 AMOUNT FORMAT XATOSI: {e} | Kelgan qiymat: {raw_amount}")
            return False

        logger.info(f"🟡 AMOUNT (FORMATTED FOR SIGN): {amount}")

        # action parametri 'prepare' -> 0, 'complete' -> 1
        expected_action = '0' if action == 'prepare' else '1'
        action_str = str(request_data.get('action', '')).strip()
        if action_str != expected_action:
            logger.error(f"🔴 ACTION NOMUVOFIQ: Keldi={action_str}, Kutilgan={expected_action}")
            return False

        # sign_time — kelgan ko‘rinishda olinadi
        sign_time = str(request_data.get('sign_time', '')).strip()

        # complete uchun merchant_prepare_id (faqat complete uchun qo'shiladi)
        merchant_prepare_id = ''
        if action == 'complete':
            merchant_prepare_id = str(request_data.get('merchant_prepare_id', '')).strip() or ''

        # Logga chiqaramiz (diagnostika uchun)
        logger.info(
            f"🟡 Maydonlar:\n"
            f"  click_trans_id={click_trans_id}\n"
            f"  service_id={SERVICE_ID}\n"
            f"  secret_key={SECRET_KEY}\n"
            f"  merchant_trans_id={merchant_trans_id}\n"
            f"  amount={amount}\n"
            f"  action={action_str}\n"
            f"  sign_time={sign_time}\n"
            f"  merchant_prepare_id={merchant_prepare_id}"
        )

        # --- Data string yaratish (Click hujjatlariga muvofiq, hech qanday qo'shimcha belgilar bilan emas) ---
        if action == 'prepare':
            data_string = (
                f"{click_trans_id}{SERVICE_ID}{SECRET_KEY}"
                f"{merchant_trans_id}{amount}{action_str}{sign_time}"
            )
        elif action == 'complete':
            data_string = (
                f"{click_trans_id}{SERVICE_ID}{SECRET_KEY}"
                f"{merchant_trans_id}{amount}{action_str}{sign_time}{merchant_prepare_id}"
            )
        else:
            logger.error(f"🔴 NOMA'LUM ACTION: {action}")
            return False

        logger.info(f"🟡 DATA STRING: {data_string}")
        logger.info(f"🟡 COMPLETE SIGN CHECK: merchant_prepare_id (kelgan) = {merchant_prepare_id}")

        # --- MD5 imzo yaratish va solishtirish ---
        generated_sign = md5(data_string.encode('utf-8')).hexdigest()
        received_sign = str(
            request_data.get('sign_string') or 
            request_data.get('sign') or 
            request_data.get('signature') or ''
        ).strip()

        logger.info(f"🟡 SIGNATURE: Generated={generated_sign}, Received={received_sign}")

        if generated_sign != received_sign:
            logger.error("🔴 SIGNATURE MOS KELMADI ❌")
            return False

        logger.info("✅ SIGNATURE MOS KELDI ✅")
        return True

    except Exception as e:
        logger.error(f"🔴 SIGNATURE TEKSHIRISHDA XATOLIK: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def handle_click_prepare(request):
    """Click to'lovni tayyorlash (Prepare) so'rovini qayta ishlaydi."""
    try:
        logger.info(f"🟡 CLICK PREPARE SO'ROVI: Method={request.method}")
       
        # Ma'lumotlarni parse qilish
        data = await parse_click_data(request)
        logger.info(f"🟡 PREPARE DATA: {data}")
       
        if not data:
            logger.error("🔴 BO'SH DATA QABUL QILINDI")
            return web.json_response({
                "error": -1,
                "error_note": "EMPTY_DATA"
            })
       
        # Signature tekshirish
        if not check_click_request(data, 'prepare'):
            logger.error("🔴 SIGNATURE TEKSHIRISH XATOSI")
            return web.json_response({
                "error": -1,
                "error_note": "SIGNATURE_CHECK_FAILED"
            })
           
        order_id = data.get('merchant_trans_id')
        amount_str = data.get('amount', '0')
       
        try:
            amount = float(amount_str)
        except ValueError:
            logger.error(f"🔴 NOTO'G'RI SUMMA: {amount_str}")
            return web.json_response({
                "error": -2,
                "error_note": "INVALID_AMOUNT"
            })
       
        logger.info(f"🟡 BUYURTMA: ID={order_id}, SUMMA={amount}")
       
        # Buyurtmani tekshirish
        order = get_order_by_id(order_id)
        if not order:
            logger.error(f"🔴 BUYURTMA TOPILMADI: {order_id}")
            return web.json_response({
                "error": -4,
                "error_note": "ORDER_NOT_FOUND"
            })
           
        total_price = float(order[2])
        logger.info(f"🟡 SUMMA TEKSHIRISH: Bazada={total_price}, Kelgan={amount}, Farq={abs(total_price - amount)}")
       
        # Summa tekshirish (1 so'm farqga ruxsat)
        if abs(total_price - amount) > 1:
            logger.error(f"🔴 SUMMA MOS KELMAYDI: Bazada {total_price}, Kelgan {amount}")
            return web.json_response({
                "error": -2,
                "error_note": "INCORRECT_AMOUNT"
            })
       
        # Holat tekshirish
        current_status = order[4] if len(order) > 4 else 'Noma lum'
        logger.info(f"🟡 BUYURTMA HOLATI: {current_status}")
       
        if current_status != 'Pending':
            logger.error(f"🔴 NOTO'G'RI HOLAT: {current_status}")
            return web.json_response({
                "error": -5,
                "error_note": "ALREADY_PAID"
            })
           
        # Holatni yangilash
        update_order_status(order_id, 'Preparing')
        logger.info(f"✅ PREPARE MUVAFFAQIYATLI: {order_id}")
        return web.json_response({
            "click_trans_id": data.get('click_trans_id'),
            "merchant_trans_id": order_id,
            "merchant_prepare_id": order_id,
            "error": 0,
            "error_note": "Success"
        })
    except Exception as e:
        logger.error(f"🔴 PREPARE XATOSI: {str(e)}")
        import traceback
        logger.error(f"🔴 XATO TAFSILOTLARI: {traceback.format_exc()}")
        return web.json_response({
            "error": -1,
            "error_note": f"System error: {str(e)}"
        })

async def handle_click_complete(request):
    """Click to'lovni yakunlash (Complete) so'rovini qayta ishlaydi."""
    try:
        logger.info(f"🟡 CLICK COMPLETE SO'ROVI: Method={request.method}")
       
        # GET so'rovini tekshirish (return_url uchun)
        if request.method == 'GET':
            query_params = dict(request.query)
            logger.info(f"🟡 GET SO'ROVI (return_url): {query_params}")
           
            html_response = """
            <html>
                <head>
                    <title>To'lov Muvaffaqiyatli</title>
                    <meta charset="utf-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1">
                </head>
                <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px; background-color: #f5f5f5;">
                    <div style="max-width: 500px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                        <h1 style="color: #22c55e; margin-bottom: 20px;">✅ To'lov Muvaffaqiyatli!</h1>
                        <p style="font-size: 18px; color: #333; margin-bottom: 30px;">To'lov muvaffaqiyatli amalga oshirildi. Telegram botingizga qayting va buyurtma holatini tekshiring.</p>
                        <a href="https://t.me/ComoPizzaUzBot" style="display: inline-block; background-color: #0088cc; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-size: 16px;">Botga qaytish</a>
                    </div>
                </body>
            </html>
            """
            return web.Response(text=html_response, content_type='text/html')
       
        # POST so'rovini qayta ishlash (Click serverdan)
        data = await parse_click_data(request)
        logger.info(f"🟡 COMPLETE DATA: {data}")
       
        if not data:
            logger.error("🔴 BO'SH DATA QABUL QILINDI")
            return web.json_response({
                "error": -1,
                "error_note": "EMPTY_DATA"
            })
       
        # Signature tekshirish
        if not check_click_request(data, 'complete'):
            logger.error("🔴 SIGNATURE TEKSHIRISH XATOSI")
            return web.json_response({
                "error": -1,
                "error_note": "SIGNATURE_CHECK_FAILED"
            })
           
        order_id = data.get('merchant_trans_id')
        amount_str = data.get('amount', '0')
        error_code = int(data.get('error', -1))
       
        try:
            amount = float(amount_str)
        except ValueError:
            logger.error(f"🔴 NOTO'G'RI SUMMA: {amount_str}")
            return web.json_response({
                "error": -2,
                "error_note": "INVALID_AMOUNT"
            })
       
        logger.info(f"🟡 COMPLETE: Order={order_id}, Amount={amount}, Error={error_code}")
       
        # Buyurtma tekshirish
        order = get_order_by_id(order_id)
        if not order:
            logger.error(f"🔴 BUYURTMA TOPILMADI: {order_id}")
            return web.json_response({
                "error": -4,
                "error_note": "ORDER_NOT_FOUND"
            })
       
        # Summa tekshirish
        total_price = float(order[2])
        if abs(total_price - amount) > 1:
            logger.error(f"🔴 SUMMA MOS KELMAYDI: Bazada {total_price}, Kelgan {amount}")
            return web.json_response({
                "error": -2,
                "error_note": "INCORRECT_AMOUNT"
            })
           
        if error_code == 0:
            user_id = order[1]
           
            # To'lov allaqachon amalga oshirilganligini tekshirish
            current_status = order[4] if len(order) > 4 else 'Noma lum'
            if current_status == 'Paid':
                logger.warning(f"🟡 TO'LOV ALLAQACHON AMALGA OSHIRILGAN: {order_id}")
                return web.json_response({
                    "error": -5,
                    "error_note": "ALREADY_PAID"
                })
           
            # To'lovni yakunlash
            update_order_status(order_id, 'Paid')
            logger.info(f"✅ TO'LOV MUVAFFAQIYATLI: {order_id}")
           
            # Foydalanuvchiga xabar
            user_lang = get_user_language(user_id)
            try:
                await bot.send_message(
                    user_id,
                    f"✅ Buyurtma №{order_id} uchun to'lov muvaffaqiyatli amalga oshirildi!\n\n💰 Summa: {int(amount)} UZS\n\nBuyurtmangiz tez orada yetkazib beriladi.",
                    reply_markup=get_main_keyboard(user_lang)
                )
                logger.info(f"✅ FOYDALANUVCHIGA XABAR YUBORILDI: {user_id}")
            except Exception as e:
                logger.error(f"🔴 FOYDALANUVCHIGA XABAR YUBORISH XATOSI: {e}")
           
            # Adminlarga xabar
            for admin_id in ADMINS:
                try:
                    await bot.send_message(
                        admin_id,
                        f"✅ TO'LOV MUVAFFAQIYATLI:\n\n📦 Buyurtma: #{order_id}\n💰 Summa: {int(amount)} UZS\n👤 Foydalanuvchi: {user_id}\n💳 To'lov usuli: Click"
                    )
                except Exception as e:
                    logger.error(f"🔴 ADMINGA XABAR YUBORISH XATOSI: {e}")
           
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
           
            logger.warning(f"🟡 TO'LOV BEKOR QILINDI: {order_id}, Error: {error_code}")
           
            try:
                await bot.send_message(
                    user_id,
                    f"❌ Buyurtma №{order_id} uchun to'lov bekor qilindi.\n\nIltimos, qaytadan urinib ko'ring yoki boshqa to'lov usulini tanlang.",
                    reply_markup=get_main_keyboard(user_lang)
                )
            except Exception as e:
                logger.error(f"🔴 BEKOR QILISH XABARINI YUBORISH XATOSI: {e}")
           
            return web.json_response({
                "error": -9,
                "error_note": "TRANSACTION_CANCELLED"
            })
    except Exception as e:
        logger.error(f"🔴 COMPLETE XATOSI: {str(e)}")
        import traceback
        logger.error(f"🔴 XATO TAFSILOTLARI: {traceback.format_exc()}")
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
        logger.error(f"Telegram yangilanishini qayta ishlashda xato: {e}")
        return web.Response(status=500, text=f"Error: {e}")

# --- ASOSIY FUNKSIYA ---
async def main():
    logger.info("🚀 COMO PIZZA BOT ishga tushmoqda...")
   
    # Database ni ishga tushirish
    try:
        init_db()
        logger.info("✅ Database ishga tushdi")
    except Exception as e:
        logger.error(f"❌ Database xatosi: {e}")
   
    # Webhook ni o'rnatish
    try:
        await bot.delete_webhook()
        await bot.set_webhook(url=WEBHOOK_URL, drop_pending_updates=True)
        logger.info(f"✅ Webhook o'rnatildi: {WEBHOOK_URL}")
    except Exception as e:
        logger.error(f"❌ Webhook xatosi: {e}")
   
    # Web server yaratish
    app = web.Application()
   
    app.add_routes([
        web.post(WEBHOOK_PATH, handle_telegram),
        web.post('/click/prepare', handle_click_prepare),
        web.route('*', '/click/complete', handle_click_complete),
        web.get('/', lambda request: web.Response(text='🤖 COMO PIZZA BOT ISHLAYAPTI!'))
    ])
   
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
   
    logger.info(f"✅ Server {PORT}-portda ishga tushdi")
    logger.info("🍕 COMO PIZZA BOT tayyor va ishga tushdi!")
    logger.info("💳 Click integratsiyasi faollashtirildi!")
   
    # Server doimiy ishlashi
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
