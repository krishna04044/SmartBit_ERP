from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_file
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3, os, io
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'change-this-in-production')
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

def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
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

def logged_in(): return 'user_id' in session

def can(module): return logged_in() and module in ROLES.get(session.get('role'), [])

@app.context_processor
def inject():
    return {'session_user': session, 'can': can}

def require(module):
    if not can(module):
        flash('You do not have permission for this module.','danger')
        return False
    return True

@app.route('/')
def index(): return redirect(url_for('dashboard' if logged_in() else 'login'))

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email=request.form['email'].strip().lower(); password=request.form['password']
        c=db(); u=c.execute('SELECT * FROM users WHERE email=?',(email,)).fetchone(); c.close()
        if u and check_password_hash(u['password'],password):
            session.update(user_id=u['id'], name=u['name'], role=u['role'], email=u['email']); return redirect(url_for('dashboard'))
        flash('Invalid email or password','danger')
    return render_template('login.html')

@app.route('/logout')
def logout(): session.clear(); return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if not require('dashboard'): return redirect(url_for('login'))
    c=db()
    revenue=c.execute("SELECT COALESCE(SUM(total),0) v FROM sales").fetchone()['v']
    expenses=c.execute("SELECT COALESCE(SUM(amount),0) v FROM expenses").fetchone()['v']
    purchases=c.execute("SELECT COALESCE(SUM(total),0) v FROM purchases").fetchone()['v']
    customers=c.execute('SELECT COUNT(*) v FROM customers').fetchone()['v']
    orders=c.execute('SELECT COUNT(*) v FROM sales').fetchone()['v']
    low=c.execute('SELECT * FROM products WHERE stock <= min_stock ORDER BY stock ASC').fetchall()
    recent=c.execute('SELECT s.*, c.name customer FROM sales s LEFT JOIN customers c ON c.id=s.customer_id ORDER BY s.id DESC LIMIT 8').fetchall()
    monthly=c.execute("SELECT substr(created_at,1,7) month, SUM(total) total FROM sales GROUP BY month ORDER BY month DESC LIMIT 6").fetchall()
    c.close()
    return render_template('dashboard.html', revenue=revenue, expenses=expenses, purchases=purchases, profit=revenue-expenses, customers=customers, orders=orders, low=low, recent=recent, monthly=list(reversed(monthly)))

@app.route('/products', methods=['GET','POST'])
def products():
    if not require('products'): return redirect(url_for('dashboard'))
    c=db()
    if request.method=='POST':
        try:
            c.execute('INSERT INTO products(sku,name,category,purchase_price,selling_price,stock,min_stock,warehouse,created_at) VALUES(?,?,?,?,?,?,?,?,?)', (request.form['sku'].strip(),request.form['name'].strip(),request.form.get('category',''),float(request.form.get('purchase_price',0)),float(request.form.get('selling_price',0)),int(request.form.get('stock',0)),int(request.form.get('min_stock',0)),request.form.get('warehouse','Main Warehouse'),now())); c.commit(); flash('Product added','success')
        except sqlite3.IntegrityError: flash('SKU already exists','danger')
    rows=c.execute('SELECT * FROM products ORDER BY id DESC').fetchall(); c.close(); return render_template('products.html', products=rows)

@app.route('/products/edit/<int:item_id>', methods=['GET','POST'])
def edit_product(item_id):
    if not require('products'): return redirect(url_for('dashboard'))
    c=db(); item=c.execute('SELECT * FROM products WHERE id=?',(item_id,)).fetchone()
    if not item: c.close(); flash('Product not found','danger'); return redirect(url_for('products'))
    if request.method=='POST':
        try:
            c.execute('UPDATE products SET sku=?,name=?,category=?,purchase_price=?,selling_price=?,stock=?,min_stock=?,warehouse=? WHERE id=?',(request.form['sku'].strip(),request.form['name'].strip(),request.form.get('category',''),float(request.form.get('purchase_price',0)),float(request.form.get('selling_price',0)),int(request.form.get('stock',0)),int(request.form.get('min_stock',0)),request.form.get('warehouse','Main Warehouse'),item_id)); c.commit(); c.close(); flash('Product updated','success'); return redirect(url_for('products'))
        except sqlite3.IntegrityError: flash('SKU already exists','danger')
    c.close(); return render_template('edit.html', entity='Product', item=item, fields=[('sku','SKU','text'),('name','Product Name','text'),('category','Category','text'),('purchase_price','Purchase Price','number'),('selling_price','Selling Price','number'),('stock','Stock','number'),('min_stock','Minimum Stock','number'),('warehouse','Warehouse','text')], back_url=url_for('products'))

