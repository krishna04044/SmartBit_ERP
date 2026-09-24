import streamlit as st
import pandas as pd
from datetime import datetime
from database.db import get_db, now

def render_inventory(user):
    st.title("Inventory & Restocking Hub")
    st.caption("Live stock positions, low-stock reorder alerts, and quick inventory replenishment.")

    conn = get_db()
    products = conn.execute("SELECT * FROM products ORDER BY stock ASC").fetchall()
    suppliers = conn.execute("SELECT * FROM suppliers ORDER BY name").fetchall()
    summary = conn.execute("SELECT COALESCE(SUM(stock * purchase_price),0) val, COALESCE(SUM(stock),0) items FROM products").fetchone()
    conn.close()

    low_stock_items = [p for p in products if p['stock'] <= p['min_stock']]
    out_of_stock_items = [p for p in products if p['stock'] <= 0]
    total_deficit = sum(max(0, p['min_stock'] - p['stock']) for p in products)
    restock_cost = sum(max(0, p['min_stock'] - p['stock']) * p['purchase_price'] for p in products)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Warehouse Asset Value", f"₹{summary['val']:,.2f}")
    m2.metric("Total Stocked Units", f"{summary['items']:,}")
    m3.metric("Low / Out-of-Stock", f"{len(low_stock_items)} items", delta=f"{len(out_of_stock_items)} depleted" if out_of_stock_items else "Stock Stable", delta_color="inverse" if low_stock_items else "normal")
    m4.metric("Restock Capital Req.", f"₹{restock_cost:,.2f}", delta=f"{total_deficit} units deficit" if total_deficit > 0 else "0 units", delta_color="inverse" if total_deficit > 0 else "normal")

    t1, t2, t3 = st.tabs(["Live Stock Positions", "Restock & Low Stock Alerts", "Quick Stock Adjustments"])

    with t1:
        if products:
            search_inv = st.text_input("Search inventory by name or SKU", key="inv_search")
            filtered_inv = [dict(p) for p in products if search_inv.lower() in p['name'].lower() or search_inv.lower() in p['sku'].lower() or search_inv.lower() in (p['category'] or '').lower()]

            df_inv = pd.DataFrame([{
                'SKU': p['sku'],
                'Product': p['name'],
                'Category': p['category'] or '-',
                'Warehouse': p['warehouse'],
                'Current Stock': p['stock'],
                'Min Alert': p['min_stock'],
                'Asset Value': f"₹{p['stock'] * p['purchase_price']:,.2f}",
                'Status': 'Out of Stock' if p['stock'] <= 0 else ('Reorder Needed' if p['stock'] <= p['min_stock'] else 'Optimal')
            } for p in filtered_inv])
            st.dataframe(df_inv, hide_index=True, use_container_width=True)
        else:
            st.info("No inventory items found.")

    with t2:
        st.subheader("Automated Restock Recommendations")
        st.caption("Items that have fallen below the minimum safety threshold and need immediate purchase orders.")

        if low_stock_items:
            # Bulk Restock Action
            col_b1, col_b2 = st.columns([2, 1])
            with col_b1:
                st.warning(f"**{len(low_stock_items)} products** require restocking to maintain safety buffers.")
            with col_b2:
                if st.button("Auto-Restock All Low Stock Items", type="primary", use_container_width=True):
                    conn = get_db()
                    po_batch = 'PO-AUTO-' + datetime.now().strftime('%Y%m%d%H%M%S')
                    batch_total = 0
                    cur = conn.execute("INSERT INTO purchases(supplier_id, po_no, total, payment_status, created_at) VALUES(?,?,?,?,?)",
                                       (None, po_batch, 0, 'Pending', now()))
                    po_id = cur.lastrowid

                    for p in low_stock_items:
                        reorder_qty = max(20, (p['min_stock'] - p['stock']) + 20)
                        item_cost = round(reorder_qty * p['purchase_price'], 2)
                        batch_total += item_cost
                        conn.execute("INSERT INTO purchase_items(purchase_id, product_id, qty, unit_price) VALUES(?,?,?,?)",
                                     (po_id, p['id'], reorder_qty, p['purchase_price']))
                        conn.execute("UPDATE products SET stock=stock+? WHERE id=?", (reorder_qty, p['id']))

                    conn.execute("UPDATE purchases SET total=? WHERE id=?", (batch_total, po_id))
                    conn.commit()
                    conn.close()
                    st.success(f"Successfully restocked {len(low_stock_items)} items. Batch PO #{po_batch} generated for ₹{batch_total:,.2f}.")
                    st.rerun()

            st.write("---")

            for p in low_stock_items:
                deficit = max(0, p['min_stock'] - p['stock'])
                rec_qty = max(10, deficit + 15)
                rec_cost = rec_qty * p['purchase_price']

                with st.expander(f"{'[OUT OF STOCK]' if p['stock'] <= 0 else '[LOW STOCK]'} {p['name']} ({p['sku']}) — Current: {p['stock']} units | Target Min: {p['min_stock']} units", expanded=True):
                    c1, c2, c3 = st.columns([1.2, 1.2, 1])
                    with c1:
                        st.write(f"**Category:** {p['category'] or 'General'}")
                        st.write(f"**Unit Buy Price:** ₹{p['purchase_price']:,.2f}")
                        st.write(f"**Stock Deficit:** `{deficit} units` below minimum")
                    with c2:
                        st.write(f"**Recommended Order:** `{rec_qty} units`")
                        st.write(f"**Estimated Capital:** `₹{rec_cost:,.2f}`")
                        st.write(f"**Warehouse:** {p['warehouse']}")
                    with c3:
                        st.write("##### Quick Restock")
                        q_input = st.number_input(f"Quantity to Restock", min_value=1, value=rec_qty, key=f"rec_qty_{p['id']}")
                        s_choice = st.selectbox(
                            "Supplier",
                            [None] + [s['id'] for s in suppliers],
                            format_func=lambda x: "Direct Supplier" if x is None else next(s['name'] for s in suppliers if s['id'] == x),
                            key=f"rec_sup_{p['id']}"
                        )
                        if st.button(f"Restock {p['name']}", key=f"btn_restock_{p['id']}", type="primary"):
                            conn = get_db()
                            item_total = round(q_input * p['purchase_price'], 2)
                            po_num = 'PO-QUICK-' + datetime.now().strftime('%Y%m%d%H%M%S%f')[:18]
                            cur = conn.execute("INSERT INTO purchases(supplier_id, po_no, total, payment_status, created_at) VALUES(?,?,?,?,?)",
                                               (s_choice, po_num, item_total, 'Pending', now()))
                            conn.execute("INSERT INTO purchase_items(purchase_id, product_id, qty, unit_price) VALUES(?,?,?,?)",
                                         (cur.lastrowid, p['id'], q_input, p['purchase_price']))
                            conn.execute("UPDATE products SET stock=stock+? WHERE id=?", (q_input, p['id']))
                            conn.commit()
                            conn.close()
                            st.success(f"Restocked {q_input} units of {p['name']}. PO #{po_num} recorded.")
                            st.rerun()
        else:
            st.success("All product inventory levels are currently above minimum safety thresholds.")

    with t3:
        st.subheader("Manual Stock Adjustment & Audit")
        st.caption("Apply direct adjustments for cycle counts, damaged scrap, or emergency replenishment.")

        if products:
            with st.form("quick_stock_adjust_form", clear_on_submit=True):
                p_adj_id = st.selectbox(
                    "Select Product",
                    [p['id'] for p in products],
                    format_func=lambda x: f"{next(p['name'] for p in products if p['id'] == x)} (SKU: {next(p['sku'] for p in products if p['id'] == x)}, Current Stock: {next(p['stock'] for p in products if p['id'] == x)})"
                )
                adj_type = st.radio("Adjustment Type", ["Add Stock (Restock / Found Units)", "Reduce Stock (Damaged / Discrepancy / Write-off)"], horizontal=True)
                adj_units = st.number_input("Quantity of Units", min_value=1, value=5, step=1)
                adj_reason = st.text_input("Adjustment Reason / Audit Note", placeholder="e.g. Received extra vendor units / Physical inventory audit")

                if st.form_submit_button("Apply Stock Adjustment", type="primary"):
                    conn = get_db()
                    cur_stock = conn.execute("SELECT stock, name FROM products WHERE id=?", (p_adj_id,)).fetchone()
                    if "Add Stock" in adj_type:
                        new_stock = cur_stock['stock'] + adj_units
                        conn.execute("UPDATE products SET stock=? WHERE id=?", (new_stock, p_adj_id))
                        st.success(f"Added {adj_units} units to '{cur_stock['name']}'. New stock: {new_stock}")
                    else:
                        new_stock = max(0, cur_stock['stock'] - adj_units)
                        conn.execute("UPDATE products SET stock=? WHERE id=?", (new_stock, p_adj_id))
                        st.warning(f"Reduced {adj_units} units from '{cur_stock['name']}'. New stock: {new_stock}")
                    conn.commit()
                    conn.close()
                    st.rerun()
