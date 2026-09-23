# SmartBiz ERP

A Flask + SQLite ERP web application for a final-year project.

## Features
- Login and role-based access control
- Users & roles with edit/delete
- Products with edit/delete
- Inventory and low-stock alerts
- Customers with edit/delete
- Suppliers with edit/delete
- Sales with stock integration
- Invoice view, print and PDF generation
- Sales edit/delete (delete restores stock)
- Purchases with stock integration and edit/delete
- Expense tracking with edit/delete
- Finance dashboard
- Employees with edit/delete
- Reports and basic sales forecast endpoint

## Run
```bash
python -m venv venv
venv\\Scripts\\activate
pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5000

Demo login: admin@smartbiz.com / admin123

## Important
If you already have an older `smartbiz.db`, the updated application keeps that database. The new routes/templates work with the existing schema. For a clean demo, you can stop the server and delete `smartbiz.db`; restarting will create a fresh database with the demo administrator and sample products.
