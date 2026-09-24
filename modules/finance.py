import streamlit as st
from database.db import get_db

def render_finance(user):
    st.title("Financial Overview")
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
        st.subheader("Accounts Receivable")
        st.markdown(f"### **₹{receivable:,.2f}**")
        st.caption("Total value of customer sales invoices with **Pending** status awaiting collection.")

    with c_pay:
        st.subheader("Accounts Payable")
        st.markdown(f"### **₹{payable:,.2f}**")
        st.caption("Total value of vendor purchase orders with **Pending** status awaiting settlement.")
