from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_file
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3, os, io
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'smartbiz-erp-secret-key-2026')
DB = os.path.join(os.path.dirname(__file__), 'smartbiz.db')

ROLES = {
    'Super Admin': ['dashboard','users','products','inventory','customers','suppliers','sales','purchases','expenses','finance','employees','reports'],
    'Business Admin': ['dashboard','products','inventory','customers','suppliers','sales','purchases','expenses','finance','employees','reports'],
    'Finance Manager': ['dashboard','expenses','finance','reports'],
    'Inventory Manager': ['dashboard','products','inventory','suppliers','purchases','reports'],
    'Sales Manager': ['dashboard','customers','sales','reports'],
    'Purchase Manager': ['dashboard','suppliers','purchases','inventory','reports'],
    'HR Manager': ['dashboard','employees','reports'],
    'Sales Staff': ['dashboard','customers','sales'],
    'Inventory Staff': ['dashboard','products','inventory']
}

def to_float(val, default=0.0):
    try:
        if val is None:
            return default
        s = str(val).strip()
        return float(s) if s != '' else default
    except (ValueError, TypeError):
        return default

def to_int(val, default=0):
    try:
        if val is None:
            return default
        s = str(val).strip()
        return int(s) if s != '' else default
    except (ValueError, TypeError):
        return default

def db():
    c = sqlite3.connect(DB, timeout=20)
    c.row_factory = sqlite3.Row
    c.execute('PRAGMA foreign_keys = ON')
    return c

def now():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def init_db():
    c = db()
    c.executescript('''
    CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, password TEXT NOT NULL, role TEXT NOT NULL, created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS products(id INTEGER PRIMARY KEY AUTOINCREMENT, sku TEXT UNIQUE NOT NULL, name TEXT NOT NULL, category TEXT, purchase_price REAL DEFAULT 0, selling_price REAL DEFAULT 0, stock INTEGER DEFAULT 0, min_stock INTEGER DEFAULT 0, warehouse TEXT DEFAULT 'Main Warehouse', created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS customers(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, phone TEXT, email TEXT, address TEXT, created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS suppliers(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, phone TEXT, email TEXT, address TEXT, created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS sales(id INTEGER PRIMARY KEY AUTOINCREMENT, customer_id INTEGER, invoice_no TEXT UNIQUE NOT NULL, total REAL NOT NULL, payment_status TEXT DEFAULT 'Paid', payment_method TEXT, created_at TEXT NOT NULL, FOREIGN KEY(customer_id) REFERENCES customers(id));
    CREATE TABLE IF NOT EXISTS sale_items(id INTEGER PRIMARY KEY AUTOINCREMENT, sale_id INTEGER, product_id INTEGER, qty INTEGER, unit_price REAL, FOREIGN KEY(sale_id) REFERENCES sales(id), FOREIGN KEY(product_id) REFERENCES products(id));
    CREATE TABLE IF NOT EXISTS purchases(id INTEGER PRIMARY KEY AUTOINCREMENT, supplier_id INTEGER, po_no TEXT UNIQUE NOT NULL, total REAL NOT NULL, payment_status TEXT DEFAULT 'Pending', created_at TEXT NOT NULL, FOREIGN KEY(supplier_id) REFERENCES suppliers(id));
    CREATE TABLE IF NOT EXISTS purchase_items(id INTEGER PRIMARY KEY AUTOINCREMENT, purchase_id INTEGER, product_id INTEGER, qty INTEGER, unit_price REAL, FOREIGN KEY(purchase_id) REFERENCES purchases(id), FOREIGN KEY(product_id) REFERENCES products(id));
    CREATE TABLE IF NOT EXISTS expenses(id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT NOT NULL, description TEXT, amount REAL NOT NULL, payment_method TEXT, created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS employees(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, department TEXT, job_role TEXT, salary REAL DEFAULT 0, status TEXT DEFAULT 'Active', created_at TEXT NOT NULL);
    ''')
    if c.execute('SELECT COUNT(*) n FROM users').fetchone()['n'] == 0:
        c.execute('INSERT INTO users(name,email,password,role,created_at) VALUES(?,?,?,?,?)', ('Administrator','admin@smartbiz.com',generate_password_hash('admin123'),'Super Admin',now()))
    if c.execute('SELECT COUNT(*) n FROM products').fetchone()['n'] == 0:
        c.executemany('INSERT INTO products(sku,name,category,purchase_price,selling_price,stock,min_stock,warehouse,created_at) VALUES(?,?,?,?,?,?,?,?,?)', [
            ('KB-001','Wireless Keyboard','Accessories',500,800,113,20,'Main Warehouse',now()),
            ('GM-001','Gaming Mouse','Accessories',700,1200,59,15,'Main Warehouse',now()),
            ('HP-001','Headphones','Audio',900,1500,12,20,'Main Warehouse',now())])
    c.commit(); c.close()

def logged_in():
    return 'user_id' in session

def can(module):
    return logged_in() and module in ROLES.get(session.get('role'), [])

@app.context_processor
def inject():
    return {'session_user': session, 'can': can}

def require(module):
    if not logged_in():
        flash('Please login to access this section.', 'warning')
        return False
    if not can(module):
        flash('You do not have permission for this module.', 'danger')
        return False
    return True

@app.route('/')
def index():
    return redirect(url_for('dashboard' if logged_in() else 'login'))

