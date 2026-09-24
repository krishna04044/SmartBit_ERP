import streamlit as st
import pandas as pd
from database.db import get_db, now

def render_employees(user):
    st.title("Human Resources & Staff")
    st.caption("Manage employee personnel records, department assignments, designations, and payroll.")

    t1, t2 = st.tabs(["Employee Directory", "Add New Employee"])

    with t2:
        with st.form("add_emp_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            name = col1.text_input("Full Name *", placeholder="e.g. Ramesh Kumar")
            dept = col2.text_input("Department", placeholder="e.g. Sales, Operations, Tech")

            col3, col4, col5 = st.columns(3)
            role = col3.text_input("Job Role", placeholder="e.g. Associate Manager")
            salary = col4.number_input("Monthly Salary (₹)", min_value=0.0, step=1000.0, value=25000.0)
            status = col5.selectbox("Status", ["Active", "Inactive"])

            if st.form_submit_button("Add Employee", type="primary"):
                if not name.strip():
                    st.error("Employee name is required.")
                else:
                    conn = get_db()
                    conn.execute(
                        "INSERT INTO employees(name,department,job_role,salary,status,created_at) VALUES(?,?,?,?,?,?)",
                        (name.strip(), dept.strip(), role.strip(), salary, status, now())
                    )
                    conn.commit()
                    conn.close()
                    st.success(f"Employee '{name}' added successfully.")

    with t1:
        conn = get_db()
        employees = conn.execute("SELECT * FROM employees ORDER BY id DESC").fetchall()
        conn.close()

        if employees:
            df_emp = pd.DataFrame([{
                'ID': e['id'],
                'Name': e['name'],
                'Department': e['department'] or '-',
                'Role': e['job_role'] or '-',
                'Salary': f"₹{e['salary']:,.2f}",
                'Status': 'Active' if e['status'] == 'Active' else 'Inactive',
                'Joined': e['created_at']
            } for e in employees])
            st.dataframe(df_emp, hide_index=True, use_container_width=True)

            st.divider()
            e_id = st.selectbox(
                "Select Employee to Manage",
                [e['id'] for e in employees],
                format_func=lambda x: f"{next(e['name'] for e in employees if e['id'] == x)} — {next(e['department'] or 'General' for e in employees if e['id'] == x)}"
            )
            if e_id:
                emp_sel = next(e for e in employees if e['id'] == e_id)
                col1, col2 = st.columns(2)
                with col1:
                    with st.form(f"edit_emp_{e_id}"):
                        st.write("##### Edit Employee Details")
                        en = st.text_input("Name", value=emp_sel['name'])
                        ed = st.text_input("Department", value=emp_sel['department'] or '')
                        er = st.text_input("Job Role", value=emp_sel['job_role'] or '')
                        es = st.number_input("Monthly Salary", value=float(emp_sel['salary']))
                        est = st.selectbox("Status", ["Active", "Inactive"], index=0 if emp_sel['status'] == 'Active' else 1)
                        if st.form_submit_button("Update Employee"):
                            conn = get_db()
                            conn.execute("UPDATE employees SET name=?,department=?,job_role=?,salary=?,status=? WHERE id=?", (en.strip(), ed.strip(), er.strip(), es, est, e_id))
                            conn.commit()
                            conn.close()
                            st.success("Employee record updated.")
                            st.rerun()
                with col2:
                    st.write("##### Delete Employee")
                    if st.button("Delete Employee Record", key=f"del_emp_{e_id}"):
                        conn = get_db()
                        conn.execute("DELETE FROM employees WHERE id=?", (e_id,))
                        conn.commit()
                        conn.close()
                        st.success("Employee deleted.")
                        st.rerun()
        else:
            st.info("No employees registered yet.")
