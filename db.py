import os
from supabase import create_client, Client
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

# Supabase ulanish
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def init_db():
    """Ma'lumotlar bazasini boshlang'ich sozlash."""
    try:
        # Jadvallar avtomatik yaratiladi, faqat dastlabki ma'lumotlarni qo'shamiz
        response = supabase.table("menus").select("menu_name").execute()
        
        if len(response.data) == 0:
            # Dastlabki ma'lumotlarni qo'shish
            menus = [
                {"menu_name": "Fast Food"},
                {"menu_name": "Ichimliklar"},
                {"menu_name": "Pitsa"}
            ]
            supabase.table("menus").insert(menus).execute()
            
            products = [
                {"product_name": "Burger", "menu_name": "Fast Food", "description": "Mazali burger", "price": 25000},
                {"product_name": "Cola", "menu_name": "Ichimliklar", "description": "Yaxshi ichimlik", "price": 10000},
                {"product_name": "Naomi", "menu_name": "Pitsa", "description": "Jejiajbeoqlns", "price": 12000}
            ]
            supabase.table("products").insert(products).execute()
        
        logging.info("Ma'lumotlar bazasi muvaffaqiyatli sozlandi")
    except Exception as e:
        logging.error(f"Ma'lumotlar bazasini sozlashda xato: {e}")
        raise

def save_user_data(user_id: int, phone_number: str, latitude: float = None, longitude: float = None):
    try:
        data = {
            "user_id": user_id,
            "phone_number": phone_number,
            "latitude": latitude,
            "longitude": longitude
        }
        supabase.table("users").upsert(data).execute()
    except Exception as e:
        logging.error(f"User saqlashda xato: {e}")