@app.route('/products/delete/<int:item_id>', methods=['POST'])
def delete_product(item_id):
    if not require('products'): return redirect(url_for('dashboard'))
    c=db(); c.execute('DELETE FROM products WHERE id=?',(item_id,)); c.commit(); c.close(); flash('Product deleted','success'); return redirect(url_for('products'))

@app.route('/customers', methods=['GET','POST'])
def customers():
    if not require('customers'): return redirect(url_for('dashboard'))
    c=db()
    if request.method=='POST':
        c.execute('INSERT INTO customers(name,phone,email,address,created_at) VALUES(?,?,?,?,?)',(request.form['name'],request.form.get('phone'),request.form.get('email'),request.form.get('address'),now())); c.commit(); flash('Customer added','success')
    rows=c.execute('SELECT * FROM customers ORDER BY id DESC').fetchall(); c.close(); return render_template('customers.html', customers=rows)

@app.route('/customers/edit/<int:item_id>', methods=['GET','POST'])
def edit_customer(item_id):
    if not require('customers'): return redirect(url_for('dashboard'))
    c=db(); item=c.execute('SELECT * FROM customers WHERE id=?',(item_id,)).fetchone()
    if not item: c.close(); flash('Customer not found','danger'); return redirect(url_for('customers'))
    if request.method=='POST':
        c.execute('UPDATE customers SET name=?,phone=?,email=?,address=? WHERE id=?',(request.form['name'],request.form.get('phone'),request.form.get('email'),request.form.get('address'),item_id)); c.commit(); c.close(); flash('Customer updated','success'); return redirect(url_for('customers'))
    c.close(); return render_template('edit.html', entity='Customer', item=item, fields=[('name','Name','text'),('phone','Phone','text'),('email','Email','email'),('address','Address','text')], back_url=url_for('customers'))

@app.route('/customers/delete/<int:item_id>', methods=['POST'])
def delete_customer(item_id):
    if not require('customers'): return redirect(url_for('dashboard'))
    c=db(); c.execute('UPDATE sales SET customer_id=NULL WHERE customer_id=?',(item_id,)); c.execute('DELETE FROM customers WHERE id=?',(item_id,)); c.commit(); c.close(); flash('Customer deleted','success'); return redirect(url_for('customers'))

@app.route('/suppliers', methods=['GET','POST'])
def suppliers():
    if not require('suppliers'): return redirect(url_for('dashboard'))
    c=db()
    if request.method=='POST':
        c.execute('INSERT INTO suppliers(name,phone,email,address,created_at) VALUES(?,?,?,?,?)',(request.form['name'],request.form.get('phone'),request.form.get('email'),request.form.get('address'),now())); c.commit(); flash('Supplier added','success')
    rows=c.execute('SELECT * FROM suppliers ORDER BY id DESC').fetchall(); c.close(); return render_template('suppliers.html', suppliers=rows)

@app.route('/suppliers/edit/<int:item_id>', methods=['GET','POST'])
def edit_supplier(item_id):
    if not require('suppliers'): return redirect(url_for('dashboard'))
    c=db(); item=c.execute('SELECT * FROM suppliers WHERE id=?',(item_id,)).fetchone()
    if not item: c.close(); flash('Supplier not found','danger'); return redirect(url_for('suppliers'))
    if request.method=='POST':
        c.execute('UPDATE suppliers SET name=?,phone=?,email=?,address=? WHERE id=?',(request.form['name'],request.form.get('phone'),request.form.get('email'),request.form.get('address'),item_id)); c.commit(); c.close(); flash('Supplier updated','success'); return redirect(url_for('suppliers'))
    c.close(); return render_template('edit.html', entity='Supplier', item=item, fields=[('name','Supplier Name','text'),('phone','Phone','text'),('email','Email','email'),('address','Address','text')], back_url=url_for('suppliers'))

