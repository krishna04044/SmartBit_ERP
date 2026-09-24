import streamlit as st
import sqlite3
import pandas as pd
import base64
from database.db import get_db, now

def render_products(user):
    st.title("Products Catalog")
    st.caption("Manage product master data, pricing, product imagery, inventory stock thresholds, and warehouses.")

    t1, t2 = st.tabs(["Catalog List & Visual Gallery", "Add New Product"])

    with t2:
        st.subheader("New Product Entry")
        with st.form("add_product_form", clear_on_submit=True):
            c_left, c_right = st.columns([1.5, 1])

            with c_left:
                col1, col2 = st.columns(2)
                sku = col1.text_input("SKU Code *", placeholder="e.g. KB-002")
                name = col2.text_input("Product Name *", placeholder="e.g. Ergonomic Keyboard")

                col3, col4 = st.columns(2)
                category = col3.text_input("Category", placeholder="e.g. Accessories")
                warehouse = col4.text_input("Warehouse Location", value="Main Warehouse")

                col5, col6, col7, col8 = st.columns(4)
                buy_price = col5.number_input("Purchase Price (₹)", min_value=0.0, step=10.0, value=0.0)
                sell_price = col6.number_input("Selling Price (₹)", min_value=0.0, step=10.0, value=0.0)
                stock = col7.number_input("Initial Stock", min_value=0, step=1, value=10)
                min_stock = col8.number_input("Min Reorder Level", min_value=0, step=1, value=5)

            with c_right:
                st.write("##### Product Photography")
                uploaded_img = st.file_uploader("Upload Product Image", type=["png", "jpg", "jpeg", "webp"], key="new_prod_file_upload")
                if uploaded_img:
                    img_bytes = uploaded_img.read()
                    mime_type = uploaded_img.type or "image/jpeg"
                    b64_str = f"data:{mime_type};base64," + base64.b64encode(img_bytes).decode('utf-8')
                    st.markdown(f"""
                    <div style='text-align:center; padding:8px; background:#ffffff; border:1.5px solid rgba(14,15,12,0.12); border-radius:18px; box-shadow:0 2px 8px -2px rgba(14,15,12,0.06);'>
                      <img src='{b64_str}' style='max-height:140px; max-width:100%; border-radius:12px; object-fit:contain;' />
                      <div style='font-family:"JetBrains Mono",monospace; font-size:0.7rem; color:#555754; margin-top:6px;'>Preview: {uploaded_img.name}</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    b64_str = None
                    st.markdown("""
                    <div style='border:1.5px dashed rgba(14,15,12,0.2); border-radius:18px; padding:28px 16px; text-align:center; background:#ffffff;'>
                      <div style='font-family:"JetBrains Mono",monospace; font-size:0.8rem; color:#787a77; font-weight:600;'>No image uploaded</div>
                      <div style='font-size:0.75rem; color:#555754; margin-top:4px;'>Supports PNG, JPG, WEBP</div>
                    </div>
                    """, unsafe_allow_html=True)

            submit = st.form_submit_button("Add Product to Catalog", type="primary")

            if submit:
                if not sku.strip() or not name.strip():
                    st.error("SKU and Product Name are required fields.")
                else:
                    conn = get_db()
                    try:
                        conn.execute(
                            "INSERT INTO products(sku,name,category,purchase_price,selling_price,stock,min_stock,warehouse,image_data,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
                            (sku.strip(), name.strip(), category.strip(), buy_price, sell_price, stock, min_stock, warehouse.strip(), b64_str, now())
                        )
                        conn.commit()
                        st.success(f"Product '{name}' added successfully with photo.")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error(f"A product with SKU '{sku}' already exists.")
                    finally:
                        conn.close()

    with t1:
        conn = get_db()
        products = conn.execute("SELECT * FROM products ORDER BY id DESC").fetchall()
        conn.close()

        if products:
            c_search, c_view = st.columns([3, 1])
            search = c_search.text_input("Search products by name, SKU, or category", "", key="prod_search_input")
            view_mode = c_view.radio("View Layout", ["Gallery Grid", "Data Table"], horizontal=True, label_visibility="collapsed")

            filtered = [dict(p) for p in products if search.lower() in p['name'].lower() or search.lower() in p['sku'].lower() or search.lower() in (p['category'] or '').lower()]

            if view_mode == "Gallery Grid":
                # Visual Product Card Gallery
                cols = st.columns(3)
                for idx, p in enumerate(filtered):
                    with cols[idx % 3]:
                        status_color = "#fee2e2" if p['stock'] <= 0 else ("#fef3c7" if p['stock'] <= p['min_stock'] else "#e2f6d5")
                        status_text_color = "#991b1b" if p['stock'] <= 0 else ("#92400e" if p['stock'] <= p['min_stock'] else "#163300")
                        status_label = "Out of Stock" if p['stock'] <= 0 else ("Low Stock" if p['stock'] <= p['min_stock'] else "In Stock")

                        img_tag = f"<img src='{p['image_data']}' style='width:100%; height:160px; object-fit:cover; border-radius:14px;' />" if p.get('image_data') else "<div style='height:160px; width:100%; background:#ebeee8; border-radius:14px; display:flex; align-items:center; justify-content:center; color:#787a77; font-family:\"JetBrains Mono\",monospace; font-size:0.8rem; font-weight:700;'>NO IMAGE</div>"

                        st.markdown(f"""
                        <div style='background:#ffffff; border:1.5px solid rgba(14,15,12,0.12); border-radius:20px; padding:16px; box-shadow:0 3px 12px -2px rgba(14,15,12,0.06); margin-bottom:18px;'>
                          {img_tag}
                          <div style='display:flex; justify-content:space-between; align-items:flex-start; margin-top:12px;'>
                            <div>
                              <div style='font-family:"Archivo Black",sans-serif; font-size:1.1rem; color:#0e0f0c; line-height:1.1;'>{p['name']}</div>
                              <div style='font-family:"JetBrains Mono",monospace; font-size:0.75rem; color:#555754; margin-top:2px;'>SKU: {p['sku']} | {p['category'] or 'General'}</div>
                            </div>
                            <span style='background:{status_color}; color:{status_text_color}; font-family:"JetBrains Mono",monospace; font-size:0.65rem; font-weight:700; padding:3px 8px; border-radius:9999px; text-transform:uppercase;'>{status_label}</span>
                          </div>
                          <div style='display:flex; justify-content:space-between; align-items:center; margin-top:12px; padding-top:10px; border-top:1px solid rgba(14,15,12,0.08);'>
                            <div>
                              <div style='font-family:"JetBrains Mono",monospace; font-size:0.65rem; color:#787a77; text-transform:uppercase;'>Selling Price</div>
                              <div style='font-family:"Archivo Black",sans-serif; font-size:1.15rem; color:#0e0f0c;'>₹{p['selling_price']:,.2f}</div>
                            </div>
                            <div style='text-align:right;'>
                              <div style='font-family:"JetBrains Mono",monospace; font-size:0.65rem; color:#787a77; text-transform:uppercase;'>Stock</div>
                              <div style='font-family:"JetBrains Mono",monospace; font-size:0.95rem; font-weight:700; color:#0e0f0c;'>{p['stock']} units</div>
                            </div>
                          </div>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                df_prod = pd.DataFrame([{
                    'ID': p['id'],
                    'SKU': p['sku'],
                    'Product Name': p['name'],
                    'Category': p['category'] or '-',
                    'Buy Price': f"₹{p['purchase_price']:,.2f}",
                    'Sell Price': f"₹{p['selling_price']:,.2f}",
                    'Stock': p['stock'],
                    'Min Alert': p['min_stock'],
                    'Photo': 'Available' if p.get('image_data') else 'No Photo',
                    'Status': 'Out of Stock' if p['stock'] <= 0 else ('Low Stock' if p['stock'] <= p['min_stock'] else 'In Stock')
                } for p in filtered])

                st.dataframe(df_prod, hide_index=True, use_container_width=True)

            st.divider()
            st.subheader("Manage Product Record & Update Photo")
            edit_id = st.selectbox(
                "Select product to Edit / Delete",
                [p['id'] for p in filtered],
                format_func=lambda x: f"ID {x}: {next(p['name'] for p in filtered if p['id'] == x)} ({next(p['sku'] for p in filtered if p['id'] == x)})"
            )

            if edit_id:
                p_item = next(p for p in filtered if p['id'] == edit_id)
                e1, e2 = st.columns([1.6, 1])

                with e1:
                    with st.form(f"edit_prod_{edit_id}"):
                        st.write("##### Edit Product Details")
                        e_col1, e_col2 = st.columns(2)
                        e_sku = e_col1.text_input("SKU", value=p_item['sku'])
                        e_name = e_col2.text_input("Name", value=p_item['name'])

                        e_col3, e_col4 = st.columns(2)
                        e_cat = e_col3.text_input("Category", value=p_item['category'] or '')
                        e_wh = e_col4.text_input("Warehouse", value=p_item['warehouse'] or 'Main Warehouse')

                        e_col5, e_col6, e_col7, e_col8 = st.columns(4)
                        e_buy = e_col5.number_input("Buy Price (₹)", value=float(p_item['purchase_price']))
                        e_sell = e_col6.number_input("Sell Price (₹)", value=float(p_item['selling_price']))
                        e_stock = e_col7.number_input("Stock", value=int(p_item['stock']))
                        e_min = e_col8.number_input("Min Stock", value=int(p_item['min_stock']))

                        st.write("##### Update Photo")
                        new_img_file = st.file_uploader("Replace Product Image", type=["png", "jpg", "jpeg", "webp"], key=f"edit_img_{edit_id}")
                        remove_current_img = st.checkbox("Remove current photo", key=f"rm_img_{edit_id}")

                        if st.form_submit_button("Update Product Record"):
                            conn = get_db()
                            try:
                                final_img = p_item.get('image_data')
                                if remove_current_img:
                                    final_img = None
                                elif new_img_file:
                                    mime_type = new_img_file.type or "image/jpeg"
                                    final_img = f"data:{mime_type};base64," + base64.b64encode(new_img_file.read()).decode('utf-8')

                                conn.execute(
                                    "UPDATE products SET sku=?,name=?,category=?,purchase_price=?,selling_price=?,stock=?,min_stock=?,warehouse=?,image_data=? WHERE id=?",
                                    (e_sku.strip(), e_name.strip(), e_cat.strip(), e_buy, e_sell, e_stock, e_min, e_wh.strip(), final_img, edit_id)
                                )
                                conn.commit()
                                st.success("Product updated successfully.")
                                st.rerun()
                            except sqlite3.IntegrityError:
                                st.error("SKU already in use.")
                            finally:
                                conn.close()

                with e2:
                    st.write("##### Current Photo Preview")
                    if p_item.get('image_data'):
                        st.markdown(f"""
                        <div style='background:#ffffff; border:1.5px solid rgba(14,15,12,0.12); border-radius:18px; padding:12px; box-shadow:0 2px 8px -2px rgba(14,15,12,0.06); text-align:center;'>
                          <img src='{p_item['image_data']}' style='max-height:180px; max-width:100%; border-radius:12px; object-fit:contain;' />
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown("""
                        <div style='border:1.5px dashed rgba(14,15,12,0.2); border-radius:18px; padding:32px 16px; text-align:center; background:#ffffff;'>
                          <div style='font-family:"JetBrains Mono",monospace; font-size:0.8rem; color:#787a77; font-weight:600;'>No image attached</div>
                        </div>
                        """, unsafe_allow_html=True)

                    st.write("")
                    st.write("##### Danger Zone")
                    st.caption("Cannot delete products linked to past sales or purchase transactions.")
                    if st.button("Delete Product", type="secondary", key=f"del_prod_btn_{edit_id}"):
                        conn = get_db()
                        has_sales = conn.execute("SELECT COUNT(*) n FROM sale_items WHERE product_id=?", (edit_id,)).fetchone()['n']
                        has_purchases = conn.execute("SELECT COUNT(*) n FROM purchase_items WHERE product_id=?", (edit_id,)).fetchone()['n']
                        if has_sales > 0 or has_purchases > 0:
                            st.error("Cannot delete product: It is linked to existing transactions.")
                        else:
                            conn.execute("DELETE FROM products WHERE id=?", (edit_id,))
                            conn.commit()
                            st.success("Product deleted successfully.")
                            st.rerun()
                        conn.close()
        else:
            st.info("No products found. Add products using the tab above.")
