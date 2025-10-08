import logging
import sqlite3 
from aiogram import Router, F, types, Bot
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from states import (
    OrderState, AdminState, MenuState, OrderConfirmationState,
    MyOrdersState, FeedbackState, LanguageState
)
from keyboards import ( 
    get_text, get_main_keyboard, get_menu_keyboard, get_products_keyboard,
    get_admin_keyboard, get_admin_menu_keyboard, get_language_keyboard,
    get_cart_keyboard, get_order_confirm_keyboard, get_order_payment_keyboard,
    get_product_inline_keyboard, 
    LANGUAGES
)
from db import ( 
    save_user_data, get_user_data, add_menu_to_db, get_all_menus,
    add_product_to_db, get_products_by_menu, get_product_details,
    add_to_cart, get_cart_items, get_product_price, clear_cart,
    remove_from_cart, save_order, get_user_orders,
    get_order_items_by_id, update_user_location, update_user_language,
    delete_menu_from_db, delete_product_from_db, update_user_language_and_save_data,
    get_order_by_id, update_order_status, get_user_language
)
import re
from hashlib import md5
from typing import Dict, Any

# Konfiguratsiya
DELIVERY_FEE = 1000
ADMINS = [7798312047, 7720794522]
SERVICE_ID = '83881'
MERCHANT_ID = '46627'
SECRET_KEY = '4krNcqcYdfSpGD'
WEBHOOK_HOST = 'https://como-pizzabot1.onrender.com'  # O'z domainingizga o'zgartiring

router = Router()

# MarkdownV2 belgilari uchun yordamchi funksiya
def escape_markdown_v2(text):
    """MarkdownV2 formatidagi maxsus belgilarni 'escape' qiladi."""
    if text is None:
        return ""
    text = str(text)
    escape_chars = r'_*[]()~`>#+ -=|{. !}'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

# Tilni aniqlash uchun yordamchi funksiya
def get_user_language(user_id):
    user_data = get_user_data(user_id)
    return user_data[4] if user_data and len(user_data) > 4 else 'uz'

# Start buyrug'i uchun handler
@router.message(CommandStart())
async def handle_start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user_data = get_user_data(user_id)
    
    if user_data and user_data[1] is not None:
        # Nomer mavjud bo'lsa, to'g'ridan-to'g'ri asosiy menyuga o'tish
        user_lang = get_user_language(user_id)
        await message.answer(get_text(user_lang, 'WELCOME_MESSAGE'), reply_markup=get_main_keyboard(user_lang))
        await state.clear()
    else:
        # Foydalanuvchi yangi bo'lsa yoki nomeri bo'lmasa, til so'rash
        await message.answer("Iltimos, tilingizni tanlang:", reply_markup=get_language_keyboard())
        await state.set_state(LanguageState.choosing_language)

# Til sozlash handlerlari
@router.message(F.text.in_([LANGUAGES['uz']['CHANGE_LANG_BUTTON'], LANGUAGES['ru']['CHANGE_LANG_BUTTON']]))
async def handle_change_language_request(message: types.Message, state: FSMContext):
    await message.answer("Iltimos, yangi tilingizni tanlang:", reply_markup=get_language_keyboard())
    await state.set_state(LanguageState.choosing_language)

@router.message(LanguageState.choosing_language)
async def handle_language_choice(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user_data = get_user_data(user_id)
    
    if "O'zbekcha" in message.text:
        user_lang = 'uz'
    elif "Русский" in message.text:
        user_lang = 'ru'
    else:
        await message.answer("Noto'g'ri tanlov. Iltimos, tugmani bosing.")
        return

    # Tilni saqlash
    if user_data is None:
        update_user_language_and_save_data(user_id, user_lang)
    else:
        update_user_language(user_id, user_lang)

    # Nomer mavjud emasligini tekshirish va uni so'rash
    if user_data is None or user_data[1] is None:
        keyboard = types.ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text=get_text(user_lang, 'SHARE_CONTACT_BUTTON'), request_contact=True)]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        await message.answer(get_text(user_lang, 'REQUEST_CONTACT_MESSAGE'), reply_markup=keyboard)
        await state.set_state(OrderState.entering_phone)
    else:
        await message.answer(get_text(user_lang, 'WELCOME_MESSAGE'), reply_markup=get_main_keyboard(user_lang))
        await state.clear()
        
