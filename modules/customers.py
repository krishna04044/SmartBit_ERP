import streamlit as st
import pandas as pd
from database.db import get_db, now

def render_customers(user):
    st.title("Customer Relations (CRM)")
    st.caption("Manage customer directory, contact details, and account histories.")

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
                    conn.execute(
                        "INSERT INTO customers(name,phone,email,address,created_at) VALUES(?,?,?,?,?)",
                        (name.strip(), phone.strip(), email.strip(), address.strip(), now())
                    )
                    conn.commit()
                    conn.close()
                    st.success(f"Customer '{name}' registered successfully.")

    with t1:
        conn = get_db()
        customers = conn.execute("SELECT * FROM customers ORDER BY id DESC").fetchall()
        conn.close()

        if customers:
            search = st.text_input("Search customers by name, phone, or email", "")
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
                        st.write("##### Edit Customer Details")
                        en = st.text_input("Name", value=cust_sel['name'])
                        ep = st.text_input("Phone", value=cust_sel['phone'] or '')
                        ee = st.text_input("Email", value=cust_sel['email'] or '')
                        ea = st.text_area("Address", value=cust_sel['address'] or '')
                        if st.form_submit_button("Update Customer"):
                            conn = get_db()
                            conn.execute("UPDATE customers SET name=?,phone=?,email=?,address=? WHERE id=?", (en.strip(), ep.strip(), ee.strip(), ea.strip(), c_id))
                            conn.commit()
                            conn.close()
                            st.success("Customer record updated.")
                            st.rerun()
                with col2:
                    st.write("##### Delete Customer")
                    st.caption("Historical sales invoices will be preserved as walk-in orders.")
                    if st.button("Delete Customer", key=f"del_c_{c_id}"):
                        conn = get_db()
                        conn.execute("UPDATE sales SET customer_id=NULL WHERE customer_id=?", (c_id,))
                        conn.execute("DELETE FROM customers WHERE id=?", (c_id,))
                        conn.commit()
                        conn.close()
                        st.success("Customer deleted.")
                        st.rerun()
        else:
            st.info("No customers registered yet.")