@app.route('/login', methods=['GET','POST'])
def login():
    if logged_in():
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        c = db()
        u = c.execute('SELECT * FROM users WHERE email=?', (email,)).fetchone()
        c.close()
        if u and check_password_hash(u['password'], password):
            session.update(user_id=u['id'], name=u['name'], role=u['role'], email=u['email'])
            flash(f'Welcome back, {u["name"]}!', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid email or password', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if not require('dashboard'):
        return redirect(url_for('login'))
    c = db()
    revenue = c.execute("SELECT COALESCE(SUM(total),0) v FROM sales").fetchone()['v']
    expenses = c.execute("SELECT COALESCE(SUM(amount),0) v FROM expenses").fetchone()['v']
    purchases = c.execute("SELECT COALESCE(SUM(total),0) v FROM purchases").fetchone()['v']
    customers = c.execute('SELECT COUNT(*) v FROM customers').fetchone()['v']
    orders = c.execute('SELECT COUNT(*) v FROM sales').fetchone()['v']
    low = c.execute('SELECT * FROM products WHERE stock <= min_stock ORDER BY stock ASC').fetchall()
    recent = c.execute('SELECT s.*, c.name customer FROM sales s LEFT JOIN customers c ON c.id=s.customer_id ORDER BY s.id DESC LIMIT 8').fetchall()
    monthly_rows = c.execute("SELECT substr(created_at,1,7) month, SUM(total) total FROM sales GROUP BY month ORDER BY month DESC LIMIT 6").fetchall()
    monthly = [{'month': m['month'], 'total': float(m['total'])} for m in reversed(monthly_rows)]
    c.close()
    return render_template('dashboard.html', revenue=revenue, expenses=expenses, purchases=purchases, profit=revenue-expenses, customers=customers, orders=orders, low=low, recent=recent, monthly=monthly)

@app.route('/products', methods=['GET','POST'])
def products():
    if not require('products'):
        return redirect(url_for('dashboard'))
    c = db()
    if request.method == 'POST':
        sku = request.form.get('sku', '').strip()
        name = request.form.get('name', '').strip()
        category = request.form.get('category', '').strip()
        warehouse = request.form.get('warehouse', '').strip() or 'Main Warehouse'
        purchase_price = to_float(request.form.get('purchase_price'), 0.0)
        selling_price = to_float(request.form.get('selling_price'), 0.0)
        stock = to_int(request.form.get('stock'), 0)
        min_stock = to_int(request.form.get('min_stock'), 0)

        if not sku or not name:
            flash('SKU and Product Name are required.', 'danger')
        else:
            try:
                c.execute('INSERT INTO products(sku,name,category,purchase_price,selling_price,stock,min_stock,warehouse,created_at) VALUES(?,?,?,?,?,?,?,?,?)',
                          (sku, name, category, purchase_price, selling_price, stock, min_stock, warehouse, now()))
                c.commit()
                flash('Product added successfully', 'success')
            except sqlite3.IntegrityError:
                flash(f'Product with SKU "{sku}" already exists.', 'danger')
    rows = c.execute('SELECT * FROM products ORDER BY id DESC').fetchall()
    c.close()
    return render_template('products.html', products=rows)

@app.route('/products/edit/<int:item_id>', methods=['GET','POST'])
def edit_product(item_id):
    if not require('products'):
        return redirect(url_for('dashboard'))
    c = db()
    item = c.execute('SELECT * FROM products WHERE id=?', (item_id,)).fetchone()
    if not item:
        c.close()
        flash('Product not found', 'danger')
        return redirect(url_for('products'))
    if request.method == 'POST':
        sku = request.form.get('sku', '').strip()
        name = request.form.get('name', '').strip()
        category = request.form.get('category', '').strip()
        warehouse = request.form.get('warehouse', '').strip() or 'Main Warehouse'
        purchase_price = to_float(request.form.get('purchase_price'), 0.0)
        selling_price = to_float(request.form.get('selling_price'), 0.0)
        stock = to_int(request.form.get('stock'), 0)
        min_stock = to_int(request.form.get('min_stock'), 0)

        if not sku or not name:
            flash('SKU and Product Name are required.', 'danger')
        else:
            try:
                c.execute('UPDATE products SET sku=?,name=?,category=?,purchase_price=?,selling_price=?,stock=?,min_stock=?,warehouse=? WHERE id=?',
                          (sku, name, category, purchase_price, selling_price, stock, min_stock, warehouse, item_id))
                c.commit()
                c.close()
                flash('Product updated successfully', 'success')
                return redirect(url_for('products'))
            except sqlite3.IntegrityError:
                flash(f'Product with SKU "{sku}" already exists.', 'danger')
    c.close()
    return render_template('edit.html', entity='Product', item=item, fields=[
        ('sku','SKU','text'),
        ('name','Product Name','text'),
        ('category','Category','text'),
        ('purchase_price','Purchase Price','number'),
        ('selling_price','Selling Price','number'),
        ('stock','Stock','number'),
        ('min_stock','Minimum Stock','number'),
        ('warehouse','Warehouse','text')
    ], back_url=url_for('products'))

@app.route('/products/delete/<int:item_id>', methods=['POST'])
def delete_product(item_id):
    if not require('products'):
        return redirect(url_for('dashboard'))
    c = db()
    has_sales = c.execute('SELECT COUNT(*) n FROM sale_items WHERE product_id=?', (item_id,)).fetchone()['n']
    has_purchases = c.execute('SELECT COUNT(*) n FROM purchase_items WHERE product_id=?', (item_id,)).fetchone()['n']
    if has_sales > 0 or has_purchases > 0:
        c.close()
        flash('Cannot delete this product because it has past sales or purchase transactions associated with it.', 'danger')
        return redirect(url_for('products'))
    c.execute('DELETE FROM products WHERE id=?', (item_id,))
    c.commit()
    c.close()
    flash('Product deleted successfully', 'success')
    return redirect(url_for('products'))

@app.route('/customers', methods=['GET','POST'])
def customers():
    if not require('customers'):
        return redirect(url_for('dashboard'))
    c = db()
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        address = request.form.get('address', '').strip()
        if not name:
            flash('Customer name is required.', 'danger')
        else:
            c.execute('INSERT INTO customers(name,phone,email,address,created_at) VALUES(?,?,?,?,?)', (name, phone, email, address, now()))
            c.commit()
            flash('Customer added successfully', 'success')
    rows = c.execute('SELECT * FROM customers ORDER BY id DESC').fetchall()
    c.close()
    return render_template('customers.html', customers=rows)

@app.route('/customers/edit/<int:item_id>', methods=['GET','POST'])
def edit_customer(item_id):
    if not require('customers'):
        return redirect(url_for('dashboard'))
    c = db()
    item = c.execute('SELECT * FROM customers WHERE id=?', (item_id,)).fetchone()
    if not item:
        c.close()
        flash('Customer not found', 'danger')
        return redirect(url_for('customers'))
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        address = request.form.get('address', '').strip()
        if not name:
            flash('Customer name is required.', 'danger')
        else:
            c.execute('UPDATE customers SET name=?,phone=?,email=?,address=? WHERE id=?', (name, phone, email, address, item_id))
            c.commit()
            c.close()
            flash('Customer updated successfully', 'success')
            return redirect(url_for('customers'))
    c.close()
    return render_template('edit.html', entity='Customer', item=item, fields=[
        ('name','Name','text'),
        ('phone','Phone','text'),
        ('email','Email','email'),
        ('address','Address','text')
    ], back_url=url_for('customers'))

@app.route('/customers/delete/<int:item_id>', methods=['POST'])
def delete_customer(item_id):
    if not require('customers'):
        return redirect(url_for('dashboard'))
    c = db()
    c.execute('UPDATE sales SET customer_id=NULL WHERE customer_id=?', (item_id,))
    c.execute('DELETE FROM customers WHERE id=?', (item_id,))
    c.commit()
    c.close()
    flash('Customer deleted successfully (historical sales preserved as walk-in)', 'success')
    return redirect(url_for('customers'))

@app.route('/suppliers', methods=['GET','POST'])
def suppliers():
    if not require('suppliers'):
        return redirect(url_for('dashboard'))
    c = db()
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        address = request.form.get('address', '').strip()
        if not name:
            flash('Supplier name is required.', 'danger')
        else:
            c.execute('INSERT INTO suppliers(name,phone,email,address,created_at) VALUES(?,?,?,?,?)', (name, phone, email, address, now()))
            c.commit()
            flash('Supplier added successfully', 'success')
    rows = c.execute('SELECT * FROM suppliers ORDER BY id DESC').fetchall()
    c.close()
    return render_template('suppliers.html', suppliers=rows)

@app.route('/suppliers/edit/<int:item_id>', methods=['GET','POST'])
def edit_supplier(item_id):
    if not require('suppliers'):
        return redirect(url_for('dashboard'))
    c = db()
    item = c.execute('SELECT * FROM suppliers WHERE id=?', (item_id,)).fetchone()
    if not item:
        c.close()
        flash('Supplier not found', 'danger')
        return redirect(url_for('suppliers'))
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        address = request.form.get('address', '').strip()
        if not name:
            flash('Supplier name is required.', 'danger')
        else:
            c.execute('UPDATE suppliers SET name=?,phone=?,email=?,address=? WHERE id=?', (name, phone, email, address, item_id))
            c.commit()
            c.close()
            flash('Supplier updated successfully', 'success')
            return redirect(url_for('suppliers'))
    c.close()
    return render_template('edit.html', entity='Supplier', item=item, fields=[
        ('name','Supplier Name','text'),
        ('phone','Phone','text'),
        ('email','Email','email'),
        ('address','Address','text')
    ], back_url=url_for('suppliers'))

@app.route('/suppliers/delete/<int:item_id>', methods=['POST'])
def delete_supplier(item_id):
    if not require('suppliers'):
        return redirect(url_for('dashboard'))
    c = db()
    c.execute('UPDATE purchases SET supplier_id=NULL WHERE supplier_id=?', (item_id,))
    c.execute('DELETE FROM suppliers WHERE id=?', (item_id,))
    c.commit()
    c.close()
    flash('Supplier deleted successfully', 'success')
    return redirect(url_for('suppliers'))

@app.route('/sales', methods=['GET','POST'])
def sales():
    if not require('sales'):
        return redirect(url_for('dashboard'))
    c = db()
    products = c.execute('SELECT * FROM products ORDER BY name').fetchall()
    customers = c.execute('SELECT * FROM customers ORDER BY name').fetchall()
    if request.method == 'POST':
        try:
            product_id = request.form.get('product_id')
            if not product_id:
                raise ValueError('Please select a product.')
            product = c.execute('SELECT * FROM products WHERE id=?', (product_id,)).fetchone()
            if not product:
                raise ValueError('Selected product was not found.')
            qty = to_int(request.form.get('qty'), 0)
            if qty <= 0:
                raise ValueError('Sale quantity must be at least 1.')
            if product['stock'] < qty:
                raise ValueError(f'Insufficient stock. Only {product["stock"]} available for {product["name"]}.')

            customer_id = request.form.get('customer_id') or None
            payment_status = request.form.get('payment_status', 'Paid')
            payment_method = request.form.get('payment_method', 'UPI')
            total = round(qty * product['selling_price'], 2)
            inv = 'INV-' + datetime.now().strftime('%Y%m%d%H%M%S%f')[:18]

            cur = c.execute('INSERT INTO sales(customer_id,invoice_no,total,payment_status,payment_method,created_at) VALUES(?,?,?,?,?,?)',
                            (customer_id, inv, total, payment_status, payment_method, now()))
            c.execute('INSERT INTO sale_items(sale_id,product_id,qty,unit_price) VALUES(?,?,?,?)',
                      (cur.lastrowid, product['id'], qty, product['selling_price']))
            c.execute('UPDATE products SET stock=stock-? WHERE id=?', (qty, product['id']))
            c.commit()
            flash(f'Sale {inv} created successfully! Total: ₹{total:.2f}', 'success')
        except Exception as e:
            c.rollback()
            flash(str(e), 'danger')

    rows = c.execute('SELECT s.*, c.name customer FROM sales s LEFT JOIN customers c ON c.id=s.customer_id ORDER BY s.id DESC LIMIT 50').fetchall()
    c.close()
    return render_template('sales.html', sales=rows, products=products, customers=customers)

@app.route('/sales/edit/<int:item_id>', methods=['GET','POST'])
def edit_sale(item_id):
    if not require('sales'):
        return redirect(url_for('dashboard'))
    c = db()
    item = c.execute('SELECT * FROM sales WHERE id=?', (item_id,)).fetchone()
    if not item:
        c.close()
        flash('Sale not found', 'danger')
        return redirect(url_for('sales'))
    if request.method == 'POST':
        c.execute('UPDATE sales SET payment_status=?,payment_method=? WHERE id=?',
                  (request.form.get('payment_status', 'Paid'), request.form.get('payment_method', 'UPI'), item_id))
        c.commit()
        c.close()
        flash('Sale payment details updated successfully', 'success')
        return redirect(url_for('sales'))
    c.close()
    return render_template('edit.html', entity='Sale ' + item['invoice_no'], item=item, fields=[
        ('payment_status','Payment Status','select', ['Paid','Pending']),
        ('payment_method','Payment Method','select',['UPI','Cash','Card','Bank Transfer'])
    ], back_url=url_for('sales'))

@app.route('/sales/delete/<int:item_id>', methods=['POST'])
def delete_sale(item_id):
    if not require('sales'):
        return redirect(url_for('dashboard'))
    c = db()
    sale = c.execute('SELECT * FROM sales WHERE id=?', (item_id,)).fetchone()
    if not sale:
        c.close()
        flash('Sale not found', 'danger')
        return redirect(url_for('sales'))
    items = c.execute('SELECT * FROM sale_items WHERE sale_id=?', (item_id,)).fetchall()
    for it in items:
        c.execute('UPDATE products SET stock=stock+? WHERE id=?', (it['qty'], it['product_id']))
    c.execute('DELETE FROM sale_items WHERE sale_id=?', (item_id,))
    c.execute('DELETE FROM sales WHERE id=?', (item_id,))
    c.commit()
    c.close()
    flash('Sale deleted and inventory stock restored successfully', 'success')
    return redirect(url_for('sales'))

@app.route('/sales/<int:item_id>/invoice')
def invoice(item_id):
    if not require('sales'):
        return redirect(url_for('dashboard'))
    c = db()
    sale = c.execute('SELECT s.*, c.name customer,c.phone,c.email,c.address FROM sales s LEFT JOIN customers c ON c.id=s.customer_id WHERE s.id=?', (item_id,)).fetchone()
    if not sale:
        c.close()
        flash('Invoice not found', 'danger')
        return redirect(url_for('sales'))
    items = c.execute('SELECT si.*, COALESCE(p.name, "Discontinued Item") as name, COALESCE(p.sku, "-") as sku FROM sale_items si LEFT JOIN products p ON p.id=si.product_id WHERE si.sale_id=?', (item_id,)).fetchall()
    c.close()
    return render_template('invoice.html', sale=sale, items=items)

@app.route('/sales/<int:item_id>/invoice/pdf')
def invoice_pdf(item_id):
    if not require('sales'):
        return redirect(url_for('dashboard'))
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_RIGHT
    except ImportError:
        flash('PDF support is not installed. Please run: pip install reportlab', 'danger')
        return redirect(url_for('sales'))

    c = db()
    sale = c.execute('SELECT s.*, c.name customer,c.phone,c.email,c.address FROM sales s LEFT JOIN customers c ON c.id=s.customer_id WHERE s.id=?', (item_id,)).fetchone()
    if not sale:
        c.close()
        flash('Invoice not found', 'danger')
        return redirect(url_for('sales'))
    items = c.execute('SELECT si.*, COALESCE(p.name, "Item") as name, COALESCE(p.sku, "-") as sku FROM sale_items si LEFT JOIN products p ON p.id=si.product_id WHERE si.sale_id=?', (item_id,)).fetchall()
    c.close()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle('InvTitle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=22, leading=26, textColor=colors.HexColor('#172033'))
    sub_style = ParagraphStyle('InvSub', parent=styles['Normal'], fontName='Helvetica', fontSize=10, textColor=colors.HexColor('#64748b'), leading=14)
    norm = ParagraphStyle('InvNorm', parent=styles['Normal'], fontName='Helvetica', fontSize=10, leading=14)

    story = [
        Paragraph('SMARTBIZ ERP', title_style),
        Paragraph('Enterprise Business Management System', sub_style),
        Spacer(1, 15),
        Paragraph(f"<b>Invoice:</b> {sale['invoice_no']}", norm),
        Paragraph(f"<b>Date:</b> {sale['created_at']}", norm),
        Paragraph(f"<b>Customer:</b> {sale['customer'] or 'Walk-in Customer'}", norm),
    ]
    if sale['phone']:
        story.append(Paragraph(f"<b>Phone:</b> {sale['phone']}", norm))
    if sale['email']:
        story.append(Paragraph(f"<b>Email:</b> {sale['email']}", norm))
    story.append(Spacer(1, 15))

    data = [['SKU', 'Product', 'Qty', 'Unit Price', 'Amount']]
    for it in items:
        data.append([
            str(it['sku']),
            str(it['name']),
            str(it['qty']),
            f"Rs. {it['unit_price']:.2f}",
            f"Rs. {it['qty']*it['unit_price']:.2f}"
        ])
    data.append(['', '', '', 'Total', f"Rs. {sale['total']:.2f}"])

    table = Table(data, colWidths=[70, 200, 45, 90, 90])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#172033')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('ALIGN', (2,1), (-1,-1), 'RIGHT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTNAME', (-2,-1), (-1,-1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('FONTSIZE', (0,0), (-1,-1), 9)
    ]))

    story.extend([
        table,
        Spacer(1, 15),
        Paragraph(f"<b>Payment:</b> {sale['payment_status']} | <b>Method:</b> {sale['payment_method'] or 'UPI'}", norm),
        Spacer(1, 20),
        Paragraph('<i>Thank you for your business.</i>', sub_style)
    ])
    doc.build(story)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f"{sale['invoice_no']}.pdf", mimetype='application/pdf')