@app.route('/suppliers/delete/<int:item_id>', methods=['POST'])
def delete_supplier(item_id):
    if not require('suppliers'): return redirect(url_for('dashboard'))
    c=db(); c.execute('UPDATE purchases SET supplier_id=NULL WHERE supplier_id=?',(item_id,)); c.execute('DELETE FROM suppliers WHERE id=?',(item_id,)); c.commit(); c.close(); flash('Supplier deleted','success'); return redirect(url_for('suppliers'))

@app.route('/sales', methods=['GET','POST'])
def sales():
    if not require('sales'): return redirect(url_for('dashboard'))
    c=db(); products=c.execute('SELECT * FROM products ORDER BY name').fetchall(); customers=c.execute('SELECT * FROM customers ORDER BY name').fetchall()
    if request.method=='POST':
        try:
            product=c.execute('SELECT * FROM products WHERE id=?',(request.form['product_id'],)).fetchone(); qty=int(request.form['qty']); customer_id=request.form.get('customer_id') or None
            if not product or qty<=0 or product['stock']<qty: raise ValueError('Insufficient stock')
            total=qty*product['selling_price']; inv='INV-'+datetime.now().strftime('%Y%m%d%H%M%S%f')
            cur=c.execute('INSERT INTO sales(customer_id,invoice_no,total,payment_status,payment_method,created_at) VALUES(?,?,?,?,?,?)',(customer_id,inv,total,request.form.get('payment_status','Paid'),request.form.get('payment_method','UPI'),now()))
            c.execute('INSERT INTO sale_items(sale_id,product_id,qty,unit_price) VALUES(?,?,?,?)',(cur.lastrowid,product['id'],qty,product['selling_price']))
            c.execute('UPDATE products SET stock=stock-? WHERE id=?',(qty,product['id'])); c.commit(); flash(f'Sale {inv} created. Invoice is ready to download.','success')
        except Exception as e: c.rollback(); flash(str(e),'danger')
    rows=c.execute('SELECT s.*, c.name customer FROM sales s LEFT JOIN customers c ON c.id=s.customer_id ORDER BY s.id DESC LIMIT 50').fetchall(); c.close(); return render_template('sales.html', sales=rows, products=products, customers=customers)

@app.route('/sales/edit/<int:item_id>', methods=['GET','POST'])
def edit_sale(item_id):
    if not require('sales'): return redirect(url_for('dashboard'))
    c=db(); item=c.execute('SELECT * FROM sales WHERE id=?',(item_id,)).fetchone()
    if not item: c.close(); flash('Sale not found','danger'); return redirect(url_for('sales'))
    if request.method=='POST':
        c.execute('UPDATE sales SET payment_status=?,payment_method=? WHERE id=?',(request.form['payment_status'],request.form['payment_method'],item_id)); c.commit(); c.close(); flash('Sale payment details updated','success'); return redirect(url_for('sales'))
    c.close(); return render_template('edit.html', entity='Sale '+item['invoice_no'], item=item, fields=[('payment_status','Payment Status','select', ['Paid','Pending']),('payment_method','Payment Method','select',['UPI','Cash','Card','Bank Transfer'])], back_url=url_for('sales'))

@app.route('/sales/delete/<int:item_id>', methods=['POST'])
def delete_sale(item_id):
    if not require('sales'): return redirect(url_for('dashboard'))
    c=db(); sale=c.execute('SELECT * FROM sales WHERE id=?',(item_id,)).fetchone()
    if not sale: c.close(); flash('Sale not found','danger'); return redirect(url_for('sales'))
    items=c.execute('SELECT * FROM sale_items WHERE sale_id=?',(item_id,)).fetchall()
    for it in items: c.execute('UPDATE products SET stock=stock+? WHERE id=?',(it['qty'],it['product_id']))
    c.execute('DELETE FROM sale_items WHERE sale_id=?',(item_id,)); c.execute('DELETE FROM sales WHERE id=?',(item_id,)); c.commit(); c.close(); flash('Sale deleted and stock restored','success'); return redirect(url_for('sales'))

