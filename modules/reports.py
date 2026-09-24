import streamlit as st
import pandas as pd
import plotly.express as px
from database.db import get_db

def render_reports(user):
    st.title("Reports & Analytics")
    st.caption("Financial performance summaries, product turnover, and data exports.")

    conn = get_db()
    sales_cnt = conn.execute("SELECT COUNT(*) c, COALESCE(SUM(total),0) t FROM sales").fetchone()
    expenses_cnt = conn.execute("SELECT COUNT(*) c, COALESCE(SUM(amount),0) t FROM expenses").fetchone()
    products_cnt = conn.execute("SELECT COUNT(*) c, COALESCE(SUM(stock * purchase_price),0) v FROM products").fetchone()
    low_cnt = conn.execute("SELECT COUNT(*) c FROM products WHERE stock<=min_stock").fetchone()

    monthly_sales = {r['m']: r['t'] for r in conn.execute("SELECT substr(created_at,1,7) m, SUM(total) t FROM sales GROUP BY m").fetchall()}
    monthly_exp = {r['m']: r['t'] for r in conn.execute("SELECT substr(created_at,1,7) m, SUM(amount) t FROM expenses GROUP BY m").fetchall()}
    all_months = sorted(list(set(list(monthly_sales.keys()) + list(monthly_exp.keys()))), reverse=True)[:6]

    monthly_data = []
    for m in all_months:
        s_val = monthly_sales.get(m, 0.0)
        e_val = monthly_exp.get(m, 0.0)
        monthly_data.append({
            'Month': m,
            'Revenue (₹)': s_val,
            'Expenses (₹)': e_val,
            'Net Profit (₹)': s_val - e_val
        })

    top_prods = conn.execute("""
        SELECT COALESCE(p.name, 'Unknown') name, COALESCE(p.sku, '-') sku, SUM(si.qty) total_qty, SUM(si.qty * si.unit_price) total_rev
        FROM sale_items si
        LEFT JOIN products p ON p.id = si.product_id
        GROUP BY si.product_id
        ORDER BY total_qty DESC
        LIMIT 5
    """).fetchall()

    exp_cats = conn.execute("SELECT category, COUNT(*) count, SUM(amount) total FROM expenses GROUP BY category ORDER BY total DESC").fetchall()
    conn.close()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sales Orders", f"{sales_cnt['c']}", f"₹{sales_cnt['t']:,.2f} total")
    c2.metric("Expenses Logged", f"{expenses_cnt['c']}", f"₹{expenses_cnt['t']:,.2f} total")
    c3.metric("Inventory Asset Value", f"₹{products_cnt['v']:,.2f}", f"{products_cnt['c']} items")
    c4.metric("Low Stock Items", f"{low_cnt['c']}", "Requires reorder")

    st.write("")
    col_l, col_r = st.columns(2)

    with col_l:
        st.subheader("Monthly Performance")
        if monthly_data:
            df_m = pd.DataFrame(monthly_data)
            st.dataframe(df_m.style.format({
                'Revenue (₹)': '₹{:,.2f}',
                'Expenses (₹)': '₹{:,.2f}',
                'Net Profit (₹)': '₹{:,.2f}'
            }), hide_index=True, use_container_width=True)
        else:
            st.info("No monthly transaction data available.")

    with col_r:
        st.subheader("Top Selling Products")
        if top_prods:
            df_top = pd.DataFrame([{
                'Product': r['name'],
                'SKU': r['sku'],
                'Units Sold': r['total_qty'],
                'Revenue': f"₹{r['total_rev']:,.2f}"
            } for r in top_prods])
            st.dataframe(df_top, hide_index=True, use_container_width=True)
        else:
            st.info("No sales transactions yet.")

    st.subheader("Category-wise Expense Breakdown")
    if exp_cats:
        df_exp_cat = pd.DataFrame([dict(r) for r in exp_cats])
        is_dark = st.session_state.get("theme_mode", "dark") == "dark"
        chart_bg = "#1a1c1e" if is_dark else "#ffffff"
        text_color = "#f5f6f7" if is_dark else "#0e0f0c"
        font_family = "Geist Mono" if is_dark else "JetBrains Mono"
        border_color = "#0c0d0f" if is_dark else "#ffffff"
        chart_palette = (
            ["#5fe3b1", "#8b8e93", "#3a3d42", "#26292d", "#e8b95f", "#e87a5f", "#f5f6f7"]
            if is_dark else
            ["#9fe870", "#163300", "#454745", "#e2f6d5", "#cdffad", "#0e0f0c", "#868685"]
        )

        fig_pie = px.pie(
            df_exp_cat,
            names="category",
            values="total",
            color_discrete_sequence=chart_palette
        )
        fig_pie.update_traces(
            textinfo="percent+label",
            marker=dict(line=dict(color=border_color, width=2))
        )
        fig_pie.update_layout(
            margin=dict(l=20, r=20, t=20, b=20),
            height=320,
            plot_bgcolor=chart_bg,
            paper_bgcolor=chart_bg,
            font=dict(family=font_family, color=text_color)
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("No expense categories recorded yet.")

    # Data Export Section
    st.divider()
    st.subheader("Export System Data (CSV)")
    conn = get_db()
    df_sales_exp = pd.read_sql_query("SELECT * FROM sales", conn)
    df_inv_exp = pd.read_sql_query("SELECT * FROM products", conn)
    df_exp_exp = pd.read_sql_query("SELECT * FROM expenses", conn)
    conn.close()

    ex1, ex2, ex3 = st.columns(3)
    ex1.download_button("Download Sales Data (.csv)", df_sales_exp.to_csv(index=False), "sales_export.csv", "text/csv")
    ex2.download_button("Download Products (.csv)", df_inv_exp.to_csv(index=False), "products_export.csv", "text/csv")
    ex3.download_button("Download Expenses (.csv)", df_exp_exp.to_csv(index=False), "expenses_export.csv", "text/csv")