@app.route('/purchases', methods=['GET','POST'])
def purchases():
    if not require('purchases'):
        return redirect(url_for('dashboard'))
    c = db()
    products = c.execute('SELECT * FROM products ORDER BY name').fetchall()
    suppliers = c.execute('SELECT * FROM suppliers ORDER BY name').fetchall()
    if request.method == 'POST':
        try:
            product_id = request.form.get('product_id')
            if not product_id:
                raise ValueError('Please select a product.')
            p = c.execute('SELECT * FROM products WHERE id=?', (product_id,)).fetchone()
            if not p:
                raise ValueError('Selected product not found.')
            qty = to_int(request.form.get('qty'), 0)
            if qty <= 0:
                raise ValueError('Purchase quantity must be at least 1.')

            supplier_id = request.form.get('supplier_id') or None
            payment_status = request.form.get('payment_status', 'Pending')
            total = round(qty * p['purchase_price'], 2)
            po = 'PO-' + datetime.now().strftime('%Y%m%d%H%M%S%f')[:18]

            cur = c.execute('INSERT INTO purchases(supplier_id,po_no,total,payment_status,created_at) VALUES(?,?,?,?,?)',
                            (supplier_id, po, total, payment_status, now()))
            c.execute('INSERT INTO purchase_items(purchase_id,product_id,qty,unit_price) VALUES(?,?,?,?)',
                      (cur.lastrowid, p['id'], qty, p['purchase_price']))
            c.execute('UPDATE products SET stock=stock+? WHERE id=?', (qty, p['id']))
            c.commit()
            flash(f'Purchase order {po} received and stock updated successfully', 'success')
        except Exception as e:
            c.rollback()
            flash(str(e), 'danger')

    rows = c.execute('SELECT p.*, s.name supplier FROM purchases p LEFT JOIN suppliers s ON s.id=p.supplier_id ORDER BY p.id DESC LIMIT 50').fetchall()
    c.close()
    return render_template('purchases.html', purchases=rows, products=products, suppliers=suppliers)