@app.route('/sales/<int:item_id>/invoice')
def invoice(item_id):
    if not require('sales'): return redirect(url_for('dashboard'))
    c=db(); sale=c.execute('SELECT s.*, c.name customer,c.phone,c.email,c.address FROM sales s LEFT JOIN customers c ON c.id=s.customer_id WHERE s.id=?',(item_id,)).fetchone();
    if not sale: c.close(); flash('Invoice not found','danger'); return redirect(url_for('sales'))
    items=c.execute('SELECT si.*,p.name,p.sku FROM sale_items si JOIN products p ON p.id=si.product_id WHERE si.sale_id=?',(item_id,)).fetchall(); c.close()
    return render_template('invoice.html', sale=sale, items=items)

@app.route('/sales/<int:item_id>/invoice/pdf')
def invoice_pdf(item_id):
    if not require('sales'): return redirect(url_for('dashboard'))
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.enums import TA_RIGHT
    except ImportError:
        flash('PDF support is not installed. Run: pip install -r requirements.txt','danger'); return redirect(url_for('sales'))
    c=db(); sale=c.execute('SELECT s.*, c.name customer,c.phone,c.email,c.address FROM sales s LEFT JOIN customers c ON c.id=s.customer_id WHERE s.id=?',(item_id,)).fetchone(); items=c.execute('SELECT si.*,p.name,p.sku FROM sale_items si JOIN products p ON p.id=si.product_id WHERE si.sale_id=?',(item_id,)).fetchall(); c.close()
    if not sale: flash('Invoice not found','danger'); return redirect(url_for('sales'))
    buffer=io.BytesIO(); doc=SimpleDocTemplate(buffer,pagesize=A4,rightMargin=40,leftMargin=40,topMargin=40,bottomMargin=40); styles=getSampleStyleSheet(); right=styles['Normal'].clone('right'); right.alignment=TA_RIGHT
    story=[Paragraph('SMARTBIZ ERP',styles['Title']),Paragraph('Sales Invoice',styles['Heading2']),Spacer(1,10),Paragraph(f"Invoice: {sale['invoice_no']}",styles['Normal']),Paragraph(f"Date: {sale['created_at']}",styles['Normal']),Paragraph(f"Customer: {sale['customer'] or 'Walk-in Customer'}",styles['Normal']),Spacer(1,15)]
    data=[['SKU','Product','Qty','Unit Price','Amount']]
    for it in items: data.append([it['sku'],it['name'],str(it['qty']),f"₹{it['unit_price']:.2f}",f"₹{it['qty']*it['unit_price']:.2f}"])
    data.append(['','','','Total',f"₹{sale['total']:.2f}"])
    table=Table(data,colWidths=[65,190,45,80,80]); table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#172033')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('GRID',(0,0),(-1,-1),0.5,colors.grey),('ALIGN',(2,1),(-1,-1),'RIGHT'),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTNAME',(-2,-1),(-1,-1),'Helvetica-Bold'),('BOTTOMPADDING',(0,0),(-1,0),8),('TOPPADDING',(0,0),(-1,0),8)])); story += [table,Spacer(1,15),Paragraph(f"Payment: {sale['payment_status']} | Method: {sale['payment_method'] or '-'}",styles['Normal']),Spacer(1,25),Paragraph('Thank you for your business.',styles['Normal'])]; doc.build(story); buffer.seek(0)
    return send_file(buffer,as_attachment=True,download_name=f"{sale['invoice_no']}.pdf",mimetype='application/pdf')

