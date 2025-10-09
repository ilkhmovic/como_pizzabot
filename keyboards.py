from aiogram import types
from db import get_all_menus, get_products_by_menu
import logging

# Tugmalar uchun matnlar
ORDER_BUTTON = "🛍️ Buyurtma berish"
MY_ORDERS_BUTTON = "📦 Mening buyurtmalarim"
ABOUT_US_BUTTON = "ℹ️ Biz haqimizda"
FEEDBACK_BUTTON = "✍️ Izoh qoldirish"
SHARE_CONTACT_BUTTON = "📞 Telefon raqamni ulashish"
SHARE_LOCATION_BUTTON = "📍 Manzilni yuborish"
BACK_BUTTON = "🔙 Orqaga"
CART_BUTTON = "🛒 Savat"
cart_button = "🛒 Savatga solish"
MENU_BUTTON = "🍽️ Menyu"
CHANGE_LANG_BUTTON = "🇺🇿/🇷🇺 Tilni o'zgartirish"

# Admin paneli tugmalari
ADD_MENU_BUTTON = "➕ Menyu qo'shish"
ADD_PRODUCT_BUTTON = "➕ Mahsulot qo'shish"
DELETE_MENU_BUTTON = "🗑️ Menyu o'chirish"
DELETE_PRODUCT_BUTTON = "🗑️ Mahsulot o'chirish"
ADMIN_PANEL_BACK_BUTTON = "🔙 Orqaga"

# To'lov tugmalari
PAYMENT_CASH = "💵 Naqd pul"
PAYMENT_CLICK = "💳 Click"
PAYMENT_PAYME = "💳 Payme"
CONFIRM_ORDER_BUTTON = "✅ Tasdiqlash"
CANCEL_ORDER_BUTTON = "❌ Bekor qilish"
CLEAN_CART_BUTTON = "🗑️ Savatni tozalash"