@app.route('/purchases/edit/<int:item_id>', methods=['GET','POST'])
def edit_purchase(item_id):
    if not require('purchases'):
        return redirect(url_for('dashboard'))
    c = db()
    item = c.execute('SELECT * FROM purchases WHERE id=?', (item_id,)).fetchone()
    if not item:
        c.close()
        flash('Purchase not found', 'danger')
        return redirect(url_for('purchases'))
    if request.method == 'POST':
        c.execute('UPDATE purchases SET payment_status=? WHERE id=?',
                  (request.form.get('payment_status', 'Pending'), item_id))
        c.commit()
        c.close()
        flash('Purchase payment status updated successfully', 'success')
        return redirect(url_for('purchases'))
    c.close()
    return render_template('edit.html', entity='Purchase ' + item['po_no'], item=item, fields=[
        ('payment_status','Payment Status','select',['Pending','Paid'])
    ], back_url=url_for('purchases'))

@app.route('/purchases/delete/<int:item_id>', methods=['POST'])
def delete_purchase(item_id):
    if not require('purchases'):
        return redirect(url_for('dashboard'))
    c = db()
    purchase = c.execute('SELECT * FROM purchases WHERE id=?', (item_id,)).fetchone()
    if not purchase:
        c.close()
        flash('Purchase not found', 'danger')
        return redirect(url_for('purchases'))
    items = c.execute('SELECT * FROM purchase_items WHERE purchase_id=?', (item_id,)).fetchall()
    for it in items:
        c.execute('UPDATE products SET stock=MAX(0,stock-?) WHERE id=?', (it['qty'], it['product_id']))
    c.execute('DELETE FROM purchase_items WHERE purchase_id=?', (item_id,))
    c.execute('DELETE FROM purchases WHERE id=?', (item_id,))
    c.commit()
    c.close()
    flash('Purchase deleted and received stock reversed successfully', 'success')
    return redirect(url_for('purchases'))

