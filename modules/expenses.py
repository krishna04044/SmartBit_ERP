import streamlit as st
import pandas as pd
from database.db import get_db, now

def render_expenses(user):
    st.title("Expense Tracking")
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
                conn.execute(
                    "INSERT INTO expenses(category,description,amount,payment_method,created_at) VALUES(?,?,?,?,?)",
                    (cat, desc.strip(), amt, method, now())
                )
                conn.commit()
                conn.close()
                st.success("Expense recorded successfully.")
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
            e_id = st.selectbox(
                "Select Expense to Manage",
                [e['id'] for e in expenses],
                format_func=lambda x: f"ID {x}: {next(e['category'] for e in expenses if e['id'] == x)} — ₹{next(e['amount'] for e in expenses if e['id'] == x):,.2f}"
            )
            if e_id:
                exp_sel = next(e for e in expenses if e['id'] == e_id)
                col1, col2 = st.columns(2)
                with col1:
                    with st.form(f"edit_exp_{e_id}"):
                        st.write("##### Edit Expense Details")
                        cats = ["Salary", "Rent", "Electricity", "Marketing", "Transportation", "Equipment", "Other"]
                        ecat = st.selectbox("Category", cats, index=cats.index(exp_sel['category']) if exp_sel['category'] in cats else 0)
                        edesc = st.text_input("Description", value=exp_sel['description'] or '')
                        eamt = st.number_input("Amount (₹)", value=float(exp_sel['amount']))
                        methods = ["UPI", "Cash", "Card", "Bank Transfer"]
                        emeth = st.selectbox("Method", methods, index=methods.index(exp_sel['payment_method']) if exp_sel['payment_method'] in methods else 0)
                        if st.form_submit_button("Update Expense"):
                            conn = get_db()
                            conn.execute("UPDATE expenses SET category=?,description=?,amount=?,payment_method=? WHERE id=?", (ecat, edesc.strip(), eamt, emeth, e_id))
                            conn.commit()
                            conn.close()
                            st.success("Expense updated.")
                            st.rerun()
                with col2:
                    st.write("##### Delete Expense")
                    if st.button("Delete Expense Entry", key=f"del_exp_{e_id}"):
                        conn = get_db()
                        conn.execute("DELETE FROM expenses WHERE id=?", (e_id,))
                        conn.commit()
                        conn.close()
                        st.success("Expense deleted.")
                        st.rerun()
        else:
            st.info("No expenses recorded yet.")
