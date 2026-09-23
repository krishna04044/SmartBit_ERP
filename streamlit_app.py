import streamlit as st
import sqlite3
import os
import io
import pandas as pd
import plotly.express as px
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# ReportLab imports for invoice PDF generation
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

DB_PATH = os.path.join(os.path.dirname(__file__), 'smartbiz.db')

ROLES = {
    'Super Admin': ['Dashboard', 'Users & Roles', 'Products', 'Inventory', 'Customers', 'Suppliers', 'Sales & Invoices', 'Purchases', 'Expenses', 'Finance', 'Employees', 'Reports & Analytics'],
    'Business Admin': ['Dashboard', 'Products', 'Inventory', 'Customers', 'Suppliers', 'Sales & Invoices', 'Purchases', 'Expenses', 'Finance', 'Employees', 'Reports & Analytics'],
    'Finance Manager': ['Dashboard', 'Expenses', 'Finance', 'Reports & Analytics'],
    'Inventory Manager': ['Dashboard', 'Products', 'Inventory', 'Suppliers', 'Purchases', 'Reports & Analytics'],
    'Sales Manager': ['Dashboard', 'Customers', 'Sales & Invoices', 'Reports & Analytics'],
    'Purchase Manager': ['Dashboard', 'Suppliers', 'Purchases', 'Inventory', 'Reports & Analytics'],
    'HR Manager': ['Dashboard', 'Employees', 'Reports & Analytics'],
    'Sales Staff': ['Dashboard', 'Customers', 'Sales & Invoices'],
    'Inventory Staff': ['Dashboard', 'Products', 'Inventory']
}

def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn

def now():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def init_db():
    conn = get_db()
    conn.executescript('''
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
    if conn.execute('SELECT COUNT(*) n FROM users').fetchone()['n'] == 0:
        conn.execute('INSERT INTO users(name,email,password,role,created_at) VALUES(?,?,?,?,?)',
                     ('Administrator', 'admin@smartbiz.com', generate_password_hash('admin123'), 'Super Admin', now()))
    if conn.execute('SELECT COUNT(*) n FROM products').fetchone()['n'] == 0:
        conn.executemany('INSERT INTO products(sku,name,category,purchase_price,selling_price,stock,min_stock,warehouse,created_at) VALUES(?,?,?,?,?,?,?,?,?)', [
            ('KB-001', 'Wireless Keyboard', 'Accessories', 500, 800, 113, 20, 'Main Warehouse', now()),
            ('GM-001', 'Gaming Mouse', 'Accessories', 700, 1200, 59, 15, 'Main Warehouse', now()),
            ('HP-001', 'Headphones', 'Audio', 900, 1500, 12, 20, 'Main Warehouse', now())
        ])
    conn.commit()
    conn.close()

def generate_pdf_invoice(sale, items):
    if not HAS_REPORTLAB:
        return None
    sale_data = dict(sale)
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
        Paragraph(f"<b>Invoice:</b> {sale_data['invoice_no']}", norm),
        Paragraph(f"<b>Date:</b> {sale_data['created_at']}", norm),
        Paragraph(f"<b>Customer:</b> {sale_data['customer'] or 'Walk-in Customer'}", norm),
    ]
    if sale_data.get('phone'):
        story.append(Paragraph(f"<b>Phone:</b> {sale_data['phone']}", norm))
    if sale_data.get('email'):
        story.append(Paragraph(f"<b>Email:</b> {sale_data['email']}", norm))
    story.append(Spacer(1, 15))

    data = [['SKU', 'Product', 'Qty', 'Unit Price', 'Amount']]
    for it in items:
        it_data = dict(it)
        data.append([
            str(it_data['sku']),
            str(it_data['name']),
            str(it_data['qty']),
            f"Rs. {it_data['unit_price']:.2f}",
            f"Rs. {it_data['qty']*it_data['unit_price']:.2f}"
        ])
    data.append(['', '', '', 'Total', f"Rs. {sale_data['total']:.2f}"])

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
        Paragraph(f"<b>Payment:</b> {sale_data['payment_status']} | <b>Method:</b> {sale_data.get('payment_method') or 'UPI'}", norm),
        Spacer(1, 20),
        Paragraph('<i>Thank you for your business.</i>', sub_style)
    ])
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# ----------------- STREAMLIT APPLICATION -----------------

st.set_page_config(page_title="SmartBiz ERP", page_icon="💼", layout="wide")

init_db()

if 'user' not in st.session_state:
    st.session_state.user = None

def login_user(email, password):
    conn = get_db()
    u = conn.execute('SELECT * FROM users WHERE email=?', (email.strip().lower(),)).fetchone()
    conn.close()
    if u and check_password_hash(u['password'], password):
        st.session_state.user = {
            'id': u['id'],
            'name': u['name'],
            'email': u['email'],
            'role': u['role']
        }
        return True
    return False

def logout_user():
    st.session_state.user = None
    st.rerun()

# ----------------- LOGIN SCREEN -----------------
if not st.session_state.user:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h2 style='text-align: center; color: #1e293b;'>💼 SmartBiz ERP</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #64748b;'>Enterprise Resource Planning & Business Management</p>", unsafe_allow_html=True)
        
        with st.form("login_form"):
            st.subheader("Sign In")
            email = st.text_input("Email Address", value="admin@smartbiz.com")
            password = st.text_input("Password", type="password", value="admin123")
            submit = st.form_submit_button("Sign In", use_container_width=True, type="primary")

            if submit:
                if login_user(email, password):
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid email or password.")

        st.info("💡 **Demo Credentials**:\n- **Email**: `admin@smartbiz.com`\n- **Password**: `admin123`")
    st.stop()

# ----------------- AUTHENTICATED USER SESSION -----------------
user = st.session_state.user
allowed_modules = ROLES.get(user['role'], ['Dashboard'])

with st.sidebar:
    st.markdown(f"### 💼 **SmartBiz ERP**")
    st.markdown(f"👤 **{user['name']}**")
    st.caption(f"Role: `{user['role']}`")
    st.divider()

    selected_module = st.radio("Navigation", allowed_modules, index=0)

    st.divider()
    if st.button("🚪 Logout", use_container_width=True):
        logout_user()

# ==================== MODULE: DASHBOARD ====================
if selected_module == 'Dashboard':
    st.title("📊 Business Dashboard")
    st.caption(f"Welcome back, {user['name']}! Live overview of operations, cashflow, and inventory.")

    conn = get_db()
    revenue = conn.execute("SELECT COALESCE(SUM(total),0) v FROM sales").fetchone()['v']
    expenses = conn.execute("SELECT COALESCE(SUM(amount),0) v FROM expenses").fetchone()['v']
    purchases = conn.execute("SELECT COALESCE(SUM(total),0) v FROM purchases").fetchone()['v']
    customers_cnt = conn.execute("SELECT COUNT(*) v FROM customers").fetchone()['v']
    orders_cnt = conn.execute("SELECT COUNT(*) v FROM sales").fetchone()['v']
    low_stock = conn.execute("SELECT * FROM products WHERE stock <= min_stock ORDER BY stock ASC").fetchall()
    recent_sales = conn.execute("SELECT s.*, c.name customer FROM sales s LEFT JOIN customers c ON c.id=s.customer_id ORDER BY s.id DESC LIMIT 8").fetchall()
    monthly_rows = conn.execute("SELECT substr(created_at,1,7) month, SUM(total) total FROM sales GROUP BY month ORDER BY month ASC").fetchall()
    conn.close()

    net_profit = revenue - expenses

    # Metric Cards
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Revenue", f"₹{revenue:,.2f}", delta=f"{orders_cnt} orders")
    c2.metric("Total Expenses", f"₹{expenses:,.2f}", delta="-Operational", delta_color="inverse")
    c3.metric("Net Profit", f"₹{net_profit:,.2f}", delta="Healthy" if net_profit >= 0 else "Deficit")
    c4.metric("Client Base", f"{customers_cnt} Customers", delta=f"{len(low_stock)} Low Stock")

    st.write("")

    # Chart & Low Stock
    col_chart, col_low = st.columns([2, 1])

    with col_chart:
        st.subheader("📈 Monthly Sales Trend")
        if monthly_rows:
            df_monthly = pd.DataFrame([dict(r) for r in monthly_rows])
            fig = px.area(df_monthly, x="month", y="total", markers=True,
                          labels={"month": "Month", "total": "Revenue (₹)"},
                          color_discrete_sequence=["#3b82f6"])
            fig.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=300)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No sales transactions recorded yet. Record sales to populate visual trend curves.")

    with col_low:
        st.subheader("⚠️ Low Stock Alert")
        if low_stock:
            df_low = pd.DataFrame([{'Product': r['name'], 'Stock': r['stock'], 'Min': r['min_stock']} for r in low_stock])
            st.dataframe(df_low, hide_index=True, use_container_width=True)
        else:
            st.success("All stock levels are optimal!")

    # AI Forecast & Insights Section
    with st.expander("🤖 AI Sales Forecast & Analytical Projections", expanded=True):
        conn = get_db()
        rows_fc = conn.execute("SELECT substr(created_at,1,10) d, SUM(total) total FROM sales GROUP BY d ORDER BY d").fetchall()
        conn.close()

        if not rows_fc:
            st.warning("No sales transactions found yet. Create sales orders to activate the forecast engine.")
        elif len(rows_fc) == 1:
            val = rows_fc[0]['total']
            f1, f2, f3 = st.columns(3)
            f1.metric("Recent Daily Average", f"₹{val:,.2f}")
            f2.metric("Projected Next Period", f"₹{val * 1.05:,.2f}", delta="+5.0% Growth")
            f3.metric("Analyzed Days", "1 Day")
            st.caption("Baseline projection active (+5% growth trajectory). Add sales on multiple calendar dates to enable rolling trend detection.")
        else:
            vals = [r['total'] for r in rows_fc]
            window = min(7, len(vals))
            avg = sum(vals[-window:]) / window
            growth = 1.05 if vals[-1] >= vals[0] else 0.98
            forecast_val = round(avg * growth, 2)
            pct = "+5.0%" if growth > 1 else "-2.0%"

            f1, f2, f3 = st.columns(3)
            f1.metric("Recent Daily Average", f"₹{avg:,.2f}")
            f2.metric("Projected Next Period", f"₹{forecast_val:,.2f}", delta=f"{pct} Trend")
            f3.metric("Analyzed History", f"{len(vals)} Active Sales Days")
            st.caption(f"Model: {window}-day weighted moving average with trajectory momentum.")

    # Recent Sales Activity
    st.subheader("🛒 Recent Sales Activity")
    if recent_sales:
        df_recent = pd.DataFrame([{
            'Invoice #': r['invoice_no'],
            'Customer': r['customer'] or 'Walk-in Customer',
            'Total': f"₹{r['total']:,.2f}",
            'Payment': r['payment_status'],
            'Method': r['payment_method'] or 'UPI',
            'Date': r['created_at']
        } for r in recent_sales])
        st.dataframe(df_recent, hide_index=True, use_container_width=True)
    else:
        st.caption("No recent sales records.")

# ==================== MODULE: PRODUCTS ====================
elif selected_module == 'Products':
    st.title("📦 Products Catalog")
    st.caption("Manage product master data, pricing, inventory stock thresholds, and warehouses.")

    t1, t2 = st.tabs(["Catalog List", "Add New Product"])

    with t2:
        with st.form("add_product_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            sku = col1.text_input("SKU Code *", placeholder="e.g. KB-002")
            name = col2.text_input("Product Name *", placeholder="e.g. Ergonomic Keyboard")

            col3, col4 = st.columns(2)
            category = col3.text_input("Category", placeholder="e.g. Accessories")
            warehouse = col4.text_input("Warehouse Location", value="Main Warehouse")

            col5, col6, col7, col8 = st.columns(4)
            buy_price = col5.number_input("Purchase Price (₹)", min_value=0.0, step=10.0, value=0.0)
            sell_price = col6.number_input("Selling Price (₹)", min_value=0.0, step=10.0, value=0.0)
            stock = col7.number_input("Initial Stock", min_value=0, step=1, value=10)
            min_stock = col8.number_input("Min Reorder Level", min_value=0, step=1, value=5)

            if st.form_submit_button("Add Product", type="primary"):
                if not sku.strip() or not name.strip():
                    st.error("SKU and Product Name are required fields.")
                else:
                    conn = get_db()
                    try:
                        conn.execute("INSERT INTO products(sku,name,category,purchase_price,selling_price,stock,min_stock,warehouse,created_at) VALUES(?,?,?,?,?,?,?,?,?)",
                                     (sku.strip(), name.strip(), category.strip(), buy_price, sell_price, stock, min_stock, warehouse.strip(), now()))
                        conn.commit()
                        st.success(f"Product '{name}' added successfully!")
                    except sqlite3.IntegrityError:
                        st.error(f"A product with SKU '{sku}' already exists.")
                    finally:
                        conn.close()

    with t1:
        conn = get_db()
        products = conn.execute("SELECT * FROM products ORDER BY id DESC").fetchall()
        conn.close()

        if products:
            search = st.text_input("🔍 Search products by name, SKU, or category", "")
            filtered = [dict(p) for p in products if search.lower() in p['name'].lower() or search.lower() in p['sku'].lower() or search.lower() in (p['category'] or '').lower()]

            df_prod = pd.DataFrame([{
                'ID': p['id'],
                'SKU': p['sku'],
                'Product Name': p['name'],
                'Category': p['category'] or '-',
                'Buy Price': f"₹{p['purchase_price']:,.2f}",
                'Sell Price': f"₹{p['selling_price']:,.2f}",
                'Stock': p['stock'],
                'Min Alert': p['min_stock'],
                'Status': '🔴 Out of Stock' if p['stock'] <= 0 else ('🟡 Low Stock' if p['stock'] <= p['min_stock'] else '🟢 In Stock')
            } for p in filtered])

            st.dataframe(df_prod, hide_index=True, use_container_width=True)

            st.divider()
            st.subheader("Manage Product Record")
            edit_id = st.selectbox("Select product to Edit / Delete", [p['id'] for p in filtered], format_func=lambda x: f"ID {x}: {next(p['name'] for p in filtered if p['id'] == x)} ({next(p['sku'] for p in filtered if p['id'] == x)})")

            if edit_id:
                p_item = next(p for p in filtered if p['id'] == edit_id)
                e1, e2 = st.columns(2)
                with e1:
                    with st.form(f"edit_prod_{edit_id}"):
                        st.write("##### Edit Product Details")
                        e_sku = st.text_input("SKU", value=p_item['sku'])
                        e_name = st.text_input("Name", value=p_item['name'])
                        e_cat = st.text_input("Category", value=p_item['category'] or '')
                        e_buy = st.number_input("Buy Price (₹)", value=float(p_item['purchase_price']))
                        e_sell = st.number_input("Sell Price (₹)", value=float(p_item['selling_price']))
                        e_stock = st.number_input("Stock", value=int(p_item['stock']))
                        e_min = st.number_input("Min Stock", value=int(p_item['min_stock']))
                        if st.form_submit_button("Update Product"):
                            conn = get_db()
                            try:
                                conn.execute("UPDATE products SET sku=?,name=?,category=?,purchase_price=?,selling_price=?,stock=?,min_stock=? WHERE id=?",
                                             (e_sku.strip(), e_name.strip(), e_cat.strip(), e_buy, e_sell, e_stock, e_min, edit_id))
                                conn.commit()
                                st.success("Product updated successfully!")
                                st.rerun()
                            except sqlite3.IntegrityError:
                                st.error("SKU already in use.")
                            finally:
                                conn.close()
                with e2:
                    st.write("##### Danger Zone")
                    st.caption("Cannot delete products linked to past sales or purchase transactions.")
                    if st.button("🗑️ Delete Product", type="secondary"):
                        conn = get_db()
                        has_sales = conn.execute("SELECT COUNT(*) n FROM sale_items WHERE product_id=?", (edit_id,)).fetchone()['n']
                        has_purchases = conn.execute("SELECT COUNT(*) n FROM purchase_items WHERE product_id=?", (edit_id,)).fetchone()['n']
                        if has_sales > 0 or has_purchases > 0:
                            st.error("Cannot delete product: It is linked to existing transactions.")
                        else:
                            conn.execute("DELETE FROM products WHERE id=?", (edit_id,))
                            conn.commit()
                            st.success("Product deleted successfully!")
                            st.rerun()
                        conn.close()
        else:
            st.info("No products found. Add products using the tab above.")

# ==================== MODULE: INVENTORY ====================
elif selected_module == 'Inventory':
    st.title("🏷️ Inventory Management")
    st.caption("Live stock positions, reorder monitoring, and total warehouse asset valuation.")

    conn = get_db()
    products = conn.execute("SELECT * FROM products ORDER BY stock ASC").fetchall()
    summary = conn.execute("SELECT COALESCE(SUM(stock * purchase_price),0) val, COALESCE(SUM(stock),0) items FROM products").fetchone()
    conn.close()

    m1, m2, m3 = st.columns(3)
    m1.metric("Total Warehouse Asset Value", f"₹{summary['val']:,.2f}")
    m2.metric("Total Stocked Units", f"{summary['items']:,}")
    m3.metric("Catalog Items Tracked", f"{len(products)}")

    st.write("")
    if products:
        df_inv = pd.DataFrame([{
            'SKU': p['sku'],
            'Product': p['name'],
            'Warehouse': p['warehouse'],
            'Current Stock': p['stock'],
            'Min Alert': p['min_stock'],
            'Asset Value (₹)': f"₹{p['stock'] * p['purchase_price']:,.2f}",
            'Status': '🔴 Out of Stock' if p['stock'] <= 0 else ('🟡 Reorder Needed' if p['stock'] <= p['min_stock'] else '🟢 Optimal')
        } for p in products])
        st.dataframe(df_inv, hide_index=True, use_container_width=True)
    else:
        st.info("No inventory items found.")

# ==================== MODULE: CUSTOMERS ====================
elif selected_module == 'Customers':
    st.title("👥 Customers CRM")
    st.caption("Manage customer directory, contact details, and historical accounts.")

    t1, t2 = st.tabs(["Customer Directory", "Add New Customer"])

    with t2:
        with st.form("add_cust_form", clear_on_submit=True):
            name = st.text_input("Full Name / Company Name *")
            col1, col2 = st.columns(2)
            phone = col1.text_input("Phone Number")
            email = col2.text_input("Email Address")
            address = st.text_area("Billing / Shipping Address")

            if st.form_submit_button("Add Customer", type="primary"):
                if not name.strip():
                    st.error("Customer name is required.")
                else:
                    conn = get_db()
                    conn.execute("INSERT INTO customers(name,phone,email,address,created_at) VALUES(?,?,?,?,?)",
                                 (name.strip(), phone.strip(), email.strip(), address.strip(), now()))
                    conn.commit()
                    conn.close()
                    st.success(f"Customer '{name}' added successfully!")

    with t1:
        conn = get_db()
        customers = conn.execute("SELECT * FROM customers ORDER BY id DESC").fetchall()
        conn.close()

        if customers:
            search = st.text_input("🔍 Search customers", "")
            filtered = [dict(c) for c in customers if search.lower() in c['name'].lower() or search.lower() in (c['phone'] or '').lower() or search.lower() in (c['email'] or '').lower()]

            df_cust = pd.DataFrame([{
                'ID': c['id'],
                'Name': c['name'],
                'Phone': c['phone'] or '-',
                'Email': c['email'] or '-',
                'Address': c['address'] or '-',
                'Registered': c['created_at']
            } for c in filtered])
            st.dataframe(df_cust, hide_index=True, use_container_width=True)

            st.divider()
            c_id = st.selectbox("Select Customer to Manage", [c['id'] for c in filtered], format_func=lambda x: next(c['name'] for c in filtered if c['id'] == x))
            if c_id:
                cust_sel = next(c for c in filtered if c['id'] == c_id)
                col1, col2 = st.columns(2)
                with col1:
                    with st.form(f"edit_cust_{c_id}"):
                        st.write("##### Edit Customer")
                        en = st.text_input("Name", value=cust_sel['name'])
                        ep = st.text_input("Phone", value=cust_sel['phone'] or '')
                        ee = st.text_input("Email", value=cust_sel['email'] or '')
                        ea = st.text_area("Address", value=cust_sel['address'] or '')
                        if st.form_submit_button("Update Customer"):
                            conn = get_db()
                            conn.execute("UPDATE customers SET name=?,phone=?,email=?,address=? WHERE id=?", (en.strip(), ep.strip(), ee.strip(), ea.strip(), c_id))
                            conn.commit()
                            conn.close()
                            st.success("Customer updated!")
                            st.rerun()
                with col2:
                    st.write("##### Delete Customer")
                    st.caption("Historical sales invoices will be retained as walk-in orders.")
                    if st.button("🗑️ Delete Customer", key=f"del_c_{c_id}"):
                        conn = get_db()
                        conn.execute("UPDATE sales SET customer_id=NULL WHERE customer_id=?", (c_id,))
                        conn.execute("DELETE FROM customers WHERE id=?", (c_id,))
                        conn.commit()
                        conn.close()
                        st.success("Customer deleted!")
                        st.rerun()
        else:
            st.info("No customers registered yet.")

# ==================== MODULE: SUPPLIERS ====================
elif selected_module == 'Suppliers':
    st.title("🚚 Suppliers Management")
    st.caption("Manage procurement vendors, contact information, and supply sources.")

    t1, t2 = st.tabs(["Supplier Directory", "Add New Supplier"])

    with t2:
        with st.form("add_supp_form", clear_on_submit=True):
            name = st.text_input("Supplier / Business Name *")
            col1, col2 = st.columns(2)
            phone = col1.text_input("Phone Number")
            email = col2.text_input("Email Address")
            address = st.text_area("Location / Address")

            if st.form_submit_button("Add Supplier", type="primary"):
                if not name.strip():
                    st.error("Supplier name is required.")
                else:
                    conn = get_db()
                    conn.execute("INSERT INTO suppliers(name,phone,email,address,created_at) VALUES(?,?,?,?,?)",
                                 (name.strip(), phone.strip(), email.strip(), address.strip(), now()))
                    conn.commit()
                    conn.close()
                    st.success(f"Supplier '{name}' added successfully!")

    with t1:
        conn = get_db()
        suppliers = conn.execute("SELECT * FROM suppliers ORDER BY id DESC").fetchall()
        conn.close()

        if suppliers:
            df_supp = pd.DataFrame([{
                'ID': s['id'],
                'Name': s['name'],
                'Phone': s['phone'] or '-',
                'Email': s['email'] or '-',
                'Address': s['address'] or '-',
                'Created': s['created_at']
            } for s in suppliers])
            st.dataframe(df_supp, hide_index=True, use_container_width=True)

            st.divider()
            s_id = st.selectbox("Select Supplier to Manage", [s['id'] for s in suppliers], format_func=lambda x: next(s['name'] for s in suppliers if s['id'] == x))
            if s_id:
                supp_sel = next(s for s in suppliers if s['id'] == s_id)
                col1, col2 = st.columns(2)
                with col1:
                    with st.form(f"edit_supp_{s_id}"):
                        st.write("##### Edit Supplier")
                        sn = st.text_input("Supplier Name", value=supp_sel['name'])
                        sp = st.text_input("Phone", value=supp_sel['phone'] or '')
                        se = st.text_input("Email", value=supp_sel['email'] or '')
                        sa = st.text_area("Address", value=supp_sel['address'] or '')
                        if st.form_submit_button("Update Supplier"):
                            conn = get_db()
                            conn.execute("UPDATE suppliers SET name=?,phone=?,email=?,address=? WHERE id=?", (sn.strip(), sp.strip(), se.strip(), sa.strip(), s_id))
                            conn.commit()
                            conn.close()
                            st.success("Supplier updated!")
                            st.rerun()
                with col2:
                    st.write("##### Delete Supplier")
                    st.caption("Past purchase records will be preserved without supplier link.")
                    if st.button("🗑️ Delete Supplier", key=f"del_s_{s_id}"):
                        conn = get_db()
                        conn.execute("UPDATE purchases SET supplier_id=NULL WHERE supplier_id=?", (s_id,))
                        conn.execute("DELETE FROM suppliers WHERE id=?", (s_id,))
                        conn.commit()
                        conn.close()
                        st.success("Supplier deleted!")
                        st.rerun()
        else:
            st.info("No suppliers registered yet.")

# ==================== MODULE: SALES & INVOICES ====================
elif selected_module == 'Sales & Invoices':
    st.title("🛒 Sales & Invoicing")
    st.caption("Record customer sales, automatically deduct warehouse stock, and download tax invoices.")

    t1, t2 = st.tabs(["Sales Records", "Create New Sale"])

    conn = get_db()
    products = conn.execute("SELECT * FROM products ORDER BY name").fetchall()
    customers = conn.execute("SELECT * FROM customers ORDER BY name").fetchall()
    conn.close()

    with t2:
        if not products:
            st.warning("No products available in the catalog. Please add products first.")
        else:
            with st.form("create_sale_form", clear_on_submit=True):
                st.subheader("New Sales Order")
                c_opts = [None] + [c['id'] for c in customers]
                cust_id = st.selectbox("Select Customer", c_opts, format_func=lambda x: "Walk-in Customer (None)" if x is None else next(c['name'] for c in customers if c['id'] == x))

                prod_opts = [p['id'] for p in products]
                p_id = st.selectbox("Select Product", prod_opts, format_func=lambda x: f"{next(p['name'] for p in products if p['id'] == x)} — ₹{next(p['selling_price'] for p in products if p['id'] == x):,.2f} ({next(p['stock'] for p in products if p['id'] == x)} in stock)")

                col1, col2, col3 = st.columns(3)
                qty = col1.number_input("Quantity", min_value=1, value=1, step=1)
                method = col2.selectbox("Payment Method", ["UPI", "Cash", "Card", "Bank Transfer"])
                status = col3.selectbox("Payment Status", ["Paid", "Pending"])

                if st.form_submit_button("Complete Sale", type="primary"):
                    conn = get_db()
                    prod_rec = conn.execute("SELECT * FROM products WHERE id=?", (p_id,)).fetchone()
                    if not prod_rec:
                        st.error("Selected product not found.")
                    elif prod_rec['stock'] < qty:
                        st.error(f"Insufficient stock! Only {prod_rec['stock']} available for {prod_rec['name']}.")
                    else:
                        total = round(qty * prod_rec['selling_price'], 2)
                        inv = 'INV-' + datetime.now().strftime('%Y%m%d%H%M%S%f')[:18]
                        cur = conn.execute("INSERT INTO sales(customer_id,invoice_no,total,payment_status,payment_method,created_at) VALUES(?,?,?,?,?,?)",
                                           (cust_id, inv, total, status, method, now()))
                        conn.execute("INSERT INTO sale_items(sale_id,product_id,qty,unit_price) VALUES(?,?,?,?)",
                                     (cur.lastrowid, prod_rec['id'], qty, prod_rec['selling_price']))
                        conn.execute("UPDATE products SET stock=stock-? WHERE id=?", (qty, prod_rec['id']))
                        conn.commit()
                        st.success(f"Sale completed! Invoice #{inv} generated for ₹{total:,.2f}.")
                        st.rerun()
                    conn.close()

    with t1:
        conn = get_db()
        sales_records = conn.execute("SELECT s.*, c.name customer, c.phone, c.email, c.address FROM sales s LEFT JOIN customers c ON c.id=s.customer_id ORDER BY s.id DESC LIMIT 50").fetchall()
        conn.close()

        if sales_records:
            df_sales = pd.DataFrame([{
                'ID': s['id'],
                'Invoice #': s['invoice_no'],
                'Customer': s['customer'] or 'Walk-in Customer',
                'Total': f"₹{s['total']:,.2f}",
                'Status': '🟢 Paid' if s['payment_status'] == 'Paid' else '🟡 Pending',
                'Method': s['payment_method'] or 'UPI',
                'Date': s['created_at']
            } for s in sales_records])
            st.dataframe(df_sales, hide_index=True, use_container_width=True)

            st.divider()
            sale_id = st.selectbox("Select Sale to View Invoice & Actions", [s['id'] for s in sales_records], format_func=lambda x: f"Invoice #{next(s['invoice_no'] for s in sales_records if s['id'] == x)} — {next(s['customer'] or 'Walk-in' for s in sales_records if s['id'] == x)} (₹{next(s['total'] for s in sales_records if s['id'] == x):,.2f})")

            if sale_id:
                s_item = next(s for s in sales_records if s['id'] == sale_id)
                conn = get_db()
                items = conn.execute("SELECT si.*, COALESCE(p.name, 'Discontinued Item') name, COALESCE(p.sku, '-') sku FROM sale_items si LEFT JOIN products p ON p.id=si.product_id WHERE si.sale_id=?", (sale_id,)).fetchall()
                conn.close()

                c_info, c_actions = st.columns([2, 1])

                with c_info:
                    st.subheader(f"Invoice: {s_item['invoice_no']}")
                    st.write(f"**Customer:** {s_item['customer'] or 'Walk-in Customer'} | **Date:** {s_item['created_at']}")
                    st.write(f"**Payment:** {s_item['payment_status']} via {s_item['payment_method'] or 'UPI'}")

                    df_it = pd.DataFrame([{
                        'SKU': it['sku'],
                        'Product': it['name'],
                        'Qty': it['qty'],
                        'Unit Price': f"₹{it['unit_price']:,.2f}",
                        'Amount': f"₹{it['qty'] * it['unit_price']:,.2f}"
                    } for it in items])
                    st.dataframe(df_it, hide_index=True, use_container_width=True)
                    st.markdown(f"### **Grand Total: ₹{s_item['total']:,.2f}**")

                with c_actions:
                    st.subheader("Invoice Actions")
                    # PDF Download Button
                    pdf_bytes = generate_pdf_invoice(s_item, items)
                    if pdf_bytes:
                        st.download_button(
                            label="📄 Download Official PDF Invoice",
                            data=pdf_bytes,
                            file_name=f"{s_item['invoice_no']}.pdf",
                            mime="application/pdf",
                            type="primary",
                            use_container_width=True
                        )

                    st.write("---")
                    # Edit payment status
                    new_status = st.selectbox("Update Status", ["Paid", "Pending"], index=0 if s_item['payment_status'] == 'Paid' else 1, key=f"stat_{sale_id}")
                    if st.button("Save Payment Status", key=f"btn_stat_{sale_id}", use_container_width=True):
                        conn = get_db()
                        conn.execute("UPDATE sales SET payment_status=? WHERE id=?", (new_status, sale_id))
                        conn.commit()
                        conn.close()
                        st.success("Payment status updated!")
                        st.rerun()

                    # Delete sale & restore stock
                    if st.button("🗑️ Delete Sale (Restore Stock)", key=f"del_sale_{sale_id}", use_container_width=True):
                        conn = get_db()
                        for it in items:
                            conn.execute("UPDATE products SET stock=stock+? WHERE id=?", (it['qty'], it['product_id']))
                        conn.execute("DELETE FROM sale_items WHERE sale_id=?", (sale_id,))
                        conn.execute("DELETE FROM sales WHERE id=?", (sale_id,))
                        conn.commit()
                        conn.close()
                        st.success("Sale deleted and stock restored!")
                        st.rerun()
        else:
            st.info("No sales orders recorded yet.")

# ==================== MODULE: PURCHASES ====================
elif selected_module == 'Purchases':
    st.title("📥 Purchases & Restocking")
    st.caption("Receive stock shipments from suppliers and automatically increment inventory levels.")

    t1, t2 = st.tabs(["Purchase History", "Receive New Purchase"])

    conn = get_db()
    products = conn.execute("SELECT * FROM products ORDER BY name").fetchall()
    suppliers = conn.execute("SELECT * FROM suppliers ORDER BY name").fetchall()
    conn.close()

    with t2:
        if not products:
            st.warning("Please add products before receiving purchases.")
        else:
            with st.form("create_po_form", clear_on_submit=True):
                st.subheader("Receive Stock Shipment")
                s_opts = [None] + [s['id'] for s in suppliers]
                supp_id = st.selectbox("Supplier", s_opts, format_func=lambda x: "Direct Purchase / Unknown" if x is None else next(s['name'] for s in suppliers if s['id'] == x))

                prod_opts = [p['id'] for p in products]
                p_id = st.selectbox("Product to Restock", prod_opts, format_func=lambda x: f"{next(p['name'] for p in products if p['id'] == x)} — Buy: ₹{next(p['purchase_price'] for p in products if p['id'] == x):,.2f} (Current Stock: {next(p['stock'] for p in products if p['id'] == x)})")

                col1, col2 = st.columns(2)
                qty = col1.number_input("Units Received", min_value=1, value=10, step=1)
                status = col2.selectbox("Payment Status", ["Pending", "Paid"])

                if st.form_submit_button("Receive Stock", type="primary"):
                    conn = get_db()
                    p_rec = conn.execute("SELECT * FROM products WHERE id=?", (p_id,)).fetchone()
                    total = round(qty * p_rec['purchase_price'], 2)
                    po = 'PO-' + datetime.now().strftime('%Y%m%d%H%M%S%f')[:18]

                    cur = conn.execute("INSERT INTO purchases(supplier_id,po_no,total,payment_status,created_at) VALUES(?,?,?,?,?)",
                                       (supp_id, po, total, status, now()))
                    conn.execute("INSERT INTO purchase_items(purchase_id,product_id,qty,unit_price) VALUES(?,?,?,?)",
                                 (cur.lastrowid, p_rec['id'], qty, p_rec['purchase_price']))
                    conn.execute("UPDATE products SET stock=stock+? WHERE id=?", (qty, p_rec['id']))
                    conn.commit()
                    conn.close()
                    st.success(f"Stock received! Purchase Order #{po} recorded for ₹{total:,.2f}.")
                    st.rerun()

    with t1:
        conn = get_db()
        po_records = conn.execute("SELECT p.*, s.name supplier FROM purchases p LEFT JOIN suppliers s ON s.id=p.supplier_id ORDER BY p.id DESC LIMIT 50").fetchall()
        conn.close()

        if po_records:
            df_po = pd.DataFrame([{
                'ID': p['id'],
                'PO #': p['po_no'],
                'Supplier': p['supplier'] or 'Direct Purchase',
                'Total Cost': f"₹{p['total']:,.2f}",
                'Status': '🟢 Paid' if p['payment_status'] == 'Paid' else '🟡 Pending',
                'Received Date': p['created_at']
            } for p in po_records])
            st.dataframe(df_po, hide_index=True, use_container_width=True)

            st.divider()
            po_id = st.selectbox("Select PO to Manage", [p['id'] for p in po_records], format_func=lambda x: f"{next(p['po_no'] for p in po_records if p['id'] == x)} — {next(p['supplier'] or 'Direct' for p in po_records if p['id'] == x)} (₹{next(p['total'] for p in po_records if p['id'] == x):,.2f})")
            if po_id:
                po_sel = next(p for p in po_records if p['id'] == po_id)
                col1, col2 = st.columns(2)
                with col1:
                    new_st = st.selectbox("Update Status", ["Pending", "Paid"], index=0 if po_sel['payment_status'] == 'Pending' else 1, key=f"po_st_{po_id}")
                    if st.button("Save PO Status", key=f"btn_po_st_{po_id}"):
                        conn = get_db()
                        conn.execute("UPDATE purchases SET payment_status=? WHERE id=?", (new_st, po_id))
                        conn.commit()
                        conn.close()
                        st.success("PO payment status updated!")
                        st.rerun()
                with col2:
                    st.caption("Reverses received quantities from warehouse inventory.")
                    if st.button("🗑️ Delete Purchase (Reverse Stock)", key=f"del_po_{po_id}"):
                        conn = get_db()
                        items = conn.execute("SELECT * FROM purchase_items WHERE purchase_id=?", (po_id,)).fetchall()
                        for it in items:
                            conn.execute("UPDATE products SET stock=MAX(0, stock-?) WHERE id=?", (it['qty'], it['product_id']))
                        conn.execute("DELETE FROM purchase_items WHERE purchase_id=?", (po_id,))
                        conn.execute("DELETE FROM purchases WHERE id=?", (po_id,))
                        conn.commit()
                        conn.close()
                        st.success("Purchase deleted and inventory reversed!")
                        st.rerun()
        else:
            st.info("No purchase orders recorded yet.")

# ==================== MODULE: EXPENSES ====================
elif selected_module == 'Expenses':
    st.title("💸 Expense Tracking")
    st.caption("Record and monitor operational expenditures, utility bills, salaries, and office costs.")

    conn = get_db()
    total_exp = conn.execute("SELECT COALESCE(SUM(amount),0) v FROM expenses").fetchone()['v']
    by_cat = conn.execute("SELECT category, COUNT(*) count, SUM(amount) total FROM expenses GROUP BY category ORDER BY total DESC").fetchall()
    expenses = conn.execute("SELECT * FROM expenses ORDER BY id DESC").fetchall()
    conn.close()

    m1, m2 = st.columns([1, 2])
    m1.metric("Cumulative Expenses", f"₹{total_exp:,.2f}", delta=f"{len(expenses)} entries")
    with m2:
        if by_cat:
            cat_summary = " &bull; ".join([f"**{c['category']}**: ₹{c['total']:,.2f}" for c in by_cat])
            st.markdown(f"**Category Breakdown**: {cat_summary}")

    t1, t2 = st.tabs(["Expense History", "Record Expense"])

    with t2:
        with st.form("add_exp_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            cat = col1.selectbox("Category", ["Salary", "Rent", "Electricity", "Marketing", "Transportation", "Equipment", "Other"])
            method = col2.selectbox("Payment Method", ["UPI", "Cash", "Card", "Bank Transfer"])

            desc = st.text_input("Description", placeholder="e.g. September Office Electricity Bill")
            amt = st.number_input("Amount (₹)", min_value=0.01, step=100.0, value=500.0)

            if st.form_submit_button("Record Expense", type="primary"):
                conn = get_db()
                conn.execute("INSERT INTO expenses(category,description,amount,payment_method,created_at) VALUES(?,?,?,?,?)",
                             (cat, desc.strip(), amt, method, now()))
                conn.commit()
                conn.close()
                st.success("Expense recorded successfully!")
                st.rerun()

    with t1:
        if expenses:
            df_exp = pd.DataFrame([{
                'ID': e['id'],
                'Category': e['category'],
                'Description': e['description'] or '-',
                'Amount': f"₹{e['amount']:,.2f}",
                'Payment Method': e['payment_method'],
                'Date': e['created_at']
            } for e in expenses])
            st.dataframe(df_exp, hide_index=True, use_container_width=True)

            st.divider()
            e_id = st.selectbox("Select Expense to Manage", [e['id'] for e in expenses], format_func=lambda x: f"ID {x}: {next(e['category'] for e in expenses if e['id'] == x)} — ₹{next(e['amount'] for e in expenses if e['id'] == x):,.2f}")
            if e_id:
                exp_sel = next(e for e in expenses if e['id'] == e_id)
                col1, col2 = st.columns(2)
                with col1:
                    with st.form(f"edit_exp_{e_id}"):
                        st.write("##### Edit Expense")
                        ecat = st.selectbox("Category", ["Salary", "Rent", "Electricity", "Marketing", "Transportation", "Equipment", "Other"], index=["Salary", "Rent", "Electricity", "Marketing", "Transportation", "Equipment", "Other"].index(exp_sel['category']) if exp_sel['category'] in ["Salary", "Rent", "Electricity", "Marketing", "Transportation", "Equipment", "Other"] else 0)
                        edesc = st.text_input("Description", value=exp_sel['description'] or '')
                        eamt = st.number_input("Amount (₹)", value=float(exp_sel['amount']))
                        emeth = st.selectbox("Method", ["UPI", "Cash", "Card", "Bank Transfer"], index=["UPI", "Cash", "Card", "Bank Transfer"].index(exp_sel['payment_method']) if exp_sel['payment_method'] in ["UPI", "Cash", "Card", "Bank Transfer"] else 0)
                        if st.form_submit_button("Update Expense"):
                            conn = get_db()
                            conn.execute("UPDATE expenses SET category=?,description=?,amount=?,payment_method=? WHERE id=?", (ecat, edesc.strip(), eamt, emeth, e_id))
                            conn.commit()
                            conn.close()
                            st.success("Expense updated!")
                            st.rerun()
                with col2:
                    st.write("##### Delete Expense")
                    if st.button("🗑️ Delete Expense Entry", key=f"del_exp_{e_id}"):
                        conn = get_db()
                        conn.execute("DELETE FROM expenses WHERE id=?", (e_id,))
                        conn.commit()
                        conn.close()
                        st.success("Expense deleted!")
                        st.rerun()
        else:
            st.info("No expenses recorded yet.")

# ==================== MODULE: FINANCE ====================
elif selected_module == 'Finance':
    st.title("💰 Financial Overview")
    st.caption("Monitor corporate cashflow, operating profit, and outstanding receivables & payables.")

    conn = get_db()
    revenue = conn.execute("SELECT COALESCE(SUM(total),0) v FROM sales").fetchone()['v']
    expenses = conn.execute("SELECT COALESCE(SUM(amount),0) v FROM expenses").fetchone()['v']
    purchases = conn.execute("SELECT COALESCE(SUM(total),0) v FROM purchases").fetchone()['v']
    receivable = conn.execute("SELECT COALESCE(SUM(total),0) v FROM sales WHERE payment_status!='Paid'").fetchone()['v']
    payable = conn.execute("SELECT COALESCE(SUM(total),0) v FROM purchases WHERE payment_status!='Paid'").fetchone()['v']
    conn.close()

    net_profit = revenue - expenses

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Revenue", f"₹{revenue:,.2f}")
    col2.metric("Operating Expenses", f"₹{expenses:,.2f}", delta="-Disbursements", delta_color="inverse")
    col3.metric("Net Operating Profit", f"₹{net_profit:,.2f}", delta="Net Return")
    col4.metric("Inventory Purchases", f"₹{purchases:,.2f}")

    st.write("")
    c_rec, c_pay = st.columns(2)

    with c_rec:
        st.subheader("📬 Accounts Receivable")
        st.markdown(f"### **₹{receivable:,.2f}**")
        st.caption("Total value of customer sales invoices with **Pending** status awaiting collection.")

    with c_pay:
        st.subheader("📤 Accounts Payable")
        st.markdown(f"### **₹{payable:,.2f}**")
        st.caption("Total value of vendor purchase orders with **Pending** status awaiting settlement.")

# ==================== MODULE: EMPLOYEES ====================
elif selected_module == 'Employees':
    st.title("👨‍💼 Human Resources & Staff")
    st.caption("Manage employee personnel records, department assignments, designations, and payroll.")

    t1, t2 = st.tabs(["Employee Directory", "Add New Employee"])

    with t2:
        with st.form("add_emp_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            name = col1.text_input("Full Name *", placeholder="e.g. Ramesh Kumar")
            dept = col2.text_input("Department", placeholder="e.g. Sales, Operations, Tech")

            col3, col4, col5 = st.columns(3)
            role = col3.text_input("Job Role", placeholder="e.g. Associate Manager")
            salary = col4.number_input("Monthly Salary (₹)", min_value=0.0, step=1000.0, value=25000.0)
            status = col5.selectbox("Status", ["Active", "Inactive"])

            if st.form_submit_button("Add Employee", type="primary"):
                if not name.strip():
                    st.error("Employee name is required.")
                else:
                    conn = get_db()
                    conn.execute("INSERT INTO employees(name,department,job_role,salary,status,created_at) VALUES(?,?,?,?,?,?)",
                                 (name.strip(), dept.strip(), role.strip(), salary, status, now()))
                    conn.commit()
                    conn.close()
                    st.success(f"Employee '{name}' added successfully!")

    with t1:
        conn = get_db()
        employees = conn.execute("SELECT * FROM employees ORDER BY id DESC").fetchall()
        conn.close()

        if employees:
            df_emp = pd.DataFrame([{
                'ID': e['id'],
                'Name': e['name'],
                'Department': e['department'] or '-',
                'Role': e['job_role'] or '-',
                'Salary': f"₹{e['salary']:,.2f}",
                'Status': '🟢 Active' if e['status'] == 'Active' else '⚪ Inactive',
                'Joined': e['created_at']
            } for e in employees])
            st.dataframe(df_emp, hide_index=True, use_container_width=True)

            st.divider()
            e_id = st.selectbox("Select Employee to Manage", [e['id'] for e in employees], format_func=lambda x: f"{next(e['name'] for e in employees if e['id'] == x)} — {next(e['department'] or 'General' for e in employees if e['id'] == x)}")
            if e_id:
                emp_sel = next(e for e in employees if e['id'] == e_id)
                col1, col2 = st.columns(2)
                with col1:
                    with st.form(f"edit_emp_{e_id}"):
                        st.write("##### Edit Employee Details")
                        en = st.text_input("Name", value=emp_sel['name'])
                        ed = st.text_input("Department", value=emp_sel['department'] or '')
                        er = st.text_input("Job Role", value=emp_sel['job_role'] or '')
                        es = st.number_input("Monthly Salary", value=float(emp_sel['salary']))
                        est = st.selectbox("Status", ["Active", "Inactive"], index=0 if emp_sel['status'] == 'Active' else 1)
                        if st.form_submit_button("Update Employee"):
                            conn = get_db()
                            conn.execute("UPDATE employees SET name=?,department=?,job_role=?,salary=?,status=? WHERE id=?", (en.strip(), ed.strip(), er.strip(), es, est, e_id))
                            conn.commit()
                            conn.close()
                            st.success("Employee record updated!")
                            st.rerun()
                with col2:
                    st.write("##### Delete Employee")
                    if st.button("🗑️ Delete Employee Record", key=f"del_emp_{e_id}"):
                        conn = get_db()
                        conn.execute("DELETE FROM employees WHERE id=?", (e_id,))
                        conn.commit()
                        conn.close()
                        st.success("Employee deleted!")
                        st.rerun()
        else:
            st.info("No employees registered yet.")

# ==================== MODULE: USERS & ROLES ====================
elif selected_module == 'Users & Roles':
    st.title("🔐 User Management & RBAC")
    st.caption("Manage enterprise user credentials, role permissions, and access privileges.")

    t1, t2 = st.tabs(["Users List", "Create New User"])

    with t2:
        with st.form("create_user_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            name = col1.text_input("Full Name *")
            email = col2.text_input("Email Address *")

            col3, col4 = st.columns(2)
            pwd = col3.text_input("Password *", type="password")
            role = col4.selectbox("Role Assignment", list(ROLES.keys()))

            if st.form_submit_button("Create User", type="primary"):
                if not name.strip() or not email.strip() or not pwd:
                    st.error("Name, email, and password are required.")
                else:
                    conn = get_db()
                    try:
                        conn.execute("INSERT INTO users(name,email,password,role,created_at) VALUES(?,?,?,?,?)",
                                     (name.strip(), email.strip().lower(), generate_password_hash(pwd), role, now()))
                        conn.commit()
                        st.success(f"User '{name}' created with role '{role}'!")
                    except sqlite3.IntegrityError:
                        st.error(f"Email '{email}' is already registered.")
                    finally:
                        conn.close()

    with t1:
        conn = get_db()
        users = conn.execute("SELECT id,name,email,role,created_at FROM users ORDER BY id DESC").fetchall()
        conn.close()

        df_users = pd.DataFrame([{
            'ID': u['id'],
            'Name': u['name'],
            'Email': u['email'],
            'Role': u['role'],
            'Created': u['created_at'],
            'Session': '⭐ Current User' if u['id'] == user['id'] else ''
        } for u in users])
        st.dataframe(df_users, hide_index=True, use_container_width=True)

        st.divider()
        u_id = st.selectbox("Select User to Manage", [u['id'] for u in users], format_func=lambda x: f"{next(u['name'] for u in users if u['id'] == x)} ({next(u['role'] for u in users if u['id'] == x)})")
        if u_id:
            u_sel = next(u for u in users if u['id'] == u_id)
            col1, col2 = st.columns(2)
            with col1:
                with st.form(f"edit_u_{u_id}"):
                    st.write("##### Edit User")
                    un = st.text_input("Name", value=u_sel['name'])
                    ue = st.text_input("Email", value=u_sel['email'])
                    ur = st.selectbox("Role", list(ROLES.keys()), index=list(ROLES.keys()).index(u_sel['role']))
                    up = st.text_input("New Password (leave blank to keep current)", type="password")

                    if st.form_submit_button("Update User"):
                        conn = get_db()
                        # Guard against demoting only remaining Super Admin
                        if u_sel['role'] == 'Super Admin' and ur != 'Super Admin':
                            admin_cnt = conn.execute("SELECT COUNT(*) n FROM users WHERE role='Super Admin'").fetchone()['n']
                            if admin_cnt <= 1:
                                st.error("Cannot change role: System requires at least one Super Admin.")
                                conn.close()
                                st.stop()

                        try:
                            conn.execute("UPDATE users SET name=?,email=?,role=? WHERE id=?", (un.strip(), ue.strip().lower(), ur, u_id))
                            if up.strip():
                                conn.execute("UPDATE users SET password=? WHERE id=?", (generate_password_hash(up.strip()), u_id))
                            conn.commit()
                            if u_id == user['id']:
                                st.session_state.user['name'] = un.strip()
                                st.session_state.user['email'] = ue.strip().lower()
                                st.session_state.user['role'] = ur
                            st.success("User updated successfully!")
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("Email already in use.")
                        finally:
                            conn.close()

            with col2:
                st.write("##### Delete User")
                if u_id == user['id']:
                    st.info("You cannot delete your own logged-in account.")
                else:
                    if st.button("🗑️ Delete User Account", key=f"del_u_{u_id}"):
                        conn = get_db()
                        if u_sel['role'] == 'Super Admin':
                            admin_cnt = conn.execute("SELECT COUNT(*) n FROM users WHERE role='Super Admin'").fetchone()['n']
                            if admin_cnt <= 1:
                                st.error("Cannot delete the only remaining Super Admin account.")
                                conn.close()
                                st.stop()
                        conn.execute("DELETE FROM users WHERE id=?", (u_id,))
                        conn.commit()
                        conn.close()
                        st.success("User deleted!")
                        st.rerun()

# ==================== MODULE: REPORTS & ANALYTICS ====================
elif selected_module == 'Reports & Analytics':
    st.title("📈 Reports & Analytics")
    st.caption("Financial performance summaries, product turnover, and data exports.")

    conn = get_db()
    sales_cnt = conn.execute("SELECT COUNT(*) c, COALESCE(SUM(total),0) t FROM sales").fetchone()
    expenses_cnt = conn.execute("SELECT COUNT(*) c, COALESCE(SUM(amount),0) t FROM expenses").fetchone()
    products_cnt = conn.execute("SELECT COUNT(*) c, COALESCE(SUM(stock * purchase_price),0) v FROM products").fetchone()
    low_cnt = conn.execute("SELECT COUNT(*) c FROM products WHERE stock<=min_stock").fetchone()

    monthly_sales = {r['m']: r['t'] for r in conn.execute("SELECT substr(created_at,1,7) m, SUM(total) t FROM sales GROUP BY m").fetchall()}
    monthly_exp = {r['m']: r['t'] for r in conn.execute("SELECT substr(created_at,1,7) m, SUM(amount) t FROM expenses GROUP BY m").fetchall()}
    all_months = sorted(list(set(list(monthly_sales.keys()) + list(monthly_exp.keys()))), reverse=True)[:6]

    monthly_data = []
    for m in all_months:
        s_val = monthly_sales.get(m, 0.0)
        e_val = monthly_exp.get(m, 0.0)
        monthly_data.append({
            'Month': m,
            'Revenue (₹)': s_val,
            'Expenses (₹)': e_val,
            'Net Profit (₹)': s_val - e_val
        })

    top_prods = conn.execute("""
        SELECT COALESCE(p.name, 'Unknown') name, COALESCE(p.sku, '-') sku, SUM(si.qty) total_qty, SUM(si.qty * si.unit_price) total_rev
        FROM sale_items si
        LEFT JOIN products p ON p.id = si.product_id
        GROUP BY si.product_id
        ORDER BY total_qty DESC
        LIMIT 5
    """).fetchall()

    exp_cats = conn.execute("SELECT category, COUNT(*) count, SUM(amount) total FROM expenses GROUP BY category ORDER BY total DESC").fetchall()
    conn.close()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sales Orders", f"{sales_cnt['c']}", f"₹{sales_cnt['t']:,.2f} total")
    c2.metric("Expenses Logged", f"{expenses_cnt['c']}", f"₹{expenses_cnt['t']:,.2f} total")
    c3.metric("Inventory Asset Value", f"₹{products_cnt['v']:,.2f}", f"{products_cnt['c']} items")
    c4.metric("Low Stock Items", f"{low_cnt['c']}", "Requires reorder")

    st.write("")
    col_l, col_r = st.columns(2)

    with col_l:
        st.subheader("📅 Monthly Performance")
        if monthly_data:
            df_m = pd.DataFrame(monthly_data)
            st.dataframe(df_m.style.format({
                'Revenue (₹)': '₹{:,.2f}',
                'Expenses (₹)': '₹{:,.2f}',
                'Net Profit (₹)': '₹{:,.2f}'
            }), hide_index=True, use_container_width=True)
        else:
            st.info("No monthly transaction data available.")

    with col_r:
        st.subheader("🏆 Top Selling Products")
        if top_prods:
            df_top = pd.DataFrame([{
                'Product': r['name'],
                'SKU': r['sku'],
                'Units Sold': r['total_qty'],
                'Revenue': f"₹{r['total_rev']:,.2f}"
            } for r in top_prods])
            st.dataframe(df_top, hide_index=True, use_container_width=True)
        else:
            st.info("No sales transactions yet.")

    st.subheader("📊 Category-wise Expense Breakdown")
    if exp_cats:
        df_exp_cat = pd.DataFrame([dict(r) for r in exp_cats])
        fig_pie = px.pie(df_exp_cat, names="category", values="total",
                         color_discrete_sequence=px.colors.sequential.RdBu)
        fig_pie.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=300)
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("No expense categories recorded yet.")

    # Data Export Section
    st.divider()
    st.subheader("📥 Export System Data (CSV)")
    conn = get_db()
    df_sales_exp = pd.read_sql_query("SELECT * FROM sales", conn)
    df_inv_exp = pd.read_sql_query("SELECT * FROM products", conn)
    df_exp_exp = pd.read_sql_query("SELECT * FROM expenses", conn)
    conn.close()

    ex1, ex2, ex3 = st.columns(3)
    ex1.download_button("Download Sales Data (.csv)", df_sales_exp.to_csv(index=False), "sales_export.csv", "text/csv")
    ex2.download_button("Download Products (.csv)", df_inv_exp.to_csv(index=False), "products_export.csv", "text/csv")
    ex3.download_button("Download Expenses (.csv)", df_exp_exp.to_csv(index=False), "expenses_export.csv", "text/csv")