@app.route('/expenses', methods=['GET','POST'])
def expenses():
    if not require('expenses'):
        return redirect(url_for('dashboard'))
    c = db()
    if request.method == 'POST':
        category = request.form.get('category', 'Other').strip()
        description = request.form.get('description', '').strip()
        amount = to_float(request.form.get('amount'), 0.0)
        payment_method = request.form.get('payment_method', 'UPI')
        if amount <= 0:
            flash('Expense amount must be greater than zero.', 'danger')
        else:
            c.execute('INSERT INTO expenses(category,description,amount,payment_method,created_at) VALUES(?,?,?,?,?)',
                      (category, description, amount, payment_method, now()))
            c.commit()
            flash('Expense recorded successfully', 'success')

    rows = c.execute('SELECT * FROM expenses ORDER BY id DESC').fetchall()
    total = c.execute('SELECT COALESCE(SUM(amount),0) v FROM expenses').fetchone()['v']
    bycat = c.execute('SELECT category,SUM(amount) total FROM expenses GROUP BY category ORDER BY total DESC').fetchall()
    c.close()
    return render_template('expenses.html', expenses=rows, total=total, bycat=bycat)

@app.route('/expenses/edit/<int:item_id>', methods=['GET','POST'])
def edit_expense(item_id):
    if not require('expenses'):
        return redirect(url_for('dashboard'))
    c = db()
    item = c.execute('SELECT * FROM expenses WHERE id=?', (item_id,)).fetchone()
    if not item:
        c.close()
        flash('Expense not found', 'danger')
        return redirect(url_for('expenses'))
    if request.method == 'POST':
        category = request.form.get('category', 'Other').strip()
        description = request.form.get('description', '').strip()
        amount = to_float(request.form.get('amount'), 0.0)
        payment_method = request.form.get('payment_method', 'UPI')
        if amount <= 0:
            flash('Expense amount must be greater than zero.', 'danger')
        else:
            c.execute('UPDATE expenses SET category=?,description=?,amount=?,payment_method=? WHERE id=?',
                      (category, description, amount, payment_method, item_id))
            c.commit()
            c.close()
            flash('Expense updated successfully', 'success')
            return redirect(url_for('expenses'))
    c.close()
    return render_template('edit.html', entity='Expense', item=item, fields=[
        ('category','Category','text'),
        ('description','Description','text'),
        ('amount','Amount','number'),
        ('payment_method','Payment Method','select',['UPI','Cash','Card','Bank Transfer'])
    ], back_url=url_for('expenses'))

