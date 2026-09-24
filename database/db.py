import sqlite3
import os
from datetime import datetime
from werkzeug.security import generate_password_hash
from database.schema import SCHEMA_SQL, SAMPLE_PRODUCTS

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'smartbiz.db')

def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn

def now():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def init_db():
    conn = get_db()
    conn.executescript(SCHEMA_SQL)
    
    # Auto-migrate image_data column if it doesn't exist
    cols = [col['name'] for col in conn.execute("PRAGMA table_info(products)").fetchall()]
    if 'image_data' not in cols:
        conn.execute("ALTER TABLE products ADD COLUMN image_data TEXT")
        conn.commit()
    
    # Seed default sample users if empty
    if conn.execute('SELECT COUNT(*) n FROM users').fetchone()['n'] == 0:
        sample_users = [
            ('Administrator', 'admin@smartbiz.com', generate_password_hash('admin123'), 'Super Admin', now()),
            ('Krishna Karthik', 'krishna@smartbiz.com', generate_password_hash('krishna123'), 'Business Admin', now()),
            ('Sophia Vance', 'finance@smartbiz.com', generate_password_hash('finance123'), 'Finance Manager', now()),
            ('Marcus Chen', 'inventory@smartbiz.com', generate_password_hash('inventory123'), 'Inventory Manager', now()),
            ('Sarah Jenkins', 'sales@smartbiz.com', generate_password_hash('sales123'), 'Sales Manager', now()),
            ('David Miller', 'purchase@smartbiz.com', generate_password_hash('purchase123'), 'Purchase Manager', now()),
            ('Elena Rostova', 'hr@smartbiz.com', generate_password_hash('hr123'), 'HR Manager', now()),
            ('Alex Rivera', 'salesstaff@smartbiz.com', generate_password_hash('staff123'), 'Sales Staff', now()),
            ('Liam Wright', 'inventorystaff@smartbiz.com', generate_password_hash('staff123'), 'Inventory Staff', now())
        ]
        conn.executemany('INSERT INTO users(name,email,password,role,created_at) VALUES(?,?,?,?,?)', sample_users)
        
    # Seed default products if empty
    if conn.execute('SELECT COUNT(*) n FROM products').fetchone()['n'] == 0:
        products_to_insert = [
            (sku, name, cat, buy, sell, stock, min_s, wh, now())
            for (sku, name, cat, buy, sell, stock, min_s, wh) in SAMPLE_PRODUCTS
        ]
        conn.executemany(
            'INSERT INTO products(sku,name,category,purchase_price,selling_price,stock,min_stock,warehouse,created_at) VALUES(?,?,?,?,?,?,?,?,?)',
            products_to_insert
        )
    conn.commit()
    conn.close()
