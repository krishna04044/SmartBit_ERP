import streamlit as st
import sqlite3
import pandas as pd
from werkzeug.security import generate_password_hash
from database.db import get_db, now
from utils.auth import ROLES

def render_users(user):
    st.title("User Management & RBAC")
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
                        conn.execute(
                            "INSERT INTO users(name,email,password,role,created_at) VALUES(?,?,?,?,?)",
                            (name.strip(), email.strip().lower(), generate_password_hash(pwd), role, now())
                        )
                        conn.commit()
                        st.success(f"User '{name}' created with role '{role}'.")
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
            'Session': 'Current User' if u['id'] == user['id'] else ''
        } for u in users])
        st.dataframe(df_users, hide_index=True, use_container_width=True)

        st.divider()
        u_id = st.selectbox(
            "Select User to Manage",
            [u['id'] for u in users],
            format_func=lambda x: f"{next(u['name'] for u in users if u['id'] == x)} ({next(u['role'] for u in users if u['id'] == x)})"
        )
        if u_id:
            u_sel = next(u for u in users if u['id'] == u_id)
            col1, col2 = st.columns(2)
            with col1:
                with st.form(f"edit_u_{u_id}"):
                    st.write("##### Edit User Details")
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
                            st.success("User updated successfully.")
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
                    if st.button("Delete User Account", key=f"del_u_{u_id}"):
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
                        st.success("User deleted.")
                        st.rerun()