# Xabarlar uchun matnlar
LANGUAGES = {
    'uz': {
        'ORDER_BUTTON': "🛍️ Buyurtma berish",
        'MY_ORDERS_BUTTON': "📦 Mening buyurtmalarim",
        'ABOUT_US_BUTTON': "ℹ️ Biz haqimizda",
        'ABOUT_US_MESSAGE': 'Como Pizza haqida',
        'FEEDBACK_BUTTON': "✍️ Izoh qoldirish",
        'SHARE_CONTACT_BUTTON': "📞 Telefon raqamni ulashish",
        'SHARE_LOCATION_BUTTON': "📍 Manzilni yuborish",
        'MENU_BUTTON': "🍽️ Menyu",
        'BACK_BUTTON': "🔙 Orqaga",
        'CART_BUTTON': "🛒 Savat",
        'cart_button': "🛒 Savatga solish",
        'ADD_MENU_BUTTON': "➕ Menyu qo'shish",
        'ADD_PRODUCT_BUTTON': "➕ Mahsulot qo'shish",
        'DELETE_MENU_BUTTON': "🗑️ Menyu o'chirish",
        'DELETE_PRODUCT_BUTTON': "🗑️ Mahsulot o'chirish",
        'ADMIN_PANEL_BACK_BUTTON': "🔙 Orqaga",
        'PAYMENT_CASH': "💵 Naqd pul",
        'PAYMENT_CLICK': "💳 Click",
        'PAYMENT_PAYME': "💳 Payme",
        'CONFIRM_ORDER_BUTTON': "✅ Tasdiqlash",
        'CANCEL_ORDER_BUTTON': "❌ Bekor qilish",
        'CLEAN_CART_BUTTON': "🗑️ Savatni tozalash",
        'GO_TO_CHECKOUT': "Buyurtmani tasdiqlash",
        'CLEAR_CART': "Savatni tozalash",
        'WELCOME_MESSAGE': "Assalomu alaykum! Botga xush kelibsiz. Quyidagi tugmalardan birini tanlang.",
        'REQUEST_CONTACT_MESSAGE': "Telefon raqamingizni ulashish uchun '📞 Telefon raqamni ulashish' tugmasini bosing.",
        'REQUEST_LOCATION_MESSAGE': "Manzilingizni yuborish uchun '📍 Manzilni yuborish tugmasini bosing.",
        'MENU_MESSAGE': "Menyu bo'limi.",
        'ADMIN_WELCOME_MESSAGE': "Admin paneliga xush kelibsiz.",
        'NO_ACCESS_MESSAGE': "Sizda admin paneliga kirish huquqi yo'q.",
        'ENTER_MENU_NAME': "Yangi menyu nomini kiriting:",
        'MENU_ADDED': "Menyu muvaffaqiyatli qo'shildi!",
        'MENU_ALREADY_EXISTS': "Bu nomli menyu allaqachon mavjud.",
        'INVALID_MENU': "Bunday menyu topilmadi. Iltimos, ro'yxatdan tanlang.",
        'ENTER_PRODUCT_NAME': "Mahsulot nomini kiriting:",
        'ENTER_DESCRIPTION': "Mahsulot haqida ma'lumot kiriting:",
        'ENTER_PRICE': "Mahsulot narxini kiriting:",
        'INVALID_PRICE': "Narx noto'g'ri kiritildi. Iltimos, butun yoki kasr son kiriting.",
        'PRODUCT_ADDED': "Mahsulot muvaffaqiyatli qo'shildi!",
        'PRODUCT_ALREADY_EXISTS': "Bu nomli mahsulot allaqachon mavjud.",
        'PRODUCT_SELECTION': "Mahsulotlar bo'limiga xush kelibsiz, mahsulotni tanlang.",
        'CART_MESSAGE': "Savatdagi mahsulotlar:",
        'CART_EMPTY': "Savat bo'sh.",
        'ADD_TO_CART_SUCCESS': "Savatga muvaffaqiyatli qo'shildi!",
        'MIN_QUANTITY_ALERT': "Miqdor 1 dan kam bo'lishi mumkin emas.",
        'PAYMENT_CHOICE': "To'lov turini tanlang:",
        'ORDER_CONFIRMED': "Buyurtmangiz qabul qilindi. Tez orada operator siz bilan bog'lanadi.",
        'ORDER_CANCELED': "Buyurtmangiz bekor qilindi.",
        'CART_CLEARED': "Savat tozalandi.",
        'DELIVERY_FEE': "Yetkazib berish narxi",
        'TOTAL': "Jami",
        'LOCATION': "Manzil",
        'PAYMENT_TYPE': "To'lov turi",
        'TOTAL_BILL': "Umumiy hisob",
        'ORDER_LIST_TITLE': "Buyurtma ro'yxati",
        'USER': "Foydalanuvchi",
        'PHONE_NUMBER': "Telefon raqami",
        'NO_ORDERS': "Sizda hali buyurtmalar mavjud emas.",
        'VIEW_ORDER_DETAILS': "Buyurtma tafsilotlari",
        'ORDER_NOT_FOUND': "Buyurtma topilmadi.",
        'BACK_TO_MAIN': "Bosh menyuga qaytish",
        'FEEDBACK_REQUEST': "Izohingizni kiriting:",
        'FEEDBACK_SUCCESS': "Izohingiz qabul qilindi. E'tiboringiz uchun rahmat!",
        'CHANGE_LANG_BUTTON': "🇺🇿/🇷🇺 Tilni o'zgartirish",
        'NEW_ORDER': "Yangi buyurtma!",
        'NO_LOCATION': "Geolokatsiya mavjud emas",
        'PAYMENT_LINK_MESSAGE': "To'lov havolasi:",
        'ERROR_MESSAGE': "Xatolik yuz berdi, qaytadan urinib ko'ring.",
        'PAYMENT_SUCCESS': "✅ Buyurtma №{order_id} uchun to'lov muvaffaqiyatli amalga oshirildi! Buyurtmangiz tez orada yetkaziladi.",
        'PAYMENT_CANCELLED': "❌ Buyurtma №{order_id} uchun to'lov bekor qilindi yoki amalga oshirilmadi. Qaytadan buyurtma bering.",
        'ORDER_STATUS': "Holati",
        'CLICK_PAYMENT_MESSAGE': "🧾 Buyurtma №{order_id} ({total} UZS) uchun Click orqali to'lovni amalga oshirish uchun quyidagi tugmadan foydalaning. To'lov tasdiqlangach sizga xabar yuboriladi va chek fiskalizatsiya qilinadi.",
        'YOUR_ORDERS': "Sizning buyurtmalaringiz",
        'BACK_MESSAGE': "Orqaga qaytish",
        'INVALID_PAYMENT_CHOICE': "Noto'g'ri to'lov turi tanlandi",
        'INVALID_CHOICE_TRY_AGAIN': "Noto'g'ri tanlov, qaytadan urinib ko'ring",
        'CHOOSE_PAYMENT': "To'lov turini tanlang:",
        'ORDER_REVIEW': "Buyurtmangizni ko'rib chiqing:\n{order_list}\nTo'lov turi: {payment_type}\nYetkazib berish: {delivery_fee} UZS\nJami: {total_price} UZS",
        'currency': "UZS",
        'order_summary_title': "Buyurtma xulosasi",
        'PAYME_NOT_AVAILABLE': "Payme hozircha mavjud emas.",
        'INVALID_CHOICE_TRY_AGAIN': 'Noto\'g\'ri tanlov, iltimos qayta urinib ko\'ring.',
    },
    'ru': {
        'ORDER_BUTTON': "🛍️ Сделать заказ",
        'MY_ORDERS_BUTTON': "📦 Мои заказы",
        'ABOUT_US_BUTTON': "ℹ️ О нас",
        'ABOUT_US_MESSAGE': 'О Como Pizza',
        'FEEDBACK_BUTTON': "✍️ Оставить отзыв",
        'SHARE_CONTACT_BUTTON': "📞 Поделиться номером",
        'SHARE_LOCATION_BUTTON': "📍 Отправить локацию",
        'MENU_BUTTON': "🍽️ Меню",
        'BACK_BUTTON': "🔙 Назад",
        'CART_BUTTON': "🛒 Корзина",
        'cart_button': "🛒 Добавить в корзину",
        'ADD_MENU_BUTTON': "➕ Добавить меню",
        'ADD_PRODUCT_BUTTON': "➕ Добавить продукт",
        'DELETE_MENU_BUTTON': "🗑️ Удалить меню",
        'DELETE_PRODUCT_BUTTON': "🗑️ Удалить продукт",
        'ADMIN_PANEL_BACK_BUTTON': "🔙 Назад",
        'PAYMENT_CASH': "💵 Наличные",
        'PAYMENT_CLICK': "💳 Click",
        'PAYMENT_PAYME': "💳 Payme",
        'CONFIRM_ORDER_BUTTON': "✅ Подтвердить",
        'CANCEL_ORDER_BUTTON': "❌ Отменить",
        'CLEAN_CART_BUTTON': "🗑️ Очистить корзину",
        'GO_TO_CHECKOUT': "Оформить заказ",
        'CLEAR_CART': "Очистить корзину",
        'WELCOME_MESSAGE': "Здравствуйте! Добро пожаловать в бот. Пожалуйста, выберите одну из кнопок ниже.",
        'REQUEST_CONTACT_MESSAGE': "Чтобы поделиться номером телефона, нажмите кнопку '📞 Поделиться номером'.",
        'REQUEST_LOCATION_MESSAGE': "Чтобы отправить свою локацию, нажмите кнопку '📍 Отправить локацию'.",
        'MENU_MESSAGE': "Раздел меню.",
        'ADMIN_WELCOME_MESSAGE': "Добро пожаловать в админ-панель.",
        'NO_ACCESS_MESSAGE': "У вас нет доступа к админ-панели.",
        'ENTER_MENU_NAME': "Введите название нового меню:",
        'MENU_ADDED': "Меню успешно добавлено!",
        'MENU_ALREADY_EXISTS': "Меню с таким названием уже существует.",
        'INVALID_MENU': "Такое меню не найдено. Пожалуйста, выберите из списка.",
        'ENTER_PRODUCT_NAME': "Введите название продукта:",
        'ENTER_DESCRIPTION': "Введите описание продукта:",
        'ENTER_PRICE': "Введите цену продукта:",
        'INVALID_PRICE': "Цена введена неверно. Пожалуйста, введите целое или десятичное число.",
        'PRODUCT_ADDED': "Продукт успешно добавлен!",
        'PRODUCT_ALREADY_EXISTS': "Продукт с таким названием уже существует.",
        'PRODUCT_SELECTION': "Добро пожаловать в раздел, выберите продукт.",
        'CART_MESSAGE': "Продукты в корзине:",
        'CART_EMPTY': "Корзина пуста.",
        'ADD_TO_CART_SUCCESS': "Успешно добавлено в корзину!",
        'MIN_QUANTITY_ALERT': "Количество не может быть меньше 1.",
        'PAYMENT_CHOICE': "Выберите тип оплаты:",
        'ORDER_CONFIRMED': "Ваш заказ принят. Скоро с вами свяжется оператор.",
        'ORDER_CANCELED': "Ваш заказ отменен.",
        'CART_CLEARED': "Корзина очищена.",
        'DELIVERY_FEE': "Стоимость доставки",
        'TOTAL': "Итого",
        'LOCATION': "Локация",
        'PAYMENT_TYPE': "Тип оплаты",
        'TOTAL_BILL': "Общий счет",
        'ORDER_LIST_TITLE': "Список заказа",
        'USER': "Пользователь",
        'PHONE_NUMBER': "Номер телефона",
        'NO_ORDERS': "У вас пока нет заказов.",
        'VIEW_ORDER_DETAILS': "Детали заказа",
        'ORDER_NOT_FOUND': "Заказ не найден.",
        'BACK_TO_MAIN': "Главное меню",
        'FEEDBACK_REQUEST': "Введите свой отзыв:",
        'FEEDBACK_SUCCESS': "Ваш отзыв принят. Спасибо за ваше внимание!",
        'CHANGE_LANG_BUTTON': "🇺🇿/🇷🇺 Сменить язык",
        'NEW_ORDER': "Новый заказ!",
        'NO_LOCATION': "Геолокация отсутствует",
        'PAYMENT_LINK_MESSAGE': "Ссылка на оплату:",
        'ERROR_MESSAGE': "Произошла ошибка, попробуйте снова.",
        'PAYMENT_SUCCESS': "✅ Оплата заказа №{order_id} успешно произведена! Ваш заказ скоро будет доставлен.",
        'PAYMENT_CANCELLED': "❌ Оплата заказа №{order_id} отменена или не была завершена. Пожалуйста, оформите заказ заново.",
        'ORDER_STATUS': "Статус",
        'CLICK_PAYMENT_MESSAGE': "🧾 Для оплаты заказа №{order_id} ({total} UZS) через Click используйте кнопку ниже. После подтверждения оплаты вы получите уведомление и чек будет фискализирован.",
        'YOUR_ORDERS': "Ваши заказы",
        'BACK_MESSAGE': "Назад",
        'INVALID_PAYMENT_CHOICE': "Неверный тип оплаты",
        'INVALID_CHOICE_TRY_AGAIN': "Неверный выбор, попробуйте снова",
        'CHOOSE_PAYMENT': "Выберите тип оплаты:",
        'ORDER_REVIEW': "Проверьте ваш заказ:\n{order_list}\nТип оплаты: {payment_type}\nДоставка: {delivery_fee} UZS\nИтого: {total_price} UZS",
        'currency': "UZS",
        'order_summary_title': "Сводка заказа",
        'PAYME_NOT_AVAILABLE': 'Payme пока недоступен.',
        'INVALID_CHOICE_TRY_AGAIN': 'Неверный выбор, пожалуйста, попробуйте снова.',
    }
}

