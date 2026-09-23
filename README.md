# SmartBiz ERP

An Enterprise Resource Planning (ERP) web application built with **Streamlit** (and Flask) + SQLite for business management.

## Features
- **Authentication & RBAC**: Login and 9 fine-grained organizational roles (Super Admin, Business Admin, Managers, Staff).
- **Dashboard**: Live financial KPIs, interactive Plotly monthly sales trends, low-stock alerts, recent sales, and AI sales forecasting.
- **Products Catalog**: Product master data with SKU uniqueness, category filters, buy/sell pricing, and safe deletion protection.
- **Inventory Tracking**: Live stock valuation (`stock * purchase_price`), total stocked units, and reorder status badges.
- **Customers CRM**: Customer contact directory, search, and historic invoice preservation.
- **Suppliers**: Procurement vendor directory and order tracking.
- **Sales & Invoicing**: Sales order recording, automatic inventory deduction, and **instant downloadable PDF invoices** (ReportLab).
- **Purchases & Restocking**: Restock purchase orders with automated stock increment and reversal.
- **Expense Tracking**: Categorized operational expense tracking with summary breakdowns.
- **Finance**: Corporate cashflow, Accounts Receivable (uncollected sales), and Accounts Payable (pending vendor POs).
- **Employees & HR**: Staff directory, department organization, designations, and payroll.
- **Users & Roles**: User management, hashed credentials, and admin lockout protections.
- **Reports & Analytics**: Monthly performance comparisons, top-selling products, and one-click CSV data exports.

## How to Run with Streamlit (Recommended)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the Streamlit application
streamlit run streamlit_app.py
```
Open **http://localhost:8501** in your browser.

### Demo Administrator Credentials
- **Email**: `admin@smartbiz.com`
- **Password**: `admin123`

---

## Alternative: Run with Flask

```bash
python app.py
```
Open **http://localhost:5000** in your browser.

## Database Note
The application uses SQLite (`smartbiz.db`). All products, sales, purchases, and user accounts are automatically persisted and shared seamlessly between the Streamlit and Flask interfaces.