@app.route('/expenses/delete/<int:item_id>', methods=['POST'])
def delete_expense(item_id):
    if not require('expenses'):
        return redirect(url_for('dashboard'))
    c = db()
    c.execute('DELETE FROM expenses WHERE id=?', (item_id,))
    c.commit()
    c.close()
    flash('Expense deleted successfully', 'success')
    return redirect(url_for('expenses'))

@app.route('/finance')
def finance():
    if not require('finance'):
        return redirect(url_for('dashboard'))
    c = db()
    revenue = c.execute('SELECT COALESCE(SUM(total),0) v FROM sales').fetchone()['v']
    expenses = c.execute('SELECT COALESCE(SUM(amount),0) v FROM expenses').fetchone()['v']
    purchases = c.execute('SELECT COALESCE(SUM(total),0) v FROM purchases').fetchone()['v']
    receivable = c.execute("SELECT COALESCE(SUM(total),0) v FROM sales WHERE payment_status!='Paid'").fetchone()['v']
    payable = c.execute("SELECT COALESCE(SUM(total),0) v FROM purchases WHERE payment_status!='Paid'").fetchone()['v']
    c.close()
    return render_template('finance.html', revenue=revenue, expenses=expenses, purchases=purchases, profit=revenue-expenses, receivable=receivable, payable=payable)

@app.route('/inventory')
def inventory():
    if not require('inventory'):
        return redirect(url_for('dashboard'))
    c = db()
    rows = c.execute('SELECT * FROM products ORDER BY stock ASC').fetchall()
    total_valuation = c.execute('SELECT COALESCE(SUM(stock * purchase_price), 0) val, COALESCE(SUM(stock), 0) items FROM products').fetchone()
    c.close()
    return render_template('inventory.html', products=rows, valuation=total_valuation['val'], total_units=total_valuation['items'])

