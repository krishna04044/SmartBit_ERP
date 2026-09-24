# SmartBiz ERP — Enterprise Business Management System

A production-grade, modular Enterprise Resource Planning (ERP) platform built with Streamlit and styled in the **Limepress Fintech** design language.

---

## 📁 Project Architecture

```
smartbiz_erp/
│
├── streamlit_app.py          # Main application orchestrator, theme & router
│
├── database/
│   ├── db.py                 # SQLite connection pooling & seed initializers
│   └── schema.py             # DDL SQL schemas & sample catalog data
│
├── modules/
│   ├── dashboard.py          # Financial & inventory summary, AI sales forecast
│   ├── products.py           # Catalog master data, pricing & SKU management
│   ├── inventory.py          # Real-time stock levels, reorders & audit adjustments
│   ├── customers.py          # CRM directory, contact records & customer histories
│   ├── suppliers.py          # Vendor profiles, procurement contacts & directory
│   ├── sales.py              # Sales POS, live stock deduction & PDF invoices
│   ├── purchases.py          # Vendor POs, multi-item batch receiving & restocking
│   ├── expenses.py           # Operating expenditure logs & category breakdown
│   ├── finance.py            # Receivables, payables & cashflow metrics
│   ├── employees.py          # HR directory, payroll & department designations
│   ├── users.py              # RBAC administration, role privileges & passwords
│   └── reports.py            # Analytics charts, product turnover & CSV exports
│
├── utils/
│   ├── auth.py               # Role definitions, password hashing & login portal
│   └── pdf.py                # ReportLab commercial PDF invoice generation
│
├── assets/
│   └── logo.jpg              # High-energy brand logo emblem
│
├── smartbiz.db               # SQLite relational database
├── requirements.txt          # Python dependencies
└── README.md                 # System documentation
```

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.9+
- Virtual environment (recommended)

### 2. Installation
```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Launch Application
```bash
streamlit run streamlit_app.py
```
Open your browser at `http://localhost:8501`.

---

## 🔐 Default User Accounts (Role-Based Access)

| Role | Email | Password | Allowed Modules |
| :--- | :--- | :--- | :--- |
| **Super Admin** | `admin@smartbiz.com` | `admin123` | All 12 Modules + RBAC |
| **Business Admin** | `krishna@smartbiz.com` | `krishna123` | All Operations & Finance |
| **Finance Manager** | `finance@smartbiz.com` | `finance123` | Dashboard, Expenses, Finance, Reports |
| **Inventory Manager** | `inventory@smartbiz.com` | `inventory123` | Dashboard, Products, Inventory, Purchases, Reports |
| **Sales Manager** | `sales@smartbiz.com` | `sales123` | Dashboard, Customers, Sales, Reports |
| **HR Manager** | `hr@smartbiz.com` | `hr123` | Dashboard, Employees, Reports |

---

## 🎨 Design System: Limepress Fintech
- **Display Typography**: `Archivo Black` (weight 900, tight line-height)
- **Body & UI**: `Inter` (weight 600 default)
- **Numerals & Tables**: `JetBrains Mono`
- **Colors**:
  - Primary: `#0E0F0C` (Deep Onyx)
  - Accent / Primary CTA: `#9FE870` (Electric Lime)
  - Dark Green: `#163300`
  - Mint: `#E2F6D5`
  - Background Neutral: `#E8EBE6`
  - Surface: `#FFFFFF`
- **Cards & Depth**: 30px rounded corners with crisp 1px ring depth.
