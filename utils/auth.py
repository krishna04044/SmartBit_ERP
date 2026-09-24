import streamlit as st
from werkzeug.security import check_password_hash
from database.db import get_db

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

def get_current_user():
    """Retrieve logged-in user from session_state or None."""
    return st.session_state.get('user', None)

def login_user(email, password):
    """Authenticate user with database hashed password."""
    conn = get_db()
    u = conn.execute("SELECT * FROM users WHERE email=?", (email.strip().lower(),)).fetchone()
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
    """Clear user session and rerun."""
    st.session_state.user = None
    if 'current_module' in st.session_state:
        del st.session_state['current_module']
    st.rerun()

def render_login(logo_b64=""):
    """Render the high-end Limepress Fintech styled login screen."""
    st.html("""
    <style>
    .stApp {
      background-color: #e8ebe6 !important;
    }

    .login-card {
      background: #ffffff;
      border: 1px solid rgba(14,15,12,0.12);
      box-shadow: rgba(14,15,12,0.12) 0 0 0 1px;
      border-radius: 30px;
      padding: 40px 36px 32px 36px;
      position: relative;
    }

    .login-badge {
      display: inline-block;
      background: #9fe870;
      color: #163300;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.72rem;
      font-weight: 700;
      letter-spacing: 0.08em;
      padding: 4px 14px;
      border-radius: 9999px;
      margin-bottom: 14px;
      text-transform: uppercase;
    }

    .login-title {
      font-family: 'Archivo Black', sans-serif;
      font-size: 3.4rem;
      font-weight: 900;
      color: #0e0f0c;
      line-height: 0.85;
      letter-spacing: 0;
      margin-bottom: 8px;
    }

    .login-sub {
      color: #454745;
      font-family: 'Inter', sans-serif;
      font-size: 0.92rem;
      font-weight: 600;
      margin-bottom: 24px;
      letter-spacing: 0.01em;
    }

    [data-testid="stForm"] {
      background: transparent !important;
      border: none !important;
      box-shadow: none !important;
      padding: 0 !important;
    }

    [data-testid="stForm"] label {
      color: #454745 !important;
      font-family: 'Inter', sans-serif !important;
      font-size: 0.8rem !important;
      font-weight: 600 !important;
      text-transform: uppercase !important;
      letter-spacing: 0.04em !important;
    }

    [data-testid="stForm"] input {
      background-color: #ffffff !important;
      border: 1px solid rgba(14,15,12,0.12) !important;
      box-shadow: rgba(14,15,12,0.12) 0 0 0 1px !important;
      border-radius: 16px !important;
      color: #0e0f0c !important;
      font-family: 'Inter', sans-serif !important;
      font-size: 0.95rem !important;
      font-weight: 600 !important;
      height: 48px !important;
      padding-left: 14px !important;
      transition: border-color 0.2s !important;
    }

    [data-testid="stForm"] input:focus {
      border-color: #9fe870 !important;
      box-shadow: 0 0 0 2px #9fe870 !important;
    }

    [data-testid="stFormSubmitButton"] button {
      background-color: #9fe870 !important;
      color: #163300 !important;
      border: none !important;
      border-radius: 9999px !important;
      font-family: 'Inter', sans-serif !important;
      font-weight: 600 !important;
      font-size: 0.95rem !important;
      letter-spacing: 0.02em !important;
      height: 48px !important;
      width: 100% !important;
      margin-top: 20px !important;
      cursor: pointer !important;
      transition: transform 180ms cubic-bezier(0.25, 0.46, 0.45, 0.94), background-color 180ms ease !important;
    }
    [data-testid="stFormSubmitButton"] button:hover {
      background-color: rgba(159, 232, 112, 0.92) !important;
      color: #163300 !important;
      transform: scale(1.05) !important;
      box-shadow: 0 4px 20px -8px rgba(159, 232, 112, 0.4) !important;
    }

    .login-remember-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-top: 6px;
    }
    .login-remember-row span {
      color: #454745;
      font-family: 'Inter', sans-serif;
      font-size: 0.8rem;
      font-weight: 500;
    }
    .login-remember-row a {
      color: #0e0f0c;
      font-family: 'Inter', sans-serif;
      font-size: 0.8rem;
      text-decoration: underline;
      font-weight: 600;
    }

    .login-creds-strip {
      margin-top: 20px;
      padding: 16px 20px;
      background: #ffffff;
      border: 1px solid rgba(14,15,12,0.12);
      box-shadow: rgba(14,15,12,0.12) 0 0 0 1px;
      border-radius: 20px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.78rem;
      color: #454745;
    }
    .login-creds-strip strong { color: #0e0f0c; }
    </style>
    """)

    col1, col2, col3 = st.columns([1, 1.4, 1])
    with col2:
        logo_html = f"<div style='text-align:center; margin-bottom:16px;'><img src='data:image/jpeg;base64,{logo_b64}' style='width:104px; height:104px; border-radius:26px; border:2.5px solid #9fe870; box-shadow:0 0 28px rgba(159,232,112,0.4); object-fit:cover;' /></div>" if logo_b64 else ""
        st.markdown(f"""
        <div class='login-card'>
          {logo_html}
          <div class='login-badge'>SmartBiz ERP</div>
          <div class='login-title'>SIGN<br>IN</div>
          <div class='login-sub'>Enterprise Resource Planning Platform</div>
        </div>
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            email = st.text_input("Email Address", value="admin@smartbiz.com", placeholder="admin@smartbiz.com")
            password = st.text_input("Password", type="password", value="admin123", placeholder="••••••••")

            st.html("""
            <div class='login-remember-row'>
              <span>Secure enterprise authentication</span>
              <a href='#'>Forgot password?</a>
            </div>
            """)

            submit = st.form_submit_button("Sign In")

            if submit:
                if login_user(email, password):
                    st.success("Authentication successful. Redirecting to workspace...")
                    st.rerun()
                else:
                    st.error("Invalid email or password. Access denied.")

        st.html("""
        <div class='login-creds-strip'>
          <div style='font-weight:700; color:#163300; margin-bottom:6px;'>DEMO ACCOUNTS (ROLE-BASED):</div>
          • <strong>admin@smartbiz.com</strong> / admin123 (Super Admin)<br>
          • <strong>krishna@smartbiz.com</strong> / krishna123 (Business Admin)<br>
          • <strong>finance@smartbiz.com</strong> / finance123 (Finance Manager)<br>
          • <strong>inventory@smartbiz.com</strong> / inventory123 (Inventory Manager)<br>
          • <strong>sales@smartbiz.com</strong> / sales123 (Sales Manager)<br>
          • <strong>hr@smartbiz.com</strong> / hr123 (HR Manager)
        </div>
        """)
