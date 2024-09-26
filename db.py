import sqlite3
import threading
from product import Product
from category import Category

conn = sqlite3.connect('shop_db.sqlite', check_same_thread=False)
cursor = conn.cursor()
db_lock = threading.Lock()

def init_database():
    # Create product table
    cursor.execute('''CREATE TABLE IF NOT EXISTS products (
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      caption TEXT,
                      description TEXT,
                      price REAL,
                      media_type TEXT,
                      media_id TEXT,
                      category TEXT
                    )''')
    conn.commit()

    # Create category table
    cursor.execute('''CREATE TABLE IF NOT EXISTS categories (
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      name TEXT UNIQUE
                   )''')
    conn.commit()

def get_all_products():
    with db_lock:
        cursor.execute("SELECT * FROM products")
        rows = cursor.fetchall()
        return [Product(id=row[0], caption=row[1], description=row[2], price=row[3], media_type=row[4], media_id=row[5], category=row[6]) for row in rows]

def get_products_by_category(category):
    with db_lock:
        cursor.execute("SELECT * FROM products WHERE category=?", (category,))
        rows = cursor.fetchall()
        return [Product(id=row[0], caption=row[1], description=row[2], price=row[3], media_type=row[4], media_id=row[5], category=row[6]) for row in rows]

def add_product(caption, description, price, media_type=None, media_id=None, category=None):
    with db_lock:
        cursor.execute("INSERT INTO products (caption, description, price, media_type, media_id, category) VALUES (?, ?, ?, ?, ?, ?)", (caption, description, price, media_type, media_id, category))
        return conn.commit()
    
def delete_product(product_id):
    with db_lock:
        cursor.execute("DELETE FROM products WHERE id=?", (product_id,))
        return conn.commit()

def add_category(name):
    with db_lock:
        try:
            cursor.execute("INSERT INTO categories (name) VALUES (?)", (name,))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            # Category with the same name already exists
            return False

def delete_category(name):
    with db_lock:
        print (name)
        print (cursor.execute("DELETE FROM categories WHERE name=?", (name,)))
        return conn.commit()

def get_all_categories():
    with db_lock:
        cursor.execute("SELECT * FROM categories")
        rows = cursor.fetchall()
        return [Category(id=row[0], name=row[1]) for row in rows]

if __name__ == "__main__":
    print (delete_category("❌ Delete category"))