def get_text(lang, key):
    return LANGUAGES.get(lang, LANGUAGES['uz']).get(key, key)

def get_main_keyboard(lang):
    kb = [
        [types.KeyboardButton(text=get_text(lang, 'ORDER_BUTTON')), types.KeyboardButton(text=get_text(lang, 'MY_ORDERS_BUTTON'))],
        [types.KeyboardButton(text=get_text(lang, 'ABOUT_US_BUTTON')), types.KeyboardButton(text=get_text(lang, 'FEEDBACK_BUTTON'))],
        [types.KeyboardButton(text=get_text(lang, 'CHANGE_LANG_BUTTON')), types.KeyboardButton(text=get_text(lang, 'CART_BUTTON'))]
    ]
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_menu_keyboard(lang):
    menus = get_all_menus()  # Bazadan barcha menyularni olish
    keyboard = []
    row = []
    for i, menu in enumerate(menus):
        row.append(types.KeyboardButton(text=menu))
        if len(row) == 2 or i == len(menus) - 1:  # Har ikkita tugmadan so'ng yoki oxirgi menyuda
            keyboard.append(row)
            row = []
    keyboard.append([types.KeyboardButton(text=get_text(lang, 'BACK_BUTTON'))])
    
    return types.ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=True
    )

def get_products_keyboard(lang, menu_name):
    """Mahsulotlar uchun klaviatura yaratadi."""
    products = get_products_by_menu(menu_name)
    kb = []
    if not products:
        logging.info(f"{menu_name} uchun mahsulotlar topilmadi")
        kb.append([types.KeyboardButton(text=get_text(lang, 'BACK_BUTTON'))])
        return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    
    for product in products:
        kb.append([types.KeyboardButton(text=product)])
    kb.append([types.KeyboardButton(text=get_text(lang, 'BACK_BUTTON'))])
    logging.info(f"Mahsulotlar klaviaturasi: {products}")
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_admin_keyboard(lang):
    kb = [
        [types.KeyboardButton(text=get_text(lang, 'ADD_MENU_BUTTON')), types.KeyboardButton(text=get_text(lang, 'ADD_PRODUCT_BUTTON'))],
        [types.KeyboardButton(text=get_text(lang, 'DELETE_MENU_BUTTON')), types.KeyboardButton(text=get_text(lang, 'DELETE_PRODUCT_BUTTON'))],
        [types.KeyboardButton(text=get_text(lang, 'ADMIN_PANEL_BACK_BUTTON'))]
    ]
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_admin_menu_keyboard(lang):
    menus = get_all_menus()
    kb = [[types.KeyboardButton(text=menu)] for menu in menus]
    kb.append([types.KeyboardButton(text=get_text(lang, 'ADMIN_PANEL_BACK_BUTTON'))])
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_language_keyboard():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="O'zbekcha")],
            [types.KeyboardButton(text="Русский")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def get_cart_keyboard(lang, share_contact=False, share_location=False):
    kb = []
   
    if share_contact:
        # Telefon raqam so'rash holati
        kb = [[types.KeyboardButton(text=get_text(lang, 'SHARE_CONTACT_BUTTON'), request_contact=True)]]
    elif share_location:
        # Manzil so'rash holati
        kb = [[types.KeyboardButton(text=get_text(lang, 'SHARE_LOCATION_BUTTON'), request_location=True)]]
    else:
        # Savatni ko'rish holati
        kb = [
            [
                types.KeyboardButton(text=get_text(lang, 'GO_TO_CHECKOUT')),
                types.KeyboardButton(text=get_text(lang, 'CLEAR_CART'))
            ],
            [types.KeyboardButton(text=get_text(lang, 'BACK_BUTTON'))]
        ]
       
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, one_time_keyboard=True)