# Telefon raqami yuborilganda bajariladigan handler
@router.message(F.contact, OrderState.entering_phone)
async def handle_contact(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user_lang = get_user_language(user_id)
    phone_number = message.contact.phone_number
    
    # Nomer saqlash
    save_user_data(user_id, phone_number)

    await message.answer(get_text(user_lang, 'WELCOME_MESSAGE'), reply_markup=get_main_keyboard(user_lang))
    await state.clear()

# Buyurtma berish tugmasi bosilganda
@router.message(F.text.in_([LANGUAGES['uz']['ORDER_BUTTON'], LANGUAGES['ru']['ORDER_BUTTON']]))
async def handle_order_request(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user_lang = get_user_language(user_id)
    user_data = get_user_data(user_id)

    if user_data and user_data[1] is not None:
        # Foydalanuvchi nomeri mavjud bo'lsa, lokatsiya so'rashga o'tish
        keyboard = types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text=get_text(user_lang, 'SHARE_LOCATION_BUTTON'), request_location=True)],
                [types.KeyboardButton(text=get_text(user_lang, 'BACK_BUTTON'))]
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        await message.answer(get_text(user_lang, 'REQUEST_LOCATION_MESSAGE'), reply_markup=keyboard)
        await state.set_state(OrderState.waiting_for_location)
        
    else:
        # Nomeri mavjud bo'lmasa, uni so'rash
        keyboard = types.ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text=get_text(user_lang, 'SHARE_CONTACT_BUTTON'), request_contact=True)]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        await message.answer(get_text(user_lang, 'REQUEST_CONTACT_MESSAGE'), reply_markup=keyboard)
        await state.set_state(OrderState.entering_phone)

@router.message(OrderState.waiting_for_location, F.location)
async def handle_location_from_order(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user_lang = get_user_language(user_id)

    try:
        latitude = message.location.latitude
        longitude = message.location.longitude
        update_user_location(user_id, latitude, longitude)
        await state.update_data(latitude=latitude, longitude=longitude)

        await message.answer(get_text(user_lang, 'MENU_MESSAGE'), reply_markup=get_menu_keyboard(user_lang))
        await state.set_state(OrderState.in_menu)
    except Exception as e:
        logging.error(f"Geolokatsiya saqlashda xato: {e}")
        await message.answer(get_text(user_lang, 'REQUEST_LOCATION_MESSAGE'), reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text=get_text(user_lang, 'SHARE_LOCATION_BUTTON'), request_location=True)]],
            resize_keyboard=True,
            one_time_keyboard=True
        ))

@router.message(F.text.in_([LANGUAGES['uz']['BACK_BUTTON'], LANGUAGES['ru']['BACK_BUTTON']]), OrderState.waiting_for_location)
async def handle_back_from_location(message: types.Message, state: FSMContext):
    user_lang = get_user_language(message.from_user.id)
    await message.answer(get_text(user_lang, 'BACK_TO_MAIN'), reply_markup=get_main_keyboard(user_lang))
    await state.clear()

@router.message(OrderState.waiting_for_location)
async def handle_invalid_location(message: types.Message, state: FSMContext):
    user_lang = get_user_language(message.from_user.id)
    await message.answer(
        get_text(user_lang, 'REQUEST_LOCATION_MESSAGE'),
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text=get_text(user_lang, 'SHARE_LOCATION_BUTTON'), request_location=True)],
                [types.KeyboardButton(text=get_text(user_lang, 'BACK_BUTTON'))]
            ],
            resize_keyboard=True
        )
    )

@router.message(F.text.in_([LANGUAGES['uz']['BACK_BUTTON'], LANGUAGES['ru']['BACK_BUTTON']]), OrderState.in_menu)
async def handle_back(message: types.Message, state: FSMContext):
    user_lang = get_user_language(message.from_user.id)
    await message.answer(get_text(user_lang, 'BACK_TO_MAIN'), reply_markup=get_main_keyboard(user_lang))
    await state.clear()

@router.message(F.text.in_([LANGUAGES['uz']['ABOUT_US_BUTTON'], LANGUAGES['ru']['ABOUT_US_BUTTON']]))
async def handle_about_us(message: types.Message):
    user_lang = get_user_language(message.from_user.id)
    about_text = (
        f"**{escape_markdown_v2(get_text(user_lang, 'ABOUT_US_BUTTON'))}**\n\n"
        f"{escape_markdown_v2(get_text(user_lang, 'ABOUT_US_MESSAGE'))}\n\n"
        "🍕 *Como Pizza* - bu sizning sevimli taomlaringizni tez va qulay yetkazib beruvchi xizmat! "
        "Biz yuqori sifatli ingredientlardan tayyorlangan mazali pitsalar va boshqa taomlarni taklif qilamiz. "
        "Mijozlarimizning qulayligi va mamnunligi bizning ustuvor vazifamizdir. "
        "Buyurtma bering va lazzatlaning! 😊"
        if user_lang == 'uz' else
        "🍕 *Como Pizza* - это сервис быстрой и удобной доставки ваших любимых блюд! "
        "Мы предлагаем вкусные пиццы и другие блюда, приготовленные из высококачественных ингредиентов. "
        "Комфорт и удовлетворенность наших клиентов - наш главный приоритет. "
        "Заказывайте и наслаждайтесь! 😊"
    )
    await message.answer(about_text, reply_markup=get_main_keyboard(user_lang), parse_mode="MarkdownV2")

