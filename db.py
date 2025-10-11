import sqlite3
import logging
from datetime import datetime

DATABASE_NAME = "bot_data.db"

def get_connection():
    return sqlite3.connect(DATABASE_NAME)

def init_db():
    """Ma'lumotlar bazasini boshlang'ich sozlash."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Jadvallarni yaratish
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                phone_number TEXT,
                latitude REAL,
                longitude REAL,
                language TEXT DEFAULT 'uz'
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS menus (
                menu_name TEXT PRIMARY KEY
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                product_name TEXT PRIMARY KEY,
                menu_name TEXT,
                description TEXT,
                price REAL,
                FOREIGN KEY (menu_name) REFERENCES menus(menu_name)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cart (
                user_id INTEGER,
                product_name TEXT,
                quantity INTEGER,
                PRIMARY KEY (user_id, product_name)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                total_price REAL,
                created_at TEXT,
                status TEXT,
                payment_type TEXT,
                user_first_name TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS order_items (
                order_id INTEGER,
                product_name TEXT,
                quantity INTEGER,
                price REAL,
                FOREIGN KEY (order_id) REFERENCES orders(order_id)
            )
        ''')

        # Dastlabki ma'lumotlarni faqat bo'sh bo'lsa qo'shish
        cursor.execute("SELECT count(*) FROM menus")
        if cursor.fetchone()[0] == 0:  # Agar menus jadvali bo'sh bo'lsa
            cursor.execute("INSERT OR IGNORE INTO menus (menu_name) VALUES ('Fast Food')")
            cursor.execute("INSERT OR IGNORE INTO menus (menu_name) VALUES ('Ichimliklar')")
            cursor.execute("INSERT OR IGNORE INTO menus (menu_name) VALUES ('Pitsa')")
            cursor.execute("INSERT OR IGNORE INTO products (product_name, menu_name, description, price) VALUES (?, ?, ?, ?)",
                          ('Burger', 'Fast Food', 'Mazali burger', 25000))
            cursor.execute("INSERT OR IGNORE INTO products (product_name, menu_name, description, price) VALUES (?, ?, ?, ?)",
                          ('Cola', 'Ichimliklar', 'Yaxshi ichimlik', 10000))
            cursor.execute("INSERT OR IGNORE INTO products (product_name, menu_name, description, price) VALUES (?, ?, ?, ?)",
                          ('Naomi', 'Pitsa', 'Jejiajbeoqlns', 12000))
        
        conn.commit()
        logging.info("Ma'lumotlar bazasi muvaffaqiyatli sozlandi")
    except sqlite3.Error as e:
        logging.error(f"Ma'lumotlar bazasini sozlashda xato: {e}")
        raise
    finally:
        conn.close()

def save_user_data(user_id, phone_number, latitude=None, longitude=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO users (user_id, phone_number, latitude, longitude) VALUES (?, ?, ?, ?)",
                   (user_id, phone_number, latitude, longitude))
    conn.commit()
    conn.close()

def get_user_data(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def update_user_location(user_id, latitude, longitude):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET latitude = ?, longitude = ? WHERE user_id = ?", (latitude, longitude, user_id))
    conn.commit()
    conn.close()

def update_user_language(user_id, lang):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET language = ? WHERE user_id = ?", (lang, user_id))
    conn.commit()
    conn.close()

def get_user_language(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT language FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 'uz'

def update_user_language_and_save_data(user_id, lang):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO users (user_id, language) VALUES (?, ?)", (user_id, lang))
    conn.commit()
    conn.close()

def add_menu_to_db(name):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO menus (menu_name) VALUES (?)", (name,))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_all_menus():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT menu_name FROM menus")
    menus = [row[0] for row in cursor.fetchall()]
    conn.close()
    return menus

def add_product_to_db(menu_name, product_name, description, price):
    """Mahsulotni bazaga qo'shadi."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # menu_name mavjudligini tekshirish
        cursor.execute("SELECT menu_name FROM menus WHERE menu_name = ?", (menu_name,))
        if not cursor.fetchone():
            logging.error(f"Menu {menu_name} mavjud emas")
            return False
        cursor.execute("INSERT INTO products (product_name, menu_name, description, price) VALUES (?, ?, ?, ?)",
                       (product_name, menu_name, description, price))
        conn.commit()
        logging.info(f"Mahsulot qo'shildi: {product_name}, Menu: {menu_name}")
        return True
    except sqlite3.IntegrityError as e:
        logging.error(f"Mahsulot qo'shishda xato: {e}")
        return False
    finally:
        conn.close()

def get_products_by_menu(menu_name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT product_name FROM products WHERE menu_name = ?", (menu_name,))
    products = [row[0] for row in cursor.fetchall()]
    logging.info(f"SQL so'rovi: SELECT product_name FROM products WHERE menu_name = {menu_name}")
    logging.info(f"Natija: {products}")
    conn.close()
    return products

def get_product_details(product_name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT product_name, description, price FROM products WHERE product_name = ?", (product_name,))
    details = cursor.fetchone()
    conn.close()
    return details

def get_product_price(product_name):
    details = get_product_details(product_name)
    return details[2] if details else 0

def delete_menu_from_db(menu_name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE menu_name = ?", (menu_name,))
    cursor.execute("DELETE FROM menus WHERE menu_name = ?", (menu_name,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

def delete_product_from_db(product_name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE product_name = ?", (product_name,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

def add_to_cart(user_id, product_name, quantity):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO cart (user_id, product_name, quantity) VALUES (?, ?, ?)",
                   (user_id, product_name, quantity))
    conn.commit()
    conn.close()

def get_cart_items(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT product_name, quantity FROM cart WHERE user_id = ?", (user_id,))
    items = cursor.fetchall()
    conn.close()
    return items

def clear_cart(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def remove_from_cart(user_id, product_name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM cart WHERE user_id = ? AND product_name = ?", (user_id, product_name))
    conn.commit()
    conn.close()

def save_order(user_id, total_price, cart_items, payment_type, user_first_name="Foydalanuvchi", status='pending'):
    conn = get_connection()
    cursor = conn.cursor()
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        cursor.execute("INSERT INTO orders (user_id, total_price, created_at, status, payment_type, user_first_name) VALUES (?, ?, ?, ?, ?, ?)",
                       (user_id, total_price, created_at, status, payment_type, user_first_name))
        order_id = cursor.lastrowid
        
        for item in cart_items:
            product_name, quantity = item
            price = get_product_price(product_name)
            cursor.execute("INSERT INTO order_items (order_id, product_name, quantity, price) VALUES (?, ?, ?, ?)",
                           (order_id, product_name, quantity, price))
        
        conn.commit()
        logging.info(f"Buyurtma saqlandi: ID={order_id}, Status={status}, To'lov={payment_type}")
        return order_id
        
    except Exception as e:
        logging.error(f"Buyurtma saqlash xatosi: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()

def get_user_orders(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT order_id, total_price, created_at FROM orders WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
    orders = cursor.fetchall()
    conn.close()
    return orders

def get_order_items_by_id(order_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT product_name, quantity, price FROM order_items WHERE order_id = ?", (order_id,))
    items = cursor.fetchall()
    conn.close()
    return items

def get_order_by_id(order_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,))
    order = cursor.fetchone()
    conn.close()
    return order

def update_order_status(order_id, status):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET status = ? WHERE order_id = ?", (status, order_id))
    conn.commit()
    conn.close()
    logging.info(f"Buyurtma holati yangilandi: ID={order_id}, Yangi status={status}")


