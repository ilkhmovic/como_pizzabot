from aiogram.fsm.state import State, StatesGroup

# Buyurtma berish jarayoni uchun holatlar
class OrderState(StatesGroup):
    choosing_product = State()
    entering_name = State()
    entering_phone = State()
    confirming_order = State()
    waiting_for_location = State()
    in_menu = State()  # Menyu bo'limida ekanligini bildiradi

# Admin paneli holatlari
class AdminState(StatesGroup):
    admin_panel = State()
    adding_menu = State()
    adding_product = State()
    choosing_menu_for_product = State()
    entering_product_name = State()
    entering_product_description = State()
    entering_product_price = State()
    deleting_menu = State()
    deleting_product = State()

# Menyu bo'limi holati
class MenuState(StatesGroup):
    in_menu = State()
    in_category = State() # Menyu ichidagi mahsulotlar bo'limi
    in_product_details = State()

class OrderConfirmationState(StatesGroup):
    choosing_payment = State()
    confirming_order = State()
    requesting_location = State()

class MyOrdersState(StatesGroup):
    viewing_orders = State()
    viewing_single_order = State()

class FeedbackState(StatesGroup):
    entering_feedback = State()

class LanguageState(StatesGroup):
    choosing_language = State()