@router.message(F.text.in_([LANGUAGES['uz']['FEEDBACK_BUTTON'], LANGUAGES['ru']['FEEDBACK_BUTTON']]))
async def handle_feedback_request(message: types.Message, state: FSMContext):
    user_lang = get_user_language(message.from_user.id)
    await message.answer(
        get_text(user_lang, 'FEEDBACK_REQUEST'),
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(FeedbackState.entering_feedback)

@router.message(FeedbackState.entering_feedback)
async def handle_feedback_entry(message: types.Message, state: FSMContext, bot: Bot):
    user_lang = get_user_language(message.from_user.id)
    feedback_text = escape_markdown_v2(message.text)
    user_info = f"Foydalanuvchi: {escape_markdown_v2(message.from_user.full_name)}\nID: `{message.from_user.id}`"

    for admin_id in ADMINS:
        feedback_message = (
            "Yangi izoh:\n\n"
            f"**{user_info}**\n\n"
            f"**Izoh**: {feedback_text}"
        )
        try:
            await bot.send_message(admin_id, feedback_message, parse_mode="MarkdownV2")
        except Exception as e:
            logging.error(f"Admin ID {admin_id}ga izoh yuborishda xato: {e}")

    await message.answer(get_text(user_lang, 'FEEDBACK_SUCCESS'), reply_markup=get_main_keyboard(user_lang))
    await state.clear()

@router.message(F.text.in_([LANGUAGES['uz']['CART_BUTTON'], LANGUAGES['ru']['CART_BUTTON']]))
async def handle_cart(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user_lang = get_user_language(user_id)

    items = get_cart_items(user_id)
    if not items:
        await message.answer(get_text(user_lang, 'CART_EMPTY'), reply_markup=get_main_keyboard(user_lang))  # get_main_keyboard ga o'zgartirildi
        return

    total_sum = 0
    text = escape_markdown_v2(get_text(user_lang, 'CART_MESSAGE')) + "\n\n"

    for item in items:
        product_name, quantity = item
        price = get_product_price(product_name)
        total = price * quantity
        total_sum += total
        text += f"*{escape_markdown_v2(product_name)}* {quantity} x {int(price)} \\= {int(total)} UZS\n"

    text += f"\n**Umumiy narx**: {escape_markdown_v2(total_sum)} UZS"

    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(text=get_text(user_lang, 'CONFIRM_ORDER_BUTTON'), callback_data="confirm_order"),
                types.InlineKeyboardButton(text=get_text(user_lang, 'CLEAN_CART_BUTTON'), callback_data="clear_cart")
            ]
        ]
    )

    await message.answer(text, reply_markup=keyboard, parse_mode="MarkdownV2")

@router.message(F.text.in_([LANGUAGES['uz']['MY_ORDERS_BUTTON'], LANGUAGES['ru']['MY_ORDERS_BUTTON']]))
async def handle_my_orders(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user_lang = get_user_language(user_id)
    
    orders = get_user_orders(user_id)

    if not orders:
        await message.answer(get_text(user_lang, 'NO_ORDERS'))
        return

    text = f"**{escape_markdown_v2(get_text(user_lang, 'YOUR_ORDERS'))}:**\n\n"
    keyboard_buttons = []

    for order in orders:
        order_id, total_price, created_at = order
        text += f"\\- №{order_id} \\| {escape_markdown_v2(int(total_price))} UZS \\| {escape_markdown_v2(created_at)}\n"
        keyboard_buttons.append([types.InlineKeyboardButton(text=f"№{order_id} Buyurtma", callback_data=f"view_order_{order_id}")])

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    await message.answer(text, reply_markup=keyboard, parse_mode="MarkdownV2")
    await state.set_state(MyOrdersState.viewing_orders)

# Bitta buyurtma tafsilotlarini ko'rish handlerini toʻgʻrilash
@router.callback_query(F.data.startswith("view_order_"))
async def handle_view_single_order(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    user_lang = get_user_language(callback.from_user.id)
    try:
        order_id = int(callback.data.split('_')[2]) 
    except (IndexError, ValueError):
        await callback.message.answer("Noto'g'ri buyurtma ID.")
        return
        
    items = get_order_items_by_id(order_id)
    if not items:
        await callback.message.answer(get_text(user_lang, 'ORDER_NOT_FOUND'))
        return
        
    order_details = f"**{escape_markdown_v2(get_text(user_lang, 'VIEW_ORDER_DETAILS'))} №{order_id}**\n\n"
    total_price = 0
    for item in items:
        product_name, quantity, price = item
        total = quantity * price
        total_price += total
        order_details += f"\\- {escape_markdown_v2(product_name)}: {quantity} x {escape_markdown_v2(str(int(price)))} \\= {escape_markdown_v2(str(int(total)))} UZS\n"
        
    order_details += f"\n**{escape_markdown_v2(get_text(user_lang, 'TOTAL'))}**: {escape_markdown_v2(str(int(total_price)))} UZS"
    
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text=get_text(user_lang, 'BACK_BUTTON'), callback_data="back_to_my_orders")]
        ]
    )
    await callback.message.edit_text(order_details, reply_markup=keyboard, parse_mode="MarkdownV2")