@app.route('/employees', methods=['GET','POST'])
def employees():
    if not require('employees'):
        return redirect(url_for('dashboard'))
    c = db()
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        department = request.form.get('department', '').strip()
        job_role = request.form.get('job_role', '').strip()
        salary = to_float(request.form.get('salary'), 0.0)
        status = request.form.get('status', 'Active')
        if not name:
            flash('Employee name is required.', 'danger')
        else:
            c.execute('INSERT INTO employees(name,department,job_role,salary,status,created_at) VALUES(?,?,?,?,?,?)',
                      (name, department, job_role, salary, status, now()))
            c.commit()
            flash('Employee added successfully', 'success')
    rows = c.execute('SELECT * FROM employees ORDER BY id DESC').fetchall()
    c.close()
    return render_template('employees.html', employees=rows)

@app.route('/employees/edit/<int:item_id>', methods=['GET','POST'])
def edit_employee(item_id):
    if not require('employees'):
        return redirect(url_for('dashboard'))
    c = db()
    item = c.execute('SELECT * FROM employees WHERE id=?', (item_id,)).fetchone()
    if not item:
        c.close()
        flash('Employee not found', 'danger')
        return redirect(url_for('employees'))
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        department = request.form.get('department', '').strip()
        job_role = request.form.get('job_role', '').strip()
        salary = to_float(request.form.get('salary'), 0.0)
        status = request.form.get('status', 'Active')
        if not name:
            flash('Employee name is required.', 'danger')
        else:
            c.execute('UPDATE employees SET name=?,department=?,job_role=?,salary=?,status=? WHERE id=?',
                      (name, department, job_role, salary, status, item_id))
            c.commit()
            c.close()
            flash('Employee updated successfully', 'success')
            return redirect(url_for('employees'))
    c.close()
    return render_template('edit.html', entity='Employee', item=item, fields=[
        ('name','Name','text'),
        ('department','Department','text'),
        ('job_role','Job Role','text'),
        ('salary','Salary','number'),
        ('status','Status','select',['Active','Inactive'])
    ], back_url=url_for('employees'))

@app.route('/employees/delete/<int:item_id>', methods=['POST'])
def delete_employee(item_id):
    if not require('employees'):
        return redirect(url_for('dashboard'))
    c = db()
    c.execute('DELETE FROM employees WHERE id=?', (item_id,))
    c.commit()
    c.close()
    flash('Employee deleted successfully', 'success')
    return redirect(url_for('employees'))

@app.route('/users', methods=['GET','POST'])
def users():
    if not require('users'):
        return redirect(url_for('dashboard'))
    c = db()
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        role = request.form.get('role', 'Sales Staff')
        if not name or not email or not password:
            flash('Name, email, and password are required.', 'danger')
        elif role not in ROLES:
            flash('Invalid role selected.', 'danger')
        else:
            try:
                c.execute('INSERT INTO users(name,email,password,role,created_at) VALUES(?,?,?,?,?)',
                          (name, email, generate_password_hash(password), role, now()))
                c.commit()
                flash('User created successfully', 'success')
            except sqlite3.IntegrityError:
                flash(f'User with email "{email}" already exists.', 'danger')
    rows = c.execute('SELECT id,name,email,role,created_at FROM users ORDER BY id DESC').fetchall()
    c.close()
    return render_template('users.html', users=rows, roles=list(ROLES))

@app.route('/users/edit/<int:item_id>', methods=['GET','POST'])
def edit_user(item_id):
    if not require('users'):
        return redirect(url_for('dashboard'))
    c = db()
    item = c.execute('SELECT id,name,email,role,created_at FROM users WHERE id=?', (item_id,)).fetchone()
    if not item:
        c.close()
        flash('User not found', 'danger')
        return redirect(url_for('users'))
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        role = request.form.get('role', item['role'])
        password = request.form.get('password', '').strip()

        if not name or not email:
            flash('Name and email are required.', 'danger')
        elif role not in ROLES:
            flash('Invalid role selected.', 'danger')
        else:
            # Check if attempting to demote last Super Admin
            if item['role'] == 'Super Admin' and role != 'Super Admin':
                admin_count = c.execute("SELECT COUNT(*) n FROM users WHERE role='Super Admin'").fetchone()['n']
                if admin_count <= 1:
                    c.close()
                    flash('Cannot change the role of the only remaining Super Admin.', 'danger')
                    return redirect(url_for('users'))

            try:
                c.execute('UPDATE users SET name=?,email=?,role=? WHERE id=?', (name, email, role, item_id))
                if password:
                    c.execute('UPDATE users SET password=? WHERE id=?', (generate_password_hash(password), item_id))
                c.commit()
                # Update current session if user modified their own profile
                if item_id == session.get('user_id'):
                    session['name'] = name
                    session['email'] = email
                    session['role'] = role
                c.close()
                flash('User updated successfully', 'success')
                return redirect(url_for('users'))
            except sqlite3.IntegrityError:
                flash(f'Email "{email}" is already in use by another account.', 'danger')
    c.close()
    return render_template('edit.html', entity='User', item=item, fields=[
        ('name','Name','text'),
        ('email','Email','email'),
        ('role','Role','select',list(ROLES)),
        ('password','New Password (leave blank to keep current)','password')
    ], back_url=url_for('users'))