@app.route('/purchases', methods=['GET','POST'])
def purchases():
    if not require('purchases'): return redirect(url_for('dashboard'))
    c=db(); products=c.execute('SELECT * FROM products ORDER BY name').fetchall(); suppliers=c.execute('SELECT * FROM suppliers ORDER BY name').fetchall()
    if request.method=='POST':
        try:
            p=c.execute('SELECT * FROM products WHERE id=?',(request.form['product_id'],)).fetchone(); qty=int(request.form['qty']); supplier_id=request.form.get('supplier_id') or None
            if not p or qty<=0: raise ValueError('Invalid product or quantity')
            total=qty*p['purchase_price']; po='PO-'+datetime.now().strftime('%Y%m%d%H%M%S%f')
            cur=c.execute('INSERT INTO purchases(supplier_id,po_no,total,payment_status,created_at) VALUES(?,?,?,?,?)',(supplier_id,po,total,request.form.get('payment_status','Pending'),now()))
            c.execute('INSERT INTO purchase_items(purchase_id,product_id,qty,unit_price) VALUES(?,?,?,?)',(cur.lastrowid,p['id'],qty,p['purchase_price']))
            c.execute('UPDATE products SET stock=stock+? WHERE id=?',(qty,p['id'])); c.commit(); flash(f'Purchase {po} received and stock updated','success')
        except Exception as e: c.rollback(); flash(str(e),'danger')
    rows=c.execute('SELECT p.*, s.name supplier FROM purchases p LEFT JOIN suppliers s ON s.id=p.supplier_id ORDER BY p.id DESC LIMIT 50').fetchall(); c.close(); return render_template('purchases.html', purchases=rows, products=products, suppliers=suppliers)

@app.route('/purchases/edit/<int:item_id>', methods=['GET','POST'])
def edit_purchase(item_id):
    if not require('purchases'): return redirect(url_for('dashboard'))
    c=db(); item=c.execute('SELECT * FROM purchases WHERE id=?',(item_id,)).fetchone()
    if not item: c.close(); flash('Purchase not found','danger'); return redirect(url_for('purchases'))
    if request.method=='POST':
        c.execute('UPDATE purchases SET payment_status=? WHERE id=?',(request.form['payment_status'],item_id)); c.commit(); c.close(); flash('Purchase payment status updated','success'); return redirect(url_for('purchases'))
    c.close(); return render_template('edit.html', entity='Purchase '+item['po_no'], item=item, fields=[('payment_status','Payment Status','select',['Pending','Paid'])], back_url=url_for('purchases'))

@app.route('/purchases/delete/<int:item_id>', methods=['POST'])
def delete_purchase(item_id):
    if not require('purchases'): return redirect(url_for('dashboard'))
    c=db(); purchase=c.execute('SELECT * FROM purchases WHERE id=?',(item_id,)).fetchone()
    if not purchase: c.close(); flash('Purchase not found','danger'); return redirect(url_for('purchases'))
    items=c.execute('SELECT * FROM purchase_items WHERE purchase_id=?',(item_id,)).fetchall()
    for it in items: c.execute('UPDATE products SET stock=MAX(0,stock-?) WHERE id=?',(it['qty'],it['product_id']))
    c.execute('DELETE FROM purchase_items WHERE purchase_id=?',(item_id,)); c.execute('DELETE FROM purchases WHERE id=?',(item_id,)); c.commit(); c.close(); flash('Purchase deleted and received stock reversed','success'); return redirect(url_for('purchases'))

@app.route('/expenses', methods=['GET','POST'])
def expenses():
    if not require('expenses'): return redirect(url_for('dashboard'))
    c=db()
    if request.method=='POST':
        c.execute('INSERT INTO expenses(category,description,amount,payment_method,created_at) VALUES(?,?,?,?,?)',(request.form['category'],request.form.get('description'),float(request.form['amount']),request.form.get('payment_method','UPI'),now())); c.commit(); flash('Expense recorded','success')
    rows=c.execute('SELECT * FROM expenses ORDER BY id DESC').fetchall(); total=c.execute('SELECT COALESCE(SUM(amount),0) v FROM expenses').fetchone()['v']; bycat=c.execute('SELECT category,SUM(amount) total FROM expenses GROUP BY category ORDER BY total DESC').fetchall(); c.close(); return render_template('expenses.html', expenses=rows,total=total,bycat=bycat)