# Buyurtmalar ro'yxatiga qaytish handlerini to'g'rilash
@router.callback_query(F.data == "back_to_my_orders")
async def handle_back_to_orders(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user_lang = get_user_language(user_id)
    await callback.answer()
    
    orders = get_user_orders(user_id)
    
    if not orders:
        await callback.message.edit_text(get_text(user_lang, 'NO_ORDERS'), reply_markup=None)
        await state.clear()
        return

    text = f"**{escape_markdown_v2(get_text(user_lang, 'YOUR_ORDERS'))}:**\n\n"
    keyboard_buttons = []

    for order in orders:
        order_id, total_price, created_at = order
        text += f"\\- №{order_id} \\| {escape_markdown_v2(str(int(total_price)))} UZS \\| {escape_markdown_v2(created_at)}\n"
        keyboard_buttons.append([types.InlineKeyboardButton(text=f"№{order_id} Buyurtma", callback_data=f"view_order_{order_id}")])

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="MarkdownV2")
    await state.set_state(MyOrdersState.viewing_orders)

@router.callback_query(F.data == "back_to_main")
async def handle_back_to_main(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    user_lang = get_user_language(callback.from_user.id)
    await state.clear()
    await callback.message.edit_text(get_text(user_lang, 'BACK_TO_MAIN'), reply_markup=None)
    await callback.message.answer(get_text(user_lang, 'BACK_TO_MAIN'), reply_markup=get_main_keyboard(user_lang))

@router.message(OrderState.in_menu)
async def handle_menu_selection(message: types.Message, state: FSMContext):
    user_lang = get_user_language(message.from_user.id)
    menu_name = message.text
    if menu_name in get_all_menus():
        await state.update_data(selected_menu=menu_name)
        text = f"'{escape_markdown_v2(menu_name)}' {escape_markdown_v2(get_text(user_lang, 'PRODUCT_SELECTION'))}"
        await message.answer(text, reply_markup=get_products_keyboard(user_lang, menu_name), parse_mode="MarkdownV2")
        await state.set_state(MenuState.in_category)
    else:
        await message.answer(get_text(user_lang, 'INVALID_MENU'))

@router.message(F.text.in_([LANGUAGES['uz']['BACK_BUTTON'], LANGUAGES['ru']['BACK_BUTTON']]), MenuState.in_category)
async def handle_back_from_products(message: types.Message, state: FSMContext):
    user_lang = get_user_language(message.from_user.id)
    await message.answer(get_text(user_lang, 'BACK_TO_MAIN'), reply_markup=get_menu_keyboard(user_lang))
    await state.set_state(OrderState.in_menu)

@router.message(MenuState.in_category)
async def handle_product_selection(message: types.Message, state: FSMContext):
    user_lang = get_user_language(message.from_user.id)
    product_name = message.text
    product_data = get_product_details(product_name)

    if product_data:
        name, description, price = product_data
        text = (
            f"**{escape_markdown_v2(name)}**\n\n"
            f"{escape_markdown_v2(description)}\n\n"
            f"**{int(price)}** UZS\n"
        )
        keyboard = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(text="➖", callback_data=f"dec_{name}"),
                    types.InlineKeyboardButton(text="1", callback_data=f"count_1_{name}"),
                    types.InlineKeyboardButton(text="➕", callback_data=f"inc_{name}")
                ],
                [
                    types.InlineKeyboardButton(text=get_text(user_lang, 'cart_button'), callback_data=f"add_to_cart_{name}")
                ]
            ]
        )
        await message.answer(text, reply_markup=keyboard, parse_mode="MarkdownV2")
        await state.set_state(MenuState.in_product_details)
        await state.update_data(product_name=name, count=1, price=price)
    else:
        await message.answer(get_text(user_lang, 'INVALID_MENU'))

@router.callback_query(F.data.startswith("inc_"))
async def handle_inc_quantity(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    user_lang = get_user_language(callback.from_user.id)
    data = await state.get_data()
    current_count = data.get("count", 1)
    product_name = data.get("product_name")
    price = data.get("price")
    new_count = current_count + 1
    total_price = new_count * price
    await state.update_data(count=new_count)
    new_keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(text="➖", callback_data=f"dec_{product_name}"),
                types.InlineKeyboardButton(text=f"{new_count}", callback_data=f"count_{new_count}_{product_name}"),
                types.InlineKeyboardButton(text="➕", callback_data=f"inc_{product_name}")
            ],
            [types.InlineKeyboardButton(text=get_text(user_lang, 'cart_button'), callback_data=f"add_to_cart_{product_name}")]
        ]
    )
    text = (
        f"**{escape_markdown_v2(product_name)}**\n\n"
        f"**{escape_markdown_v2(product_name)}** {new_count} x {int(price)} \\= {int(total_price)} UZS\n"
    )
    await callback.message.edit_text(text, reply_markup=new_keyboard, parse_mode="MarkdownV2")