def get_user_data(user_id: int) -> Optional[Dict[str, Any]]:
    try:
        response = supabase.table("users").select("*").eq("user_id", user_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        logging.error(f"User olishda xato: {e}")
        return None

def update_user_location(user_id: int, latitude: float, longitude: float):
    try:
        supabase.table("users").update({
            "latitude": latitude,
            "longitude": longitude
        }).eq("user_id", user_id).execute()
    except Exception as e:
        logging.error(f"Location yangilashda xato: {e}")

def update_user_language(user_id: int, lang: str):
    try:
        supabase.table("users").update({
            "language": lang
        }).eq("user_id", user_id).execute()
    except Exception as e:
        logging.error(f"Language yangilashda xato: {e}")

def get_user_language(user_id: int) -> str:
    try:
        response = supabase.table("users").select("language").eq("user_id", user_id).execute()
        return response.data[0]["language"] if response.data else "uz"
    except Exception as e:
        logging.error(f"Language olishda xato: {e}")
        return "uz"

def add_menu_to_db(name: str) -> bool:
    try:
        supabase.table("menus").insert({"menu_name": name}).execute()
        return True
    except Exception as e:
        logging.error(f"Menu qo'shishda xato: {e}")
        return False

def get_all_menus() -> List[str]:
    try:
        response = supabase.table("menus").select("menu_name").execute()
        return [item["menu_name"] for item in response.data]
    except Exception as e:
        logging.error(f"Menularni olishda xato: {e}")
        return []

def add_product_to_db(menu_name: str, product_name: str, description: str, price: float) -> bool:
    try:
        # Menu mavjudligini tekshirish
        menu_response = supabase.table("menus").select("menu_name").eq("menu_name", menu_name).execute()
        if not menu_response.data:
            logging.error(f"Menu {menu_name} mavjud emas")
            return False
        
        data = {
            "product_name": product_name,
            "menu_name": menu_name,
            "description": description,
            "price": price
        }
        supabase.table("products").insert(data).execute()
        logging.info(f"Mahsulot qo'shildi: {product_name}, Menu: {menu_name}")
        return True
    except Exception as e:
        logging.error(f"Mahsulot qo'shishda xato: {e}")
        return False

def get_products_by_menu(menu_name: str) -> List[str]:
    try:
        response = supabase.table("products").select("product_name").eq("menu_name", menu_name).execute()
        products = [item["product_name"] for item in response.data]
        logging.info(f"Menu: {menu_name}, Mahsulotlar: {products}")
        return products
    except Exception as e:
        logging.error(f"Mahsulotlarni olishda xato: {e}")
        return []

def get_product_details(product_name: str) -> Optional[Dict[str, Any]]:
    try:
        response = supabase.table("products").select("*").eq("product_name", product_name).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        logging.error(f"Mahsulot ma'lumotlarini olishda xato: {e}")
        return None

def get_product_price(product_name: str) -> float:
    details = get_product_details(product_name)
    return details["price"] if details else 0

def delete_menu_from_db(menu_name: str) -> bool:
    try:
        # Avval products jadvalidan o'chirish
        supabase.table("products").delete().eq("menu_name", menu_name).execute()
        # Keyin menu ni o'chirish
        response = supabase.table("menus").delete().eq("menu_name", menu_name).execute()
        return len(response.data) > 0
    except Exception as e:
        logging.error(f"Menu o'chirishda xato: {e}")
        return False

def delete_product_from_db(product_name: str) -> bool:
    try:
        response = supabase.table("products").delete().eq("product_name", product_name).execute()
        return len(response.data) > 0
    except Exception as e:
        logging.error(f"Mahsulot o'chirishda xato: {e}")
        return False

def add_to_cart(user_id: int, product_name: str, quantity: int):
    try:
        data = {
            "user_id": user_id,
            "product_name": product_name,
            "quantity": quantity
        }
        supabase.table("cart").upsert(data).execute()
    except Exception as e:
        logging.error(f"Cart ga qo'shishda xato: {e}")

def get_cart_items(user_id: int) -> List[tuple]:
    try:
        response = supabase.table("cart").select("product_name, quantity").eq("user_id", user_id).execute()
        return [(item["product_name"], item["quantity"]) for item in response.data]
    except Exception as e:
        logging.error(f"Cart ni olishda xato: {e}")
        return []

def clear_cart(user_id: int):
    try:
        supabase.table("cart").delete().eq("user_id", user_id).execute()
    except Exception as e:
        logging.error(f"Cart ni tozalashda xato: {e}")

def remove_from_cart(user_id: int, product_name: str):
    try:
        supabase.table("cart").delete().eq("user_id", user_id).eq("product_name", product_name).execute()
    except Exception as e:
        logging.error(f"Cart dan o'chirishda xato: {e}")

def save_order(user_id: int, total_price: float, cart_items: List[tuple], payment_type: str, user_first_name: str = "Foydalanuvchi", status: str = 'pending') -> Optional[int]:
    try:
        # Order yaratish
        order_data = {
            "user_id": user_id,
            "total_price": total_price,
            "status": status,
            "payment_type": payment_type,
            "user_first_name": user_first_name
        }
        order_response = supabase.table("orders").insert(order_data).execute()
        
        if order_response.data:
            order_id = order_response.data[0]["order_id"]
            
            # Order items qo'shish
            for item in cart_items:
                product_name, quantity = item
                price = get_product_price(product_name)
                
                item_data = {
                    "order_id": order_id,
                    "product_name": product_name,
                    "quantity": quantity,
                    "price": price
                }
                supabase.table("order_items").insert(item_data).execute()
            
            logging.info(f"Buyurtma saqlandi: ID={order_id}, Status={status}, To'lov={payment_type}")
            return order_id
        
        return None
        
    except Exception as e:
        logging.error(f"Buyurtma saqlash xatosi: {e}")
        return None

def get_user_orders(user_id: int) -> List[tuple]:
    try:
        response = supabase.table("orders").select("order_id, total_price, created_at").eq("user_id", user_id).order("created_at", desc=True).execute()
        return [(order["order_id"], order["total_price"], order["created_at"]) for order in response.data]
    except Exception as e:
        logging.error(f"Buyurtmalarni olishda xato: {e}")
        return []

def get_order_items_by_id(order_id: int) -> List[tuple]:
    try:
        response = supabase.table("order_items").select("product_name, quantity, price").eq("order_id", order_id).execute()
        return [(item["product_name"], item["quantity"], item["price"]) for item in response.data]
    except Exception as e:
        logging.error(f"Buyurtma elementlarini olishda xato: {e}")
        return []

def get_order_by_id(order_id: int) -> Optional[Dict[str, Any]]:
    try:
        response = supabase.table("orders").select("*").eq("order_id", order_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        logging.error(f"Buyurtmani olishda xato: {e}")
        return None

def update_order_status(order_id: int, status: str):
    try:
        supabase.table("orders").update({"status": status}).eq("order_id", order_id).execute()
        logging.info(f"Buyurtma holati yangilandi: ID={order_id}, Yangi status={status}")
    except Exception as e:
        logging.error(f"Buyurtma holatini yangilashda xato: {e}")