@app.route('/users/delete/<int:item_id>', methods=['POST'])
def delete_user(item_id):
    if not require('users'):
        return redirect(url_for('dashboard'))
    if item_id == session.get('user_id'):
        flash('You cannot delete your own logged-in account.', 'danger')
        return redirect(url_for('users'))
    c = db()
    target = c.execute('SELECT role FROM users WHERE id=?', (item_id,)).fetchone()
    if target and target['role'] == 'Super Admin':
        admin_count = c.execute("SELECT COUNT(*) n FROM users WHERE role='Super Admin'").fetchone()['n']
        if admin_count <= 1:
            c.close()
            flash('Cannot delete the only remaining Super Admin account.', 'danger')
            return redirect(url_for('users'))
    c.execute('DELETE FROM users WHERE id=?', (item_id,))
    c.commit()
    c.close()
    flash('User deleted successfully', 'success')
    return redirect(url_for('users'))

@app.route('/reports')
def reports():
    if not require('reports'):
        return redirect(url_for('dashboard'))
    c = db()
    sales = c.execute('SELECT COUNT(*) count, COALESCE(SUM(total),0) total FROM sales').fetchone()
    expenses = c.execute('SELECT COUNT(*) count, COALESCE(SUM(amount),0) total FROM expenses').fetchone()
    purchases = c.execute('SELECT COUNT(*) count, COALESCE(SUM(total),0) total FROM purchases').fetchone()
    products = c.execute('SELECT COUNT(*) count, COALESCE(SUM(stock * purchase_price),0) val FROM products').fetchone()
    low = c.execute('SELECT COUNT(*) count FROM products WHERE stock<=min_stock').fetchone()

    monthly_sales = {r['m']: r['total'] for r in c.execute("SELECT substr(created_at,1,7) m, SUM(total) total FROM sales GROUP BY m").fetchall()}
    monthly_expenses = {r['m']: r['total'] for r in c.execute("SELECT substr(created_at,1,7) m, SUM(amount) total FROM expenses GROUP BY m").fetchall()}
    all_months = sorted(list(set(list(monthly_sales.keys()) + list(monthly_expenses.keys()))), reverse=True)[:6]
    monthly_breakdown = []
    for m in all_months:
        s_tot = monthly_sales.get(m, 0.0)
        e_tot = monthly_expenses.get(m, 0.0)
        monthly_breakdown.append({
            'month': m,
            'sales': s_tot,
            'expenses': e_tot,
            'profit': s_tot - e_tot
        })

    top_products = c.execute("""
        SELECT COALESCE(p.name, 'Unknown Item') name, COALESCE(p.sku, '-') sku, SUM(si.qty) total_qty, SUM(si.qty * si.unit_price) total_revenue
        FROM sale_items si
        LEFT JOIN products p ON p.id = si.product_id
        GROUP BY si.product_id
        ORDER BY total_qty DESC
        LIMIT 5
    """).fetchall()

    expense_categories = c.execute("""
        SELECT category, COUNT(*) count, SUM(amount) total
        FROM expenses
        GROUP BY category
        ORDER BY total DESC
    """).fetchall()
    c.close()

    return render_template('reports.html',
        sales=sales,
        expenses=expenses,
        purchases=purchases,
        products=products,
        low=low,
        monthly_breakdown=monthly_breakdown,
        top_products=top_products,
        expense_categories=expense_categories
    )

@app.route('/api/forecast')
def forecast():
    if not logged_in():
        return jsonify({'error':'unauthorized'}), 401
    c = db()
    rows = c.execute("SELECT substr(created_at,1,10) d, SUM(total) total FROM sales GROUP BY d ORDER BY d").fetchall()
    total_sales_count = c.execute("SELECT COUNT(*) n FROM sales").fetchone()['n']
    c.close()

    if total_sales_count == 0 or len(rows) == 0:
        return jsonify({
            'status': 'empty',
            'message': 'No sales records found. Record your first sale to activate forecasting.'
        })

    if len(rows) == 1:
        day_total = rows[0]['total']
        return jsonify({
            'status': 'ok',
            'days_analyzed': 1,
            'recent_average': round(day_total, 2),
            'next_period_forecast': round(day_total * 1.05, 2),
            'growth_rate': '+5.0%',
            'method': 'Baseline Day Projection (+5% growth trajectory)',
            'note': 'Record sales on multiple days to enable multi-period moving average and trend detection.'
        })

    vals = [r['total'] for r in rows]
    window = min(7, len(vals))
    avg = sum(vals[-window:]) / window
    growth_factor = 1.05 if vals[-1] >= vals[0] else 0.98
    forecast_val = round(avg * growth_factor, 2)
    growth_pct = f"{round((growth_factor - 1.0) * 100, 1):+}%"

    return jsonify({
        'status': 'ok',
        'days_analyzed': len(rows),
        'recent_average': round(avg, 2),
        'next_period_forecast': forecast_val,
        'growth_rate': growth_pct,
        'method': f'{window}-day moving average with trend trajectory',
        'note': 'Production ML ready: can be connected to Prophet, ARIMA, or XGBoost algorithms.'
    })

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