def get_order_payment_keyboard(lang):
    """To'lov turini tanlash klaviaturasi (Cash, Click, Payme)"""
    kb = [
        [types.KeyboardButton(text=get_text(lang, 'PAYMENT_CASH'))],
        [types.KeyboardButton(text=get_text(lang, 'PAYMENT_CLICK')), types.KeyboardButton(text=get_text(lang, 'PAYMENT_PAYME'))],
        [types.KeyboardButton(text=get_text(lang, 'BACK_BUTTON'))]
    ]
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_order_confirm_keyboard(lang):
    """Buyurtmani tasdiqlash yoki bekor qilish klaviaturasi"""
    kb = [
        [types.KeyboardButton(text=get_text(lang, 'CONFIRM_ORDER_BUTTON'))],
        [types.KeyboardButton(text=get_text(lang, 'CANCEL_ORDER_BUTTON'))]
    ]
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_product_inline_keyboard(product_name, current_quantity=1):
    """Mahsulotga qo'shish uchun Inline klaviatura (callback_data ishlatiladi)"""
    kb = [
        [
            types.InlineKeyboardButton(text="➖", callback_data=f"qty_dec_{product_name}"),
            types.InlineKeyboardButton(text=str(current_quantity), callback_data="quantity_placeholder"), 
            types.InlineKeyboardButton(text="➕", callback_data=f"qty_inc_{product_name}")
        ],
        [
            types.InlineKeyboardButton(text="🛒 Savatga solish", callback_data=f"add_to_cart_{product_name}")
        ]
    ]

    return types.InlineKeyboardMarkup(inline_keyboard=kb)