@app.route('/expenses/edit/<int:item_id>', methods=['GET','POST'])
def edit_expense(item_id):
    if not require('expenses'): return redirect(url_for('dashboard'))
    c=db(); item=c.execute('SELECT * FROM expenses WHERE id=?',(item_id,)).fetchone()
    if not item: c.close(); flash('Expense not found','danger'); return redirect(url_for('expenses'))
    if request.method=='POST':
        c.execute('UPDATE expenses SET category=?,description=?,amount=?,payment_method=? WHERE id=?',(request.form['category'],request.form.get('description'),float(request.form['amount']),request.form.get('payment_method'),item_id)); c.commit(); c.close(); flash('Expense updated','success'); return redirect(url_for('expenses'))
    c.close(); return render_template('edit.html', entity='Expense', item=item, fields=[('category','Category','text'),('description','Description','text'),('amount','Amount','number'),('payment_method','Payment Method','select',['UPI','Cash','Card','Bank Transfer'])], back_url=url_for('expenses'))

@app.route('/expenses/delete/<int:item_id>', methods=['POST'])
def delete_expense(item_id):
    if not require('expenses'): return redirect(url_for('dashboard'))
    c=db(); c.execute('DELETE FROM expenses WHERE id=?',(item_id,)); c.commit(); c.close(); flash('Expense deleted','success'); return redirect(url_for('expenses'))

@app.route('/finance')
def finance():
    if not require('finance'): return redirect(url_for('dashboard'))
    c=db(); revenue=c.execute('SELECT COALESCE(SUM(total),0) v FROM sales').fetchone()['v']; expenses=c.execute('SELECT COALESCE(SUM(amount),0) v FROM expenses').fetchone()['v']; purchases=c.execute('SELECT COALESCE(SUM(total),0) v FROM purchases').fetchone()['v']; receivable=c.execute("SELECT COALESCE(SUM(total),0) v FROM sales WHERE payment_status!='Paid'").fetchone()['v']; payable=c.execute("SELECT COALESCE(SUM(total),0) v FROM purchases WHERE payment_status!='Paid'").fetchone()['v']; c.close(); return render_template('finance.html', revenue=revenue,expenses=expenses,purchases=purchases,profit=revenue-expenses,receivable=receivable,payable=payable)

@app.route('/inventory')
def inventory():
    if not require('inventory'): return redirect(url_for('dashboard'))
    c=db(); rows=c.execute('SELECT * FROM products ORDER BY stock ASC').fetchall(); c.close(); return render_template('inventory.html', products=rows)

@app.route('/employees', methods=['GET','POST'])
def employees():
    if not require('employees'): return redirect(url_for('dashboard'))
    c=db()
    if request.method=='POST':
        c.execute('INSERT INTO employees(name,department,job_role,salary,status,created_at) VALUES(?,?,?,?,?,?)',(request.form['name'],request.form.get('department'),request.form.get('job_role'),float(request.form.get('salary',0)),request.form.get('status','Active'),now())); c.commit(); flash('Employee added','success')
    rows=c.execute('SELECT * FROM employees ORDER BY id DESC').fetchall(); c.close(); return render_template('employees.html', employees=rows)

@app.route('/employees/edit/<int:item_id>', methods=['GET','POST'])
def edit_employee(item_id):
    if not require('employees'): return redirect(url_for('dashboard'))
    c=db(); item=c.execute('SELECT * FROM employees WHERE id=?',(item_id,)).fetchone()
    if not item: c.close(); flash('Employee not found','danger'); return redirect(url_for('employees'))
    if request.method=='POST':
        c.execute('UPDATE employees SET name=?,department=?,job_role=?,salary=?,status=? WHERE id=?',(request.form['name'],request.form.get('department'),request.form.get('job_role'),float(request.form.get('salary',0)),request.form.get('status','Active'),item_id)); c.commit(); c.close(); flash('Employee updated','success'); return redirect(url_for('employees'))
    c.close(); return render_template('edit.html', entity='Employee', item=item, fields=[('name','Name','text'),('department','Department','text'),('job_role','Job Role','text'),('salary','Salary','number'),('status','Status','select',['Active','Inactive'])], back_url=url_for('employees'))