@router.callback_query(F.data.startswith("dec_"))
async def handle_dec_quantity(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    user_lang = get_user_language(callback.from_user.id)
    data = await state.get_data()
    current_count = data.get("count", 1)
    product_name = data.get("product_name")
    price = data.get("price")
    if current_count > 1:
        new_count = current_count - 1
        total_price = new_count * price
        await state.update_data(count=new_count)
        new_keyboard = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(text="➖", callback_data=f"dec_{product_name}"),
                    types.InlineKeyboardButton(text=f"{new_count}", callback_data=f"count_{new_count}_{product_name}"),
                    types.InlineKeyboardButton(text="➕", callback_data=f"inc_{product_name}")
                ],
                [types.InlineKeyboardButton(text=get_text(user_lang, 'cart_button'), callback_data=f"add_to_cart_{product_name}")]
            ]
        )
        text = (
            f"**{escape_markdown_v2(product_name)}**\n\n"
            f"**{escape_markdown_v2(product_name)}** {new_count} x {int(price)} \\= {int(total_price)} UZS\n"
        )
        await callback.message.edit_text(text, reply_markup=new_keyboard, parse_mode="MarkdownV2")
    else:
        await callback.answer(get_text(user_lang, 'MIN_QUANTITY_ALERT'), show_alert=True)

@router.callback_query(F.data.startswith("add_to_cart_"))
async def handle_add_to_cart_callback(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    user_lang = get_user_language(callback.from_user.id)
    data = await state.get_data()
    product_name = data.get("product_name")
    quantity = data.get("count", 1)
    add_to_cart(callback.from_user.id, product_name, quantity)
    await callback.message.delete()
    await callback.message.answer(get_text(user_lang, 'ADD_TO_CART_SUCCESS'), reply_markup=get_menu_keyboard(user_lang))  # Bu yerda get_menu_keyboard saqlanadi
    await state.set_state(OrderState.in_menu)

@router.callback_query(F.data == "clear_cart")
async def handle_clear_cart_callback(callback: types.CallbackQuery):
    user_lang = get_user_language(callback.from_user.id)
    await callback.answer(get_text(user_lang, 'CART_CLEARED'))
    clear_cart(callback.from_user.id)
    await callback.message.edit_text(get_text(user_lang, 'CART_CLEARED'), reply_markup=None)
    await callback.message.answer(get_text(user_lang, 'BACK_TO_MAIN'), reply_markup=get_main_keyboard(user_lang))  # Bu yerda allaqachon get_main_keyboard bor

@router.callback_query(F.data == "confirm_order")
async def handle_confirm_order_callback(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    user_id = callback.from_user.id
    user_lang = get_user_language(user_id)
    
    user_data = get_user_data(user_id)
    # Telefon va Manzil tekshiruvi
    if not user_data or not user_data[1]: 
        await callback.message.answer(get_text(user_lang, 'REQUEST_CONTACT_MESSAGE'),
                             reply_markup=get_cart_keyboard(user_lang, share_contact=True))
        await state.set_state(OrderState.entering_phone)
        return
    if not user_data[2] or not user_data[3]: # latitude yoki longitude yo'q bo'lsa
        await callback.message.answer(get_text(user_lang, 'REQUEST_LOCATION_MESSAGE'),
                             reply_markup=get_cart_keyboard(user_lang, share_location=True))
        await state.set_state(OrderState.waiting_for_location)
        return
        
    cart_items = get_cart_items(user_id)
    
    if not cart_items:
        await callback.message.answer(get_text(user_lang, 'CART_EMPTY'), reply_markup=get_main_keyboard(user_lang))
        await state.clear()
        return

    total_sum = sum(get_product_price(item[0]) * item[1] for item in cart_items)
    final_total = total_sum + DELIVERY_FEE
    
    await state.update_data(final_total_price=final_total)

    await callback.message.answer(
        get_text(user_lang, 'CHOOSE_PAYMENT'), 
        reply_markup=get_order_payment_keyboard(user_lang)
    )
    await state.set_state(OrderConfirmationState.choosing_payment)

# handlers.py faylida Click to'lov qismini yangilang:

@router.message(OrderConfirmationState.choosing_payment)
async def process_payment_choice_or_confirm(message: types.Message, state: FSMContext, bot: Bot):
    user_id = message.from_user.id
    user_lang = get_user_language(user_id)
    text = message.text
    data = await state.get_data()
    
    # Check if cart and total price are valid
    final_total = data.get('final_total_price')
    cart_items = get_cart_items(user_id)
    
    if final_total is None or not cart_items:
        if cart_items:
            total_sum = sum(get_product_price(item[0]) * item[1] for item in cart_items)
            final_total = total_sum + DELIVERY_FEE
            await state.update_data(final_total_price=final_total)
        else:
            await message.answer(get_text(user_lang, 'CART_EMPTY'), reply_markup=get_main_keyboard(user_lang))
            await state.clear()
            return
            
    user_data = get_user_data(user_id)
    user_first_name = message.from_user.first_name

    # Handle "Click" payment
    if text == get_text(user_lang, 'PAYMENT_CLICK'):
        # Save order with "Pending" status for Click payment
        order_id = save_order(
            user_id=user_id, 
            total_price=final_total, 
            cart_items=cart_items, 
            payment_type='Click',
            user_first_name=user_first_name,
            status='Pending'
        )
        
        # Generate Click payment URL
        click_url = (
            "https://my.click.uz/services/pay"
            f"?service_id={SERVICE_ID}"
            f"&merchant_id={MERCHANT_ID}"
            f"&amount={int(final_total)}"
            f"&transaction_param={order_id}"
            f"&return_url={WEBHOOK_HOST}"
        )
        
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="💳 Click orqali to'lash", url=click_url)]
        ])
        
        click_message = f"🧾 Buyurtma №{order_id} ({int(final_total)} UZS)\n\nTo'lov qilish uchun quyidagi tugmani bosing:"
        
        await message.answer(
            click_message, 
            reply_markup=keyboard
        )
        
        await send_admin_notification(bot, order_id, user_data, final_total, 'Click', 'Pending')
        
        clear_cart(user_id)
        await state.clear()
        return

    # Handle "Cash" (Naqd) payment
    elif text == get_text(user_lang, 'PAYMENT_CASH'):
        # Save order with "New" status for Cash payment
        order_id = save_order(
            user_id=user_id, 
            total_price=final_total, 
            cart_items=cart_items, 
            payment_type='Cash',
            user_first_name=user_first_name,
            status='New'
        )
        
        # Notify admins
        await send_admin_notification(bot, order_id, user_data, final_total, 'Cash', 'New')
        
        # Clear cart and inform user
        clear_cart(user_id)
        await message.answer(
            get_text(user_lang, 'ORDER_CONFIRMED').format(order_id=order_id),
            reply_markup=get_main_keyboard(user_lang)
        )
        await state.clear()
        return

    # Handle "Payme" payment
    elif text == get_text(user_lang, 'PAYMENT_PAYME'):
        # Inform user that Payme is not available and return to payment selection
        await message.answer(
            get_text(user_lang, 'PAYME_NOT_AVAILABLE'),
            reply_markup=get_order_payment_keyboard(user_lang)
        )
        await state.set_state(OrderConfirmationState.choosing_payment)
        return

    # Handle invalid payment choice
    else:
        await message.answer(
            get_text(user_lang, 'INVALID_CHOICE_TRY_AGAIN'),
            reply_markup=get_order_payment_keyboard(user_lang)
        )
