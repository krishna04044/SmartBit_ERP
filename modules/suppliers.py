import streamlit as st
import pandas as pd
from database.db import get_db, now

def render_suppliers(user):
    st.title("Supplier Management")
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
                    conn.execute(
                        "INSERT INTO suppliers(name,phone,email,address,created_at) VALUES(?,?,?,?,?)",
                        (name.strip(), phone.strip(), email.strip(), address.strip(), now())
                    )
                    conn.commit()
                    conn.close()
                    st.success(f"Supplier '{name}' added successfully.")

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
                        st.write("##### Edit Supplier Details")
                        sn = st.text_input("Supplier Name", value=supp_sel['name'])
                        sp = st.text_input("Phone", value=supp_sel['phone'] or '')
                        se = st.text_input("Email", value=supp_sel['email'] or '')
                        sa = st.text_area("Address", value=supp_sel['address'] or '')
                        if st.form_submit_button("Update Supplier"):
                            conn = get_db()
                            conn.execute("UPDATE suppliers SET name=?,phone=?,email=?,address=? WHERE id=?", (sn.strip(), sp.strip(), se.strip(), sa.strip(), s_id))
                            conn.commit()
                            conn.close()
                            st.success("Supplier updated.")
                            st.rerun()
                with col2:
                    st.write("##### Delete Supplier")
                    st.caption("Past purchase records will be preserved without supplier link.")
                    if st.button("Delete Supplier", key=f"del_s_{s_id}"):
                        conn = get_db()
                        conn.execute("UPDATE purchases SET supplier_id=NULL WHERE supplier_id=?", (s_id,))
                        conn.execute("DELETE FROM suppliers WHERE id=?", (s_id,))
                        conn.commit()
                        conn.close()
                        st.success("Supplier deleted.")
                        st.rerun()
        else:
            st.info("No suppliers registered yet.")
