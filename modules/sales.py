import streamlit as st
import pandas as pd
from datetime import datetime
from database.db import get_db, now
from utils.pdf import generate_pdf_invoice

def render_sales(user):
    st.title("Sales & Invoicing")
    st.caption("Record customer sales, automatically deduct warehouse stock, and issue commercial invoices.")

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
                        st.error(f"Insufficient stock! Only {prod_rec['stock']} units available for {prod_rec['name']}.")
                    else:
                        total = round(qty * prod_rec['selling_price'], 2)
                        inv = 'INV-' + datetime.now().strftime('%Y%m%d%H%M%S%f')[:18]
                        cur = conn.execute(
                            "INSERT INTO sales(customer_id,invoice_no,total,payment_status,payment_method,created_at) VALUES(?,?,?,?,?,?)",
                            (cust_id, inv, total, status, method, now())
                        )
                        conn.execute(
                            "INSERT INTO sale_items(sale_id,product_id,qty,unit_price) VALUES(?,?,?,?)",
                            (cur.lastrowid, prod_rec['id'], qty, prod_rec['selling_price'])
                        )
                        conn.execute("UPDATE products SET stock=stock-? WHERE id=?", (qty, prod_rec['id']))
                        conn.commit()
                        st.success(f"Sale completed. Invoice #{inv} generated for ₹{total:,.2f}.")
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
                'Status': 'Paid' if s['payment_status'] == 'Paid' else 'Pending',
                'Method': s['payment_method'] or 'UPI',
                'Date': s['created_at']
            } for s in sales_records])
            st.dataframe(df_sales, hide_index=True, use_container_width=True)

            st.divider()
            sale_id = st.selectbox(
                "Select Sale to View Invoice & Actions",
                [s['id'] for s in sales_records],
                format_func=lambda x: f"Invoice #{next(s['invoice_no'] for s in sales_records if s['id'] == x)} — {next(s['customer'] or 'Walk-in' for s in sales_records if s['id'] == x)} (₹{next(s['total'] for s in sales_records if s['id'] == x):,.2f})"
            )

            if sale_id:
                s_item = next(s for s in sales_records if s['id'] == sale_id)
                conn = get_db()
                items = conn.execute(
                    "SELECT si.*, COALESCE(p.name, 'Discontinued Item') name, COALESCE(p.sku, '-') sku FROM sale_items si LEFT JOIN products p ON p.id=si.product_id WHERE si.sale_id=?",
                    (sale_id,)
                ).fetchall()
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
                    pdf_bytes = generate_pdf_invoice(s_item, items)
                    if pdf_bytes:
                        st.download_button(
                            label="Download Official PDF Invoice",
                            data=pdf_bytes,
                            file_name=f"{s_item['invoice_no']}.pdf",
                            mime="application/pdf",
                            type="primary",
                            use_container_width=True
                        )

                    st.write("---")
                    new_status = st.selectbox("Update Status", ["Paid", "Pending"], index=0 if s_item['payment_status'] == 'Paid' else 1, key=f"stat_{sale_id}")
                    if st.button("Save Payment Status", key=f"btn_stat_{sale_id}", use_container_width=True):
                        conn = get_db()
                        conn.execute("UPDATE sales SET payment_status=? WHERE id=?", (new_status, sale_id))
                        conn.commit()
                        conn.close()
                        st.success("Payment status updated.")
                        st.rerun()

                    if st.button("Delete Sale (Restore Stock)", key=f"del_sale_{sale_id}", use_container_width=True):
                        conn = get_db()
                        for it in items:
                            conn.execute("UPDATE products SET stock=stock+? WHERE id=?", (it['qty'], it['product_id']))
                        conn.execute("DELETE FROM sale_items WHERE sale_id=?", (sale_id,))
                        conn.execute("DELETE FROM sales WHERE id=?", (sale_id,))
                        conn.commit()
                        conn.close()
                        st.success("Sale deleted and stock restored.")
                        st.rerun()
        else:
            st.info("No sales orders recorded yet.")