@router.message(OrderConfirmationState.confirming_order)
async def handle_confirm_order_message(message: types.Message, state: FSMContext, bot: Bot):
    user_id = message.from_user.id
    user_lang = get_user_language(user_id)
    text = message.text
    data = await state.get_data()
    
    # ---------------- 1. TASDIQLASH ----------------
    if text == get_text(user_lang, 'CONFIRM_ORDER_BUTTON'):
        payment_method = data.get('payment_method')
        final_total = data.get('final_total_price')
        cart_items = get_cart_items(user_id)
        
        if payment_method is None or final_total is None or not cart_items:
            await message.answer(get_text(user_lang, 'CART_EMPTY'), reply_markup=get_main_keyboard(user_lang))
            await state.clear()
            return
            
        user_data = get_user_data(user_id)
        user_first_name = message.from_user.first_name

        order_id = save_order(
            user_id=user_id, 
            total_price=final_total, 
            cart_items=cart_items, 
            payment_type=payment_method, 
            user_first_name=user_first_name, 
            status='New'
        )
        
        # Adminga xabar yuborish
        await send_admin_notification(bot, order_id, user_data, final_total, payment_method, 'New')
        
        clear_cart(user_id)
        await message.answer(get_text(user_lang, 'ORDER_CONFIRMED').format(order_id=order_id),
                             reply_markup=get_main_keyboard(user_lang))
        await state.clear()
        return

    # ---------------- 2. BEKOR QILISH ----------------
    elif text == get_text(user_lang, 'CANCEL_ORDER_BUTTON'):
        await message.answer(get_text(user_lang, 'ORDER_CANCELLED'), reply_markup=get_main_keyboard(user_lang))
        await state.clear()
        return
    
    # ---------------- 3. ORQAGA TUGMASI ----------------
    elif text == get_text(user_lang, 'BACK_BUTTON'):
        await message.answer(get_text(user_lang, 'CHOOSE_PAYMENT'), reply_markup=get_order_payment_keyboard(user_lang))
        await state.set_state(OrderConfirmationState.choosing_payment)
        return
        
    await message.answer(get_text(user_lang, 'INVALID_CHOICE_TRY_AGAIN'))

# Admin paneli handlerlari
@router.message(Command("admin"))
async def handle_admin(message: types.Message, state: FSMContext):
    user_lang = get_user_language(message.from_user.id)
    if message.from_user.id in ADMINS:
        await message.answer(get_text(user_lang, 'ADMIN_WELCOME_MESSAGE'), reply_markup=get_admin_keyboard(user_lang))
        await state.set_state(AdminState.admin_panel)
    else:
        await message.answer(get_text(user_lang, 'NO_ACCESS_MESSAGE'))

