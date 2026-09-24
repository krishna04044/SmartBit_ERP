import streamlit as st
import pandas as pd
from datetime import datetime
from database.db import get_db, now

def render_purchases(user):
    st.title("Purchases & Restocking")
    st.caption("Receive stock shipments from suppliers and automatically increment inventory levels.")

    t1, t2, t3 = st.tabs(["Purchase History", "Receive Single Shipment", "Multi-Item Supplier Restock"])

    conn = get_db()
    products = conn.execute("SELECT * FROM products ORDER BY name").fetchall()
    suppliers = conn.execute("SELECT * FROM suppliers ORDER BY name").fetchall()
    conn.close()

    with t2:
        if not products:
            st.warning("Please add products before receiving purchases.")
        else:
            with st.form("create_po_form", clear_on_submit=True):
                st.subheader("Receive Stock Shipment")
                s_opts = [None] + [s['id'] for s in suppliers]
                supp_id = st.selectbox("Supplier", s_opts, format_func=lambda x: "Direct Purchase / Unknown" if x is None else next(s['name'] for s in suppliers if s['id'] == x))

                prod_opts = [p['id'] for p in products]
                p_id = st.selectbox("Product to Restock", prod_opts, format_func=lambda x: f"{next(p['name'] for p in products if p['id'] == x)} — Buy: ₹{next(p['purchase_price'] for p in products if p['id'] == x):,.2f} (Current Stock: {next(p['stock'] for p in products if p['id'] == x)})")

                col1, col2 = st.columns(2)
                qty = col1.number_input("Units Received", min_value=1, value=10, step=1)
                status = col2.selectbox("Payment Status", ["Pending", "Paid"])

                if st.form_submit_button("Receive Stock", type="primary"):
                    conn = get_db()
                    p_rec = conn.execute("SELECT * FROM products WHERE id=?", (p_id,)).fetchone()
                    total = round(qty * p_rec['purchase_price'], 2)
                    po = 'PO-' + datetime.now().strftime('%Y%m%d%H%M%S%f')[:18]

                    cur = conn.execute(
                        "INSERT INTO purchases(supplier_id,po_no,total,payment_status,created_at) VALUES(?,?,?,?,?)",
                        (supp_id, po, total, status, now())
                    )
                    conn.execute(
                        "INSERT INTO purchase_items(purchase_id,product_id,qty,unit_price) VALUES(?,?,?,?)",
                        (cur.lastrowid, p_rec['id'], qty, p_rec['purchase_price'])
                    )
                    conn.execute("UPDATE products SET stock=stock+? WHERE id=?", (qty, p_rec['id']))
                    conn.commit()
                    conn.close()
                    st.success(f"Stock received. Purchase Order #{po} recorded for ₹{total:,.2f}.")
                    st.rerun()

    with t3:
        st.subheader("Multi-Item Supplier Restock Order")
        st.caption("Create a combined purchase order with multiple items from a single supplier.")

        if not products:
            st.warning("No products available to restock.")
        else:
            m_supp_id = st.selectbox(
                "Select Supplier for PO",
                [s['id'] for s in suppliers] if suppliers else [None],
                format_func=lambda x: "Direct Purchase / General Vendor" if not suppliers or x is None else next(s['name'] for s in suppliers if s['id'] == x),
                key="multi_restock_supp"
            )

            selected_products = st.multiselect(
                "Select Products to Restock in this PO",
                [p['id'] for p in products],
                format_func=lambda x: f"{next(p['name'] for p in products if p['id'] == x)} (Stock: {next(p['stock'] for p in products if p['id'] == x)}, Buy: ₹{next(p['purchase_price'] for p in products if p['id'] == x):,.2f})",
                key="multi_restock_prods"
            )

            if selected_products:
                order_quantities = {}
                est_total = 0.0
                st.write("##### Order Line Items")
                cols = st.columns(len(selected_products) if len(selected_products) <= 3 else 3)
                for idx, pid in enumerate(selected_products):
                    p_obj = next(p for p in products if p['id'] == pid)
                    with cols[idx % 3]:
                        def_rec = max(10, (p_obj['min_stock'] - p_obj['stock']) + 15) if p_obj['stock'] <= p_obj['min_stock'] else 10
                        q = st.number_input(f"Units for {p_obj['name']}", min_value=1, value=def_rec, step=1, key=f"multi_q_{pid}")
                        order_quantities[pid] = q
                        est_total += q * p_obj['purchase_price']

                st.write(f"### **Estimated Purchase Order Total: ₹{est_total:,.2f}**")
                po_pay_status = st.selectbox("PO Payment Status", ["Pending", "Paid"], key="multi_po_status")

                if st.button("Confirm & Issue Multi-Item PO", type="primary", use_container_width=True):
                    conn = get_db()
                    po_batch_no = 'PO-BULK-' + datetime.now().strftime('%Y%m%d%H%M%S')
                    cur = conn.execute(
                        "INSERT INTO purchases(supplier_id, po_no, total, payment_status, created_at) VALUES(?,?,?,?,?)",
                        (m_supp_id, po_batch_no, est_total, po_pay_status, now())
                    )
                    po_created_id = cur.lastrowid

                    for pid, qty_val in order_quantities.items():
                        p_info = next(p for p in products if p['id'] == pid)
                        conn.execute(
                            "INSERT INTO purchase_items(purchase_id, product_id, qty, unit_price) VALUES(?,?,?,?)",
                            (po_created_id, pid, qty_val, p_info['purchase_price'])
                        )
                        conn.execute("UPDATE products SET stock=stock+? WHERE id=?", (qty_val, pid))

                    conn.commit()
                    conn.close()
                    st.success(f"Batch Purchase Order #{po_batch_no} created successfully for ₹{est_total:,.2f}. Warehouse inventory updated.")
                    st.rerun()

    with t1:
        conn = get_db()
        po_records = conn.execute("SELECT p.*, s.name supplier FROM purchases p LEFT JOIN suppliers s ON s.id=p.supplier_id ORDER BY p.id DESC LIMIT 50").fetchall()
        conn.close()

        if po_records:
            df_po = pd.DataFrame([{
                'ID': p['id'],
                'PO #': p['po_no'],
                'Supplier': p['supplier'] or 'Direct Purchase',
                'Total Cost': f"₹{p['total']:,.2f}",
                'Status': 'Paid' if p['payment_status'] == 'Paid' else 'Pending',
                'Received Date': p['created_at']
            } for p in po_records])
            st.dataframe(df_po, hide_index=True, use_container_width=True)

            st.divider()
            po_id = st.selectbox(
                "Select PO to Manage",
                [p['id'] for p in po_records],
                format_func=lambda x: f"{next(p['po_no'] for p in po_records if p['id'] == x)} — {next(p['supplier'] or 'Direct' for p in po_records if p['id'] == x)} (₹{next(p['total'] for p in po_records if p['id'] == x):,.2f})"
            )
            if po_id:
                po_sel = next(p for p in po_records if p['id'] == po_id)
                col1, col2 = st.columns(2)
                with col1:
                    new_st = st.selectbox("Update Status", ["Pending", "Paid"], index=0 if po_sel['payment_status'] == 'Pending' else 1, key=f"po_st_{po_id}")
                    if st.button("Save PO Status", key=f"btn_po_st_{po_id}"):
                        conn = get_db()
                        conn.execute("UPDATE purchases SET payment_status=? WHERE id=?", (new_st, po_id))
                        conn.commit()
                        conn.close()
                        st.success("PO payment status updated.")
                        st.rerun()
                with col2:
                    st.caption("Reverses received quantities from warehouse inventory.")
                    if st.button("Delete Purchase (Reverse Stock)", key=f"del_po_{po_id}"):
                        conn = get_db()
                        items = conn.execute("SELECT * FROM purchase_items WHERE purchase_id=?", (po_id,)).fetchall()
                        for it in items:
                            conn.execute("UPDATE products SET stock=MAX(0, stock-?) WHERE id=?", (it['qty'], it['product_id']))
                        conn.execute("DELETE FROM purchase_items WHERE purchase_id=?", (po_id,))
                        conn.execute("DELETE FROM purchases WHERE id=?", (po_id,))
                        conn.commit()
                        conn.close()
                        st.success("Purchase deleted and inventory reversed.")
                        st.rerun()
        else:
            st.info("No purchase orders recorded yet.")