@app.route('/employees/delete/<int:item_id>', methods=['POST'])
def delete_employee(item_id):
    if not require('employees'): return redirect(url_for('dashboard'))
    c=db(); c.execute('DELETE FROM employees WHERE id=?',(item_id,)); c.commit(); c.close(); flash('Employee deleted','success'); return redirect(url_for('employees'))

@app.route('/users', methods=['GET','POST'])
def users():
    if not require('users'): return redirect(url_for('dashboard'))
    c=db()
    if request.method=='POST':
        try:
            c.execute('INSERT INTO users(name,email,password,role,created_at) VALUES(?,?,?,?,?)',(request.form['name'],request.form['email'].lower(),generate_password_hash(request.form['password']),request.form['role'],now())); c.commit(); flash('User created','success')
        except sqlite3.IntegrityError: flash('Email already exists','danger')
    rows=c.execute('SELECT id,name,email,role,created_at FROM users ORDER BY id DESC').fetchall(); c.close(); return render_template('users.html', users=rows, roles=list(ROLES))

@app.route('/users/edit/<int:item_id>', methods=['GET','POST'])
def edit_user(item_id):
    if not require('users'): return redirect(url_for('dashboard'))
    c=db(); item=c.execute('SELECT id,name,email,role,created_at FROM users WHERE id=?',(item_id,)).fetchone()
    if not item: c.close(); flash('User not found','danger'); return redirect(url_for('users'))
    if request.method=='POST':
        try:
            c.execute('UPDATE users SET name=?,email=?,role=? WHERE id=?',(request.form['name'],request.form['email'].lower(),request.form['role'],item_id))
            if request.form.get('password'): c.execute('UPDATE users SET password=? WHERE id=?',(generate_password_hash(request.form['password']),item_id))
            c.commit(); c.close(); flash('User updated','success'); return redirect(url_for('users'))
        except sqlite3.IntegrityError: flash('Email already exists','danger')
    c.close(); return render_template('edit.html', entity='User', item=item, fields=[('name','Name','text'),('email','Email','email'),('role','Role','select',list(ROLES)),('password','New Password (optional)','password')], back_url=url_for('users'))

@app.route('/users/delete/<int:item_id>', methods=['POST'])
def delete_user(item_id):
    if not require('users'): return redirect(url_for('dashboard'))
    if item_id == session.get('user_id'): flash('You cannot delete your own logged-in account.','danger'); return redirect(url_for('users'))
    c=db(); c.execute('DELETE FROM users WHERE id=?',(item_id,)); c.commit(); c.close(); flash('User deleted','success'); return redirect(url_for('users'))

@app.route('/reports')
def reports():
    if not require('reports'): return redirect(url_for('dashboard'))
    c=db(); sales=c.execute('SELECT COUNT(*) count,COALESCE(SUM(total),0) total FROM sales').fetchone(); expenses=c.execute('SELECT COUNT(*) count,COALESCE(SUM(amount),0) total FROM expenses').fetchone(); products=c.execute('SELECT COUNT(*) count FROM products').fetchone(); low=c.execute('SELECT COUNT(*) count FROM products WHERE stock<=min_stock').fetchone(); c.close(); return render_template('reports.html',sales=sales,expenses=expenses,products=products,low=low)

@app.route('/api/forecast')
def forecast():
    if not logged_in(): return jsonify({'error':'unauthorized'}),401
    c=db(); rows=c.execute("SELECT substr(created_at,1,10) d,SUM(total) total FROM sales GROUP BY d ORDER BY d").fetchall(); c.close()
    if len(rows)<2: return jsonify({'message':'Add at least two days of sales to generate a basic forecast.'})
    vals=[r['total'] for r in rows]; avg=sum(vals[-min(7,len(vals)):])/min(7,len(vals)); return jsonify({'recent_average':round(avg,2),'next_period_forecast':round(avg*1.05,2),'note':'Demo forecast: rolling average + 5%. Replace with Prophet/XGBoost for your final ML implementation.'})

if __name__=='__main__':
    init_db(); app.run(debug=True)