@router.message(F.text.in_([LANGUAGES['uz']['ADMIN_PANEL_BACK_BUTTON'], LANGUAGES['ru']['ADMIN_PANEL_BACK_BUTTON']]), AdminState.admin_panel)
async def handle_admin_back(message: types.Message, state: FSMContext):
    user_lang = get_user_language(message.from_user.id)
    await message.answer(get_text(user_lang, 'BACK_TO_MAIN'), reply_markup=get_main_keyboard(user_lang))
    await state.clear()

@router.message(F.text.in_([LANGUAGES['uz']['DELETE_MENU_BUTTON'], LANGUAGES['ru']['DELETE_MENU_BUTTON']]), AdminState.admin_panel)
async def handle_delete_menu(message: types.Message, state: FSMContext):
    user_lang = get_user_language(message.from_user.id)
    await message.answer("O'chirmoqchi bo'lgan menyuni tanlang:", reply_markup=get_admin_menu_keyboard(user_lang))
    await state.set_state(AdminState.deleting_menu)

@router.message(AdminState.deleting_menu)
async def process_delete_menu(message: types.Message, state: FSMContext):
    user_lang = get_user_language(message.from_user.id)
    menu_name = message.text
    if delete_menu_from_db(menu_name):
        await message.answer(f"'{menu_name}' muvaffaqiyatli o'chirildi.", reply_markup=get_admin_keyboard(user_lang))
    else:
                await message.answer(f"'{menu_name}' topilmadi.", reply_markup=get_admin_keyboard(user_lang))
    await state.set_state(AdminState.admin_panel)

@router.message(F.text.in_([LANGUAGES['uz']['DELETE_PRODUCT_BUTTON'], LANGUAGES['ru']['DELETE_PRODUCT_BUTTON']]), AdminState.admin_panel)
async def handle_delete_product(message: types.Message, state: FSMContext):
    user_lang = get_user_language(message.from_user.id)
    await message.answer("O'chirmoqchi bo'lgan mahsulot nomini kiriting:", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(AdminState.deleting_product)

@router.message(AdminState.deleting_product)
async def process_delete_product(message: types.Message, state: FSMContext):
    user_lang = get_user_language(message.from_user.id)
    product_name = message.text
    if delete_product_from_db(product_name):
        await message.answer(f"'{product_name}' muvaffaqiyatli o'chirildi.", reply_markup=get_admin_keyboard(user_lang))
    else:
        await message.answer(f"'{product_name}' topilmadi.", reply_markup=get_admin_keyboard(user_lang))
    await state.set_state(AdminState.admin_panel)

@router.message(F.text.in_([LANGUAGES['uz']['ADD_MENU_BUTTON'], LANGUAGES['ru']['ADD_MENU_BUTTON']]), AdminState.admin_panel)
async def handle_add_menu(message: types.Message, state: FSMContext):
    user_lang = get_user_language(message.from_user.id)
    await message.answer(get_text(user_lang, 'ENTER_MENU_NAME'))
    await state.set_state(AdminState.adding_menu)

@router.message(AdminState.adding_menu)
async def process_new_menu(message: types.Message, state: FSMContext):
    user_lang = get_user_language(message.from_user.id)
    menu_name = message.text
    if add_menu_to_db(menu_name):
        text = f"'{escape_markdown_v2(menu_name)}' {escape_markdown_v2(get_text(user_lang, 'MENU_ADDED'))}"
        await message.answer(text, reply_markup=get_admin_keyboard(user_lang), parse_mode="MarkdownV2")
    else:
        await message.answer(get_text(user_lang, 'MENU_ALREADY_EXISTS'), reply_markup=get_admin_keyboard(user_lang))
    await state.set_state(AdminState.admin_panel)

@router.message(F.text.in_([LANGUAGES['uz']['ADD_PRODUCT_BUTTON'], LANGUAGES['ru']['ADD_PRODUCT_BUTTON']]), AdminState.admin_panel)
async def handle_add_product(message: types.Message, state: FSMContext):
    user_lang = get_user_language(message.from_user.id)
    await message.answer("Mahsulot qo'shish uchun menyuni tanlang:", reply_markup=get_admin_menu_keyboard(user_lang))
    await state.set_state(AdminState.choosing_menu_for_product)

@router.message(AdminState.choosing_menu_for_product)
async def handle_menu_for_product(message: types.Message, state: FSMContext):
    user_lang = get_user_language(message.from_user.id)
    menu_name = message.text
    menus = get_all_menus()
    if menu_name in menus:
        await state.update_data(selected_menu=menu_name)
        text = f"'{escape_markdown_v2(menu_name)}' {escape_markdown_v2(get_text(user_lang, 'ENTER_PRODUCT_NAME'))}"
        await message.answer(text, parse_mode="MarkdownV2")
        await state.set_state(AdminState.entering_product_name)
    else:
        await message.answer(get_text(user_lang, 'INVALID_MENU'), reply_markup=get_admin_menu_keyboard(user_lang))

@router.message(AdminState.entering_product_name)
async def handle_product_name_entry(message: types.Message, state: FSMContext):
    user_lang = get_user_language(message.from_user.id)
    product_name = message.text
    await state.update_data(product_name=product_name)
    await message.answer(get_text(user_lang, 'ENTER_DESCRIPTION'))
    await state.set_state(AdminState.entering_product_description)

@router.message(AdminState.entering_product_description)
async def handle_product_description_entry(message: types.Message, state: FSMContext):
    user_lang = get_user_language(message.from_user.id)
    description = message.text
    await state.update_data(description=description)
    await message.answer(get_text(user_lang, 'ENTER_PRICE'))
    await state.set_state(AdminState.entering_product_price)

@router.message(AdminState.entering_product_price)
async def handle_product_price_entry(message: types.Message, state: FSMContext):
    user_lang = get_user_language(message.from_user.id)
    try:
        price = float(message.text)
        data = await state.get_data()
        menu_name = data.get("selected_menu")
        product_name = data.get("product_name")
        description = data.get("description")
        if add_product_to_db(menu_name, product_name, description, price):
            text = f"'{escape_markdown_v2(product_name)}' {escape_markdown_v2(get_text(user_lang, 'PRODUCT_ADDED'))}"
            await message.answer(text, reply_markup=get_admin_keyboard(user_lang), parse_mode="MarkdownV2")
        else:
            await message.answer(get_text(user_lang, 'PRODUCT_ALREADY_EXISTS'), reply_markup=get_admin_keyboard(user_lang))
        await state.set_state(AdminState.admin_panel)
    except ValueError:
        await message.answer(get_text(user_lang, 'INVALID_PRICE'))
        return

# Adminlarga xabar yuborish funksiyasi
async def send_admin_notification(bot: Bot, order_id: int, user_data: tuple, final_sum: float, payment_type: str, status: str):
    """Adminlarga yangi buyurtma haqida xabar yuboradi."""
    
    # user_data ni ehtiyotkorlik bilan ochish
    if user_data and len(user_data) >= 5:
        user_id, phone_number, lat, lon, user_lang = user_data 
    else:
        # Ma'lumot to'liq bo'lmasa, default qiymatlar
        user_id, phone_number, lat, lon = 0, "Noma'lum", None, None
    
    user_first_name = "Mijoz"

    # Buyurtma mahsulotlarini olish
    items = get_order_items_by_id(order_id)
    
    message_text = f"**YANGI BUYURTMA №{order_id}**\n"
    message_text += f"**Mijoz:** {escape_markdown_v2(user_first_name)}\n"
    message_text += f"**Tel:** {escape_markdown_v2(phone_number)}\n"
    message_text += f"**To'lov turi:** {escape_markdown_v2(payment_type)}\n"
    message_text += f"**Holati:** {escape_markdown_v2(status)}\n\n"
    
    message_text += f"**Buyurtma ro'yxati:**\n"
    for product_name, quantity, price in items:
        total_item_price = price * quantity 
        message_text += f"\\- {escape_markdown_v2(product_name)}: {quantity} x {escape_markdown_v2(int(price))} UZS \\= {escape_markdown_v2(int(total_item_price))} UZS\n"
        
    message_text += f"\n**Yetkazib berish:** {int(DELIVERY_FEE)} UZS\n"
    message_text += f"**Jami:** {escape_markdown_v2(int(final_sum))} UZS"
    
    # Manzil havolasini yaratish
    map_url = ""
    if lat is not None and lon is not None:
        map_url = f"[Manzilni ko'rish](http://maps.google.com/maps?q={lat},{lon})"

    for admin_id in ADMINS:
        try:
            # Geolokatsiyani yuborish
            if lat is not None and lon is not None:
                 await bot.send_location(admin_id, latitude=lat, longitude=lon)
                 await bot.send_message(
                    chat_id=admin_id,
                    text=message_text + "\n\n" + map_url,
                    parse_mode='MarkdownV2'
                )
            else:
                 await bot.send_message(
                    chat_id=admin_id,
                    text=message_text + "\n\n" + escape_markdown_v2("Geolokatsiya mavjud emas."),
                    parse_mode='MarkdownV2'
                )
        except Exception as e:
            logging.error(f"Adminga ({admin_id}) xabar yuborishda xato: {e}")

# Qo'shimcha callback handlerlar
@router.callback_query(F.data.startswith("count_"))
async def handle_count_update(callback: types.CallbackQuery, state: FSMContext):
    """Miqdor yangilanishi uchun callback handler"""
    await callback.answer()
    # Bu handler faqat callback ni qayta ishlash uchun, asosiy funksiyalar inc_ va dec_ da bajariladi

# Noto'g'ri xabarlarni qayta ishlash
@router.message()
async def handle_unknown_messages(message: types.Message):
    """Noma'lum xabarlarni qayta ishlash"""
    user_lang = get_user_language(message.from_user.id)
    await message.answer(
        "Noto'g'ri buyruq. Iltimos, menyudan tugmalardan foydalaning.",
        reply_markup=get_main_keyboard(user_lang)

    )




