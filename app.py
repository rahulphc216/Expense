import pandas as pd
import streamlit as st
from datetime import datetime, date, timedelta
import json
import os

st.set_page_config(page_title="Personal Finance Manager", layout="wide")

# --- Persistent Storage File Setup ---
DATA_FILE = "finance_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {
        "banks": [{"Bank Name": "PNB", "Account Type": "Current/OD", "Opening Balance": 66634.72, "Current Balance": 66634.72, "Is OD": True, "OD Limit": 211000.0}],
        "cards": [],
        "lic_loans": [],
        "rd_mf": [],
        "submenus": {
            "Patna": ["Rent", "Office"],
            "Barhiya": ["Vegetable", "Fruit"],
            "Lakhisarai": ["General"],
            "Others": ["Misc"]
        },
        "transactions": []
    }

def save_data():
    data = {
        "banks": st.session_state.banks.to_dict(orient="records"),
        "cards": st.session_state.cards.to_dict(orient="records"),
        "lic_loans": st.session_state.lic_loans.to_dict(orient="records"),
        "rd_mf": st.session_state.rd_mf.to_dict(orient="records"),
        "submenus": st.session_state.submenus,
        "transactions": st.session_state.transactions.to_dict(orient="records")
    }
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, default=str)

# --- Initialize Session State with Safe Columns Check ---
if "data_loaded" not in st.session_state:
    saved_data = load_data()
    
    st.session_state.banks = pd.DataFrame(saved_data.get("banks", []))
    if st.session_state.banks.empty:
        st.session_state.banks = pd.DataFrame(columns=["Bank Name", "Account Type", "Opening Balance", "Current Balance", "Is OD", "OD Limit"])
        
    st.session_state.cards = pd.DataFrame(saved_data.get("cards", []))
    if st.session_state.cards.empty or "Card Name" not in st.session_state.cards.columns:
        st.session_state.cards = pd.DataFrame(columns=["Card Name", "Total Limit", "Opening Balance", "Current Limit", "Billing Date", "Due Date (Day)"])
        
    st.session_state.lic_loans = pd.DataFrame(saved_data.get("lic_loans", []))
    if st.session_state.lic_loans.empty:
        st.session_state.lic_loans = pd.DataFrame(columns=["Name / Policy No", "Type", "Total Amount / Sum Assured", "Frequency", "Due Date Value", "Installment / Premium", "Status"])
    else:
        if "Status" not in st.session_state.lic_loans.columns:
            st.session_state.lic_loans["Status"] = "Pending"

    st.session_state.rd_mf = pd.DataFrame(saved_data.get("rd_mf", []))
    if st.session_state.rd_mf.empty:
        st.session_state.rd_mf = pd.DataFrame(columns=["Name / Scheme", "Type", "Frequency", "Timing Value", "Linked Bank", "Installment Amount", "Opening Balance", "Status", "Start Date"])
    else:
        if "Status" not in st.session_state.rd_mf.columns:
            st.session_state.rd_mf["Status"] = "Pending"
        
    st.session_state.submenus = saved_data.get("submenus", {"Patna": ["Rent", "Office"], "Barhiya": ["Vegetable", "Fruit"], "Lakhisarai": ["General"], "Others": ["Misc"]})
    
    st.session_state.transactions = pd.DataFrame(saved_data.get("transactions", []))
    if st.session_state.transactions.empty:
        st.session_state.transactions = pd.DataFrame(columns=["Date", "Type", "Location", "Submenu", "Mode", "Account/Card", "Amount", "Note"])
        
    st.session_state.data_loaded = True

# --- Accurate IST Date Setup ---
current_ist_date = (datetime.utcnow() + timedelta(hours=5, minutes=30)).date()

# --- Helper Functions ---
def get_bank_net_balance(row):
    if row["Is OD"]:
        return row["Current Balance"] - row["OD Limit"]
    else:
        return row["Current Balance"]

def get_submenus_for_location(loc):
    subs = st.session_state.submenus.get(loc, ["General"])
    return subs if subs else ["General"]

def log_transaction(t_date, t_type, loc, sub, mode, acc_card, amount, note):
    new_tx = {
        "Date": str(t_date),
        "Type": t_type,
        "Location": loc,
        "Submenu": sub,
        "Mode": mode,
        "Account/Card": acc_card,
        "Amount": amount,
        "Note": note
    }
    st.session_state.transactions = pd.concat([st.session_state.transactions, pd.DataFrame([new_tx])], ignore_index=True)
    save_data()

def add_months(sourcedate, months):
    month = sourcedate.month - 1 + months
    year = sourcedate.year + month // 12
    month = month % 12 + 1
    day = min(sourcedate.day, [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month-1])
    return date(year, month, day)

def add_years(sourcedate, years):
    try:
        return sourcedate.replace(year=sourcedate.year + years)
    except ValueError:
        return sourcedate.replace(year=sourcedate.year + years, month=2, day=28)

# --- Sidebar Navigation ---
st.sidebar.title("Finance Manager")
menu = st.sidebar.selectbox("Navigation", ["Add Expense", "Dashboard", "Master Settings", "Add Income", "Special Transactions", "Next Due Tracker", "Reports"])

# ==================== 1. ADD EXPENSE ====================
if menu == "Add Expense":
    st.header("📉 Add Expense")
    
    exp_date = st.date_input("Date", value=current_ist_date, key="exp_date_input")
    location = st.selectbox("Location", ["Patna", "Barhiya", "Lakhisarai", "Others"], key="exp_loc_input")
    
    available_subs = get_submenus_for_location(location)
    submenu = st.selectbox("Submenu Category", available_subs, key="exp_sub_input")
    
    mode = st.selectbox("Payment Mode", ["Cash", "Credit Card", "Saving Bank Account"], key="exp_mode_input")
    
    account_or_card = None
    if mode == "Credit Card":
        if not st.session_state.cards.empty and "Card Name" in st.session_state.cards.columns:
            account_or_card = st.selectbox("Select Credit Card", st.session_state.cards["Card Name"], key="exp_cc_input")
        else:
            st.warning("Please add a credit card first in Master Settings.")
    elif mode == "Saving Bank Account":
        if not st.session_state.banks.empty and "Bank Name" in st.session_state.banks.columns:
            account_or_card = st.selectbox("Select Bank Account", st.session_state.banks["Bank Name"], key="exp_bank_input")
        else:
            st.warning("Please add a bank account first in Master Settings.")
            
    amount = st.number_input("Amount", min_value=1.0, value=100.0, key="exp_amt_input")
    note = st.text_input("Note / Description", key="exp_note_input")
    
    if st.button("Save Expense"):
        can_save = True
        if mode == "Credit Card" and not account_or_card:
            can_save = False
            st.error("Please select a valid Credit Card.")
        elif mode == "Saving Bank Account" and not account_or_card:
            can_save = False
            st.error("Please select a valid Bank Account.")
            
        if can_save:
            acc_val = account_or_card if account_or_card else "Cash"
            if mode == "Credit Card" and account_or_card:
                idx = st.session_state.cards[st.session_state.cards["Card Name"] == account_or_card].index[0]
                st.session_state.cards.loc[idx, "Current Limit"] -= amount
            elif mode == "Saving Bank Account" and account_or_card:
                idx = st.session_state.banks[st.session_state.banks["Bank Name"] == account_or_card].index[0]
                st.session_state.banks.loc[idx, "Current Balance"] -= amount
                
            log_transaction(exp_date, "Expense", location, submenu, mode, acc_val, amount, note)
            st.success("✅ Expense recorded successfully! Action completed 100%.")
            st.balloons()

# ==================== 2. DASHBOARD ====================
elif menu == "Dashboard":
    st.header("📊 Financial Dashboard & Summary")
    
    current_day = current_ist_date.day
    current_month = current_ist_date.month
    current_year = current_ist_date.year

    # Credit Card Alerts
    if not st.session_state.cards.empty and "Due Date (Day)" in st.session_state.cards.columns:
        for idx, row in st.session_state.cards.iterrows():
            try:
                due_day = int(row["Due Date (Day)"])
                days_left = due_day - current_day
                if 0 <= days_left <= 7:
                    st.warning(f"🚨 **Credit Card Alert:** **{row['Card Name']}** bill due in **{days_left} days** (Due Date: {due_day}th of this month)!")
            except:
                pass
                
    # LIC / Loans Alerts
    if not st.session_state.lic_loans.empty:
        if "Status" not in st.session_state.lic_loans.columns:
            st.session_state.lic_loans["Status"] = "Pending"
            
        for idx, row in st.session_state.lic_loans.iterrows():
            try:
                status_val = str(row.get("Status", "Pending")).strip().capitalize()
                if status_val == "Pending":
                    due_val = str(row.get("Due Date Value", "")).strip()
                    if "-" in due_val:
                        parts = due_val.split("-")
                        d_day, d_mon, d_yr = int(parts[0]), int(parts[1]), int(parts[2])
                        due_dt = date(d_yr, d_mon, d_day)
                        
                        delta_days = (due_dt - current_ist_date).days
                        if 0 <= delta_days <= 7:
                            st.warning(f"🚨 **LIC/Loan Alert:** **{row['Name / Policy No']}** payment due in **{delta_days} days** (Due on {due_val})!")
                        elif delta_days < 0 and abs(delta_days) <= 5:
                            st.warning(f"🚨 **LIC/Loan Alert:** **{row['Name / Policy No']}** payment is **OVERDUE** by {abs(delta_days)} days!")
            except:
                pass

    # RD / MF Due Alerts
    if not st.session_state.rd_mf.empty:
        if "Status" not in st.session_state.rd_mf.columns:
            st.session_state.rd_mf["Status"] = "Pending"
            
        for idx, row in st.session_state.rd_mf.iterrows():
            try:
                status_val = str(row.get("Status", "Pending")).strip().capitalize()
                if status_val == "Pending":
                    due_val = str(row.get("Timing Value", "")).strip()
                    if "-" in due_val:
                        parts = due_val.split("-")
                        d_day, d_mon, d_yr = int(parts[0]), int(parts[1]), int(parts[2])
                        due_dt = date(d_yr, d_mon, d_day)
                        delta_days = (due_dt - current_ist_date).days
                        if 0 <= delta_days <= 7:
                            st.warning(f"🚨 **RD/MF Alert:** **{row['Name / Scheme']}** installment due in **{delta_days} days** (Due on {due_val})!")
            except:
                pass

    # Quick Summary Metrics
    st.subheader("📌 Overall Financial Summary")
    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
    
    total_bank_bal = 0
    if not st.session_state.banks.empty:
        total_bank_bal = st.session_state.banks.apply(get_bank_net_balance, axis=1).sum()
        
    total_cc_used = 0
    total_cc_limit = 0
    total_cc_usage_pct = 0.0
    if not st.session_state.cards.empty:
        tot_lim_ser = pd.to_numeric(st.session_state.cards["Total Limit"], errors="coerce").fillna(0)
        cur_lim_ser = pd.to_numeric(st.session_state.cards["Current Limit"], errors="coerce").fillna(0)
        total_cc_limit = tot_lim_ser.sum()
        total_cc_used = (tot_lim_ser - cur_lim_ser).sum()
        if total_cc_limit > 0:
            total_cc_usage_pct = (total_cc_used / total_cc_limit) * 100

    col_s1.metric("Consolidated Bank Balance", f"Rs. {total_bank_bal:,.2f}")
    col_s2.metric("Total Credit Limit Used", f"Rs. {total_cc_used:,.2f}")
    col_s3.metric("Combined Credit Limit", f"Rs. {total_cc_limit:,.2f}")
    col_s4.metric("Overall CC Usage %", f"{total_cc_usage_pct:.2f}%")
    st.markdown("---")

    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏦 Bank Accounts Overview")
        if not st.session_state.banks.empty:
            b_df = st.session_state.banks.copy()
            b_df["Net Balance (inc. OD)"] = b_df.apply(get_bank_net_balance, axis=1)
            st.dataframe(b_df[["Bank Name", "Account Type", "Current Balance", "OD Limit", "Net Balance (inc. OD)"]])
        else:
            st.info("No bank accounts added yet.")

    with col2:
        st.subheader("💳 Individual Credit Cards List")
        if not st.session_state.cards.empty:
            c_disp = st.session_state.cards.copy()
            c_disp["Total Limit"] = pd.to_numeric(c_disp["Total Limit"], errors="coerce").fillna(0)
            c_disp["Current Limit"] = pd.to_numeric(c_disp["Current Limit"], errors="coerce").fillna(0)
            c_disp["Used Limit"] = c_disp["Total Limit"] - c_disp["Current Limit"]
            c_disp["Usage %"] = c_disp.apply(lambda r: f"{(r['Used Limit'] / r['Total Limit']) * 100:.2f}%" if r["Total Limit"] > 0 else "0.00%", axis=1)
            disp_cols = [c for c in ["Card Name", "Total Limit", "Current Limit", "Used Limit", "Usage %", "Billing Date", "Due Date (Day)"] if c in c_disp.columns]
            st.dataframe(c_disp[disp_cols])
        else:
            st.info("No credit cards added yet.")
            
    if not st.session_state.lic_loans.empty:
        st.markdown("---")
        st.subheader("📑 LIC Policies & Loans Summary")
        disp_ll = st.session_state.lic_loans.copy()
        if "Status" in disp_ll.columns:
            disp_ll = disp_ll.drop(columns=["Status"])
        st.dataframe(disp_ll)

    if not st.session_state.rd_mf.empty:
        st.markdown("---")
        st.subheader("📈 RD / Mutual Funds Summary")
        df_rd_disp = st.session_state.rd_mf.copy()
        df_rd_disp["Total Invested / Value"] = df_rd_disp["Opening Balance"] + df_rd_disp.apply(lambda r: r["Installment Amount"] if str(r["Status"]).strip().capitalize() == "Completed" else 0.0, axis=1)
        if "Status" in df_rd_disp.columns:
            df_rd_disp = df_rd_disp.drop(columns=["Status"])
        st.dataframe(df_rd_disp)

    st.markdown("---")
    st.subheader("📋 Recent Transactions")
    if not st.session_state.transactions.empty:
        df_show = st.session_state.transactions.copy()
        df_show["Date"] = pd.to_datetime(df_show["Date"]).dt.date
        st.dataframe(df_show.tail(10))
    else:
        st.info("No transactions recorded yet.")

# ==================== 3. MASTER SETTINGS ====================
elif menu == "Master Settings":
    st.header("⚙️ Master Settings (Add/Edit/Delete)")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Bank Accounts", "Credit Cards", "LIC / Loans", "RD / MF", "Location Submenus"])
    
    with tab1:
        st.subheader("Manage Bank Accounts")
        with st.expander("➕ Click here to Add New Bank Account"):
            with st.form("add_bank_form"):
                b_name = st.text_input("Bank Name")
                b_type = st.selectbox("Account Type", ["Saving", "Current/OD"])
                b_open = st.number_input("Opening/Current Balance", value=0.0, format="%.2f")
                is_od = st.checkbox("Is this an OD Account?")
                od_limit = st.number_input("OD Limit (if applicable)", value=0.0, format="%.2f")
                submitted_b = st.form_submit_button("Save Bank")
                if submitted_b and b_name:
                    if b_name not in st.session_state.banks["Bank Name"].values:
                        new_row = {"Bank Name": b_name, "Account Type": b_type, "Opening Balance": b_open, "Current Balance": b_open, "Is OD": is_od, "OD Limit": od_limit if is_od else 0.0}
                        st.session_state.banks = pd.concat([st.session_state.banks, pd.DataFrame([new_row])], ignore_index=True)
                        save_data()
                        st.success(f"✅ Bank '{b_name}' added successfully!")
                        st.balloons()
                    else:
                        st.warning("Bank already exists!")
        
        st.write("### Existing Banks")
        if not st.session_state.banks.empty:
            b_display = st.session_state.banks.copy()
            b_display["Net Balance"] = b_display.apply(get_bank_net_balance, axis=1)
            st.dataframe(b_display)
            
            del_bank = st.selectbox("Select Bank to Delete", st.session_state.banks["Bank Name"], key="del_bank_sel")
            if st.button("Delete Bank"):
                st.session_state.banks = st.session_state.banks[st.session_state.banks["Bank Name"] != del_bank]
                save_data()
                st.success("✅ Bank deleted successfully!")
                st.rerun()

    with tab2:
        st.subheader("Manage Credit Cards")
        with st.expander("➕ Click here to Add New Credit Card"):
            with st.form("add_card_form"):
                c_name = st.text_input("Credit Card Name")
                c_limit = st.number_input("Total Limit", value=50000.0)
                c_open = st.number_input("Current Used Amount", value=0.0)
                c_bill = st.number_input("Billing Date (Day of month)", min_value=1, max_value=31, value=1)
                c_due = st.number_input("Due Date (Day of month e.g., 10)", min_value=1, max_value=31, value=15)
                submitted_c = st.form_submit_button("Save Credit Card")
                if submitted_c and c_name:
                    if c_name not in st.session_state.cards["Card Name"].values:
                        new_card = {"Card Name": c_name, "Total Limit": c_limit, "Opening Balance": c_open, "Current Limit": c_limit - c_open, "Billing Date": c_bill, "Due Date (Day)": c_due}
                        st.session_state.cards = pd.concat([st.session_state.cards, pd.DataFrame([new_card])], ignore_index=True)
                        save_data()
                        st.success(f"✅ Credit Card '{c_name}' added successfully!")
                        st.balloons()
                    else:
                        st.warning("Credit Card already exists!")
        
        st.write("### Existing Credit Cards")
        if not st.session_state.cards.empty and "Card Name" in st.session_state.cards.columns:
            c_disp = st.session_state.cards.copy()
            c_disp["Total Limit"] = pd.to_numeric(c_disp["Total Limit"], errors="coerce").fillna(0)
            c_disp["Current Limit"] = pd.to_numeric(c_disp["Current Limit"], errors="coerce").fillna(0)
            c_disp["Used Limit"] = c_disp["Total Limit"] - c_disp["Current Limit"]
            c_disp["Usage %"] = c_disp.apply(lambda r: f"{(r['Used Limit'] / r['Total Limit']) * 100:.2f}%" if r["Total Limit"] > 0 else "0.00%", axis=1)
            disp_cols = [c for c in ["Card Name", "Total Limit", "Current Limit", "Used Limit", "Usage %", "Billing Date", "Due Date (Day)"] if c in c_disp.columns]
            st.dataframe(c_disp[disp_cols])
            
            del_card = st.selectbox("Select Card to Delete", st.session_state.cards["Card Name"], key="del_card_sel")
            if st.button("Delete Credit Card"):
                st.session_state.cards = st.session_state.cards[st.session_state.cards["Card Name"] != del_card]
                save_data()
                st.success("✅ Credit Card deleted successfully!")
                st.rerun()

    with tab3:
        st.subheader("Manage LIC Policies & Loans")
        with st.expander("➕ Click here to Add New LIC / Loan"):
            ll_name = st.text_input("Name / Policy Number / Loan Title", key="ll_name_in")
            ll_type = st.selectbox("Type", ["LIC Policy", "Loan"], key="ll_type_in")
            ll_amount = st.number_input("Total Amount / Sum Assured / Loan Amount", value=100000.0, key="ll_amt_in")
            ll_freq = st.selectbox("Payment Frequency", ["Monthly", "Yearly"], key="ll_freq_in")
            
            ll_due_dt = st.date_input("Initial Due Date", value=current_ist_date, key="ll_due_dt_in")
            ll_due_val = ll_due_dt.strftime("%d-%m-%Y")

            ll_installment = st.number_input("Installment / Premium Amount", value=5000.0, key="ll_inst_in")
            
            if st.button("Save LIC / Loan"):
                if ll_name:
                    if ll_name not in st.session_state.lic_loans["Name / Policy No"].values:
                        new_ll = {"Name / Policy No": ll_name, "Type": ll_type, "Total Amount / Sum Assured": ll_amount, "Frequency": ll_freq, "Due Date Value": ll_due_val, "Installment / Premium": ll_installment, "Status": "Pending"}
                        st.session_state.lic_loans = pd.concat([st.session_state.lic_loans, pd.DataFrame([new_ll])], ignore_index=True)
                        save_data()
                        st.success(f"✅ {ll_type} added successfully!")
                        st.balloons()
                    else:
                        st.warning("LIC/Loan entry already exists!")
                else:
                    st.error("Please enter a valid Name or Policy Number.")
        
        st.write("### Existing LIC & Loans")
        if not st.session_state.lic_loans.empty:
            disp_ll = st.session_state.lic_loans.copy()
            if "Status" in disp_ll.columns:
                disp_ll = disp_ll.drop(columns=["Status"])
            st.dataframe(disp_ll)

            del_ll = st.selectbox("Select LIC/Loan to Delete", st.session_state.lic_loans["Name / Policy No"], key="del_ll_key")
            if st.button("Delete LIC/Loan"):
                st.session_state.lic_loans = st.session_state.lic_loans[st.session_state.lic_loans["Name / Policy No"] != del_ll]
                save_data()
                st.success("✅ LIC/Loan deleted successfully!")
                st.rerun()

    with tab4:
        st.subheader("Manage RD & Mutual Funds")
        
        with st.expander("➕ Click here to Add New RD / MF Scheme"):
            rd_name = st.text_input("Scheme / Fund Name", key="rd_name_in")
            rd_type = st.selectbox("Type", ["RD", "Mutual Fund"], key="rd_type_in")
            rd_freq = st.selectbox("Frequency", ["Monthly", "Yearly"], key="rd_freq_in")
            
            rd_due_dt = st.date_input("Initial Due Date", value=current_ist_date, key="rd_due_dt_in")
            rd_timing = rd_due_dt.strftime("%d-%m-%Y")
                
            if not st.session_state.banks.empty:
                rd_bank = st.selectbox("Linked Bank Account (Deduction Source)", st.session_state.banks["Bank Name"], key="rd_bank_in")
            else:
                rd_bank = "None"
                st.warning("Please add a Bank Account first.")
                
            rd_amt = st.number_input("Installment / Contribution Amount", value=2000.0, key="rd_amt_in")
            rd_opening = st.number_input("Opening Balance (Already Invested Amount)", value=0.0, key="rd_opening_in")
            rd_date = st.date_input("Start Date", value=current_ist_date, key="rd_date_in")
            
            if st.button("Save RD / MF Scheme"):
                if rd_name and rd_bank != "None":
                    if rd_name not in st.session_state.rd_mf["Name / Scheme"].values:
                        new_rd = {
                            "Name / Scheme": rd_name, 
                            "Type": rd_type, 
                            "Frequency": rd_freq, 
                            "Timing Value": rd_timing, 
                            "Linked Bank": rd_bank, 
                            "Installment Amount": rd_amt, 
                            "Opening Balance": rd_opening, 
                            "Status": "Pending", 
                            "Start Date": str(rd_date)
                        }
                        st.session_state.rd_mf = pd.concat([st.session_state.rd_mf, pd.DataFrame([new_rd])], ignore_index=True)
                        save_data()
                        st.success(f"✅ RD / MF scheme '{rd_name}' added successfully!")
                        st.balloons()
                    else:
                        st.warning("Scheme already exists!")
                else:
                    st.error("Please enter a valid Scheme Name and select a Bank Account.")
                    
        st.write("### Existing RD / Mutual Funds")
        if not st.session_state.rd_mf.empty:
            df_rd_disp = st.session_state.rd_mf.copy()
            df_rd_disp["Total Invested / Value"] = df_rd_disp["Opening Balance"] + df_rd_disp.apply(lambda r: r["Installment Amount"] if str(r["Status"]).strip().capitalize() == "Completed" else 0.0, axis=1)
            if "Status" in df_rd_disp.columns:
                df_rd_disp = df_rd_disp.drop(columns=["Status"])
            st.dataframe(df_rd_disp)
            
            del_rd = st.selectbox("Select Scheme to Delete", st.session_state.rd_mf["Name / Scheme"], key="del_rd_key")
            if st.button("Delete Selected Scheme"):
                st.session_state.rd_mf = st.session_state.rd_mf[st.session_state.rd_mf["Name / Scheme"] != del_rd]
                save_data()
                st.success("✅ Scheme deleted successfully!")
                st.rerun()

    with tab5:
        st.subheader("Manage Location Submenus")
        loc_choice = st.selectbox("Select Location", ["Patna", "Barhiya", "Lakhisarai", "Others"], key="loc_sub_sel")
        with st.expander("➕ Click here to Add New Submenu"):
            with st.form("add_sub_form"):
                new_sub = st.text_input("New Submenu Name")
                submitted_sub = st.form_submit_button("Save Submenu")
                if submitted_sub and new_sub:
                    existing_subs = st.session_state.submenus.get(loc_choice, [])
                    if new_sub not in existing_subs:
                        st.session_state.submenus[loc_choice].append(new_sub)
                        save_data()
                        st.success(f"✅ Submenu '{new_sub}' added successfully!")
                        st.balloons()
                    else:
                        st.warning("Submenu already exists in this location!")
        
        current_subs = get_submenus_for_location(loc_choice)
        st.write(f"Current Submenus in **{loc_choice}**:", current_subs)
        if current_subs:
            sub_to_del = st.selectbox("Select Submenu to Delete", current_subs, key="del_sub")
            if st.button("Delete Submenu"):
                st.session_state.submenus[loc_choice].remove(sub_to_del)
                save_data()
                st.success("✅ Submenu deleted successfully!")
                st.rerun()

# ==================== 4. ADD INCOME ====================
elif menu == "Add Income":
    st.header("📈 Add Income")
    
    inc_date = st.date_input("Date", value=current_ist_date, key="inc_date_input")
    inc_source = st.selectbox("Income Source", ["Salary", "Advocate", "Refund from Online Platform", "Other"], key="inc_source_input")
    mode = st.selectbox("Receive Mode", ["Cash", "Credit Card (Refund)", "Saving Bank Account"], key="inc_mode_input")
    
    account_or_card = None
    if mode == "Credit Card (Refund)":
        if not st.session_state.cards.empty and "Card Name" in st.session_state.cards.columns:
            account_or_card = st.selectbox("Select Credit Card", st.session_state.cards["Card Name"], key="inc_cc_input")
        else:
            st.warning("Please add a credit card first in Master Settings.")
    elif mode == "Saving Bank Account":
        if not st.session_state.banks.empty and "Bank Name" in st.session_state.banks.columns:
            account_or_card = st.selectbox("Select Bank Account", st.session_state.banks["Bank Name"], key="inc_bank_input")
        else:
            st.warning("Please add a bank account first in Master Settings.")
            
    amount = st.number_input("Amount", min_value=1.0, value=1000.0, key="inc_amt_input")
    note = st.text_input("Note / Description", key="inc_note_input")
    
    if st.button("Save Income"):
        can_save = True
        if mode == "Credit Card (Refund)" and not account_or_card:
            can_save = False
            st.error("Please select a valid Credit Card.")
        elif mode == "Saving Bank Account" and not account_or_card:
            can_save = False
            st.error("Please select a valid Bank Account.")
            
        if can_save:
            acc_val = account_or_card if account_or_card else "Cash"
            if mode == "Credit Card (Refund)" and account_or_card:
                idx = st.session_state.cards[st.session_state.cards["Card Name"] == account_or_card].index[0]
                st.session_state.cards.loc[idx, "Current Limit"] += amount
            elif mode == "Saving Bank Account" and account_or_card:
                idx = st.session_state.banks[st.session_state.banks["Bank Name"] == account_or_card].index[0]
                st.session_state.banks.loc[idx, "Current Balance"] += amount
                
            log_transaction(inc_date, "Income", "N/A", inc_source, mode, acc_val, amount, note)
            st.success("✅ Income recorded successfully! Action completed 100%.")
            st.balloons()

# ==================== 5. SPECIAL TRANSACTIONS ====================
elif menu == "Special Transactions":
    st.header("🔄 Special Transactions (Payments & Transfers)")
    
    st_type = st.selectbox("Transaction Type", ["Lent / Borrow (Udhar)", "Self-Transfer Between Accounts", "Credit Card Bill Payment", "LIC / Loan / RD / MF Payment"])
    
    if st_type == "Lent / Borrow (Udhar)":
        st.subheader("🤝 Lent / Borrow (Udhar)")
        l_date = st.date_input("Date", value=current_ist_date, key="l_date_in")
        action = st.selectbox("Action", ["Given to Friend (Udhar Diya)", "Received Back from Friend"], key="l_action_in")
        mode = st.selectbox("Mode", ["Cash", "Bank Account", "Credit Card"], key="l_mode_in")
        
        acc = None
        if mode == "Bank Account":
            if not st.session_state.banks.empty:
                acc = st.selectbox("Select Bank Account", st.session_state.banks["Bank Name"], key="l_bank_in")
            else:
                st.warning("Please add a bank account first in Master Settings.")
        elif mode == "Credit Card":
            if not st.session_state.cards.empty:
                acc = st.selectbox("Select Credit Card", st.session_state.cards["Card Name"], key="l_card_in")
            else:
                st.warning("Please add a credit card first in Master Settings.")
                
        amount = st.number_input("Amount", value=5000.0, key="l_amt_in")
        note = st.text_input("Person Name / Detail", key="l_note_in")
        
        if st.button("Submit Special Transaction"):
            can_proceed = True
            if mode == "Bank Account" and not acc:
                can_proceed = False
                st.error("Please select a valid Bank Account.")
            elif mode == "Credit Card" and not acc:
                can_proceed = False
                st.error("Please select a valid Credit Card.")
                
            if can_proceed:
                acc_val = acc if acc else "Cash"
                if "Given" in action:
                    if mode == "Bank Account" and acc:
                        idx = st.session_state.banks[st.session_state.banks["Bank Name"] == acc].index[0]
                        st.session_state.banks.loc[idx, "Current Balance"] -= amount
                    elif mode == "Credit Card" and acc:
                        idx = st.session_state.cards[st.session_state.cards["Card Name"] == acc].index[0]
                        st.session_state.cards.loc[idx, "Current Limit"] -= amount
                    log_transaction(l_date, "Udhar Given", "N/A", "Lent", mode, acc_val, amount, note)
                else:
                    if mode == "Bank Account" and acc:
                        idx = st.session_state.banks[st.session_state.banks["Bank Name"] == acc].index[0]
                        st.session_state.banks.loc[idx, "Current Balance"] += amount
                    elif mode == "Credit Card" and acc:
                        idx = st.session_state.cards[st.session_state.cards["Card Name"] == acc].index[0]
                        st.session_state.cards.loc[idx, "Current Limit"] += amount
                    log_transaction(l_date, "Udhar Received", "N/A", "Borrow", mode, acc_val, amount, note)
                save_data()
                st.success("✅ Special transaction recorded successfully!")
                st.balloons()

    elif st_type == "Self-Transfer Between Accounts":
        st.subheader("🔄 Self-Transfer Between Bank Accounts")
        t_date = st.date_input("Transfer Date", value=current_ist_date, key="t_date_in")
        from_acc = st.selectbox("From Bank Account", st.session_state.banks["Bank Name"], key="from_b")
        to_acc = st.selectbox("To Bank Account", st.session_state.banks["Bank Name"], key="to_b")
        amount = st.number_input("Transfer Amount", value=1000.0, key="t_amt_in")
        
        if st.button("Complete Transfer"):
            if from_acc == to_acc:
                st.error("Source and destination accounts cannot be the same!")
            else:
                idx_from = st.session_state.banks[st.session_state.banks["Bank Name"] == from_acc].index[0]
                idx_to = st.session_state.banks[st.session_state.banks["Bank Name"] == to_acc].index[0]
                st.session_state.banks.loc[idx_from, "Current Balance"] -= amount
                st.session_state.banks.loc[idx_to, "Current Balance"] += amount
                
                log_transaction(t_date, "Self-Transfer Out", "N/A", "Transfer", "Saving Bank Account", from_acc, amount, f"Transfer to {to_acc}")
                log_transaction(t_date, "Self-Transfer In", "N/A", "Transfer", "Saving Bank Account", to_acc, amount, f"Transfer from {from_acc}")
                
                save_data()
                st.success("✅ Self-transfer completed successfully!")
                st.balloons()

    elif st_type == "Credit Card Bill Payment":
        st.subheader("💳 Credit Card Bill Payment")
        if not st.session_state.cards.empty and not st.session_state.banks.empty:
            cc_name = st.selectbox("Select Credit Card to Pay", st.session_state.cards["Card Name"], key="cc_pay_sel")
            bank_name = st.selectbox("Pay via Bank Account", st.session_state.banks["Bank Name"], key="cc_bank_sel")
            amount = st.number_input("Bill Payment Amount", value=5000.0, key="cc_amt_pay")
            
            if st.button("Pay Bill (Clears Alert & Restores Limit)"):
                b_idx = st.session_state.banks[st.session_state.banks["Bank Name"] == bank_name].index[0]
                c_idx = st.session_state.cards[st.session_state.cards["Card Name"] == cc_name].index[0]
                
                st.session_state.banks.loc[b_idx, "Current Balance"] -= amount
                st.session_state.cards.loc[c_idx, "Current Limit"] += amount
                
                log_transaction(current_ist_date, "CC Bill Payment Out", "N/A", "Bill Payment", "Saving Bank Account", bank_name, amount, f"Paid bill for {cc_name}")
                log_transaction(current_ist_date, "CC Bill Payment In", "N/A", "Bill Payment", "Credit Card", cc_name, amount, f"Paid via {bank_name}")
                
                save_data()
                st.success(f"✅ Bill paid successfully for {cc_name} via {bank_name}!")
                st.balloons()
        else:
            st.warning("Please add at least one Bank Account and one Credit Card in Master Settings first.")

    elif st_type == "LIC / Loan / RD / MF Payment":
        st.subheader("📑 LIC / Loan / RD / MF Installment Payment")
        
        category = st.selectbox("Select Category", ["LIC / Loan", "RD / Mutual Fund"], key="spec_cat_sel")
        
        if category == "LIC / Loan":
            if not st.session_state.lic_loans.empty and (not st.session_state.banks.empty or not st.session_state.cards.empty):
                ll_item = st.selectbox("Select LIC Policy / Loan", st.session_state.lic_loans["Name / Policy No"].tolist(), key="spec_ll_sel")
                
                matched_rows = st.session_state.lic_loans[st.session_state.lic_loans["Name / Policy No"] == ll_item]
                default_amt = float(matched_rows.iloc[0]["Installment / Premium"]) if not matched_rows.empty else 5000.0
                
                pay_action = st.selectbox("Action Type", ["Pay via Bank / Card (Deducts Balance)", "Mark as Paid (No Balance Deduction)"], key="ll_pay_act")
                
                ll_mode, ll_acc_card = "Cash", "Cash"
                if pay_action == "Pay via Bank / Card (Deducts Balance)":
                    ll_mode = st.selectbox("Payment Mode", ["Saving Bank Account", "Credit Card", "Cash"], key="spec_ll_mode")
                    if ll_mode == "Saving Bank Account" and not st.session_state.banks.empty:
                        ll_acc_card = st.selectbox("Select Bank Account", st.session_state.banks["Bank Name"], key="spec_ll_b")
                    elif ll_mode == "Credit Card" and not st.session_state.cards.empty:
                        ll_acc_card = st.selectbox("Select Credit Card", st.session_state.cards["Card Name"], key="spec_ll_c")
                        
                amount = st.number_input("Installment Amount", value=default_amt, key=f"spec_ll_amt_{ll_item}")
                
                if st.button("Submit Payment"):
                    if pay_action == "Pay via Bank / Card (Deducts Balance)":
                        if ll_mode == "Saving Bank Account" and ll_acc_card in st.session_state.banks["Bank Name"].values:
                            b_idx = st.session_state.banks[st.session_state.banks["Bank Name"] == ll_acc_card].index[0]
                            st.session_state.banks.loc[b_idx, "Current Balance"] -= amount
                        elif ll_mode == "Credit Card" and ll_acc_card in st.session_state.cards["Card Name"].values:
                            c_idx = st.session_state.cards[st.session_state.cards["Card Name"] == ll_acc_card].index[0]
                            st.session_state.cards.loc[c_idx, "Current Limit"] -= amount
                            
                    acc_val = ll_acc_card if pay_action == "Pay via Bank / Card (Deducts Balance)" else "Manual/Marked"
                    log_transaction(current_ist_date, "Expense", "Others", "LIC/Loan Payment", ll_mode if pay_action == "Pay via Bank / Card (Deducts Balance)" else "Cash", acc_val, amount, f"Installment for {ll_item}")
                            
                    save_data()
                    st.success(f"✅ Payment recorded for {ll_item} and added to Expenses report successfully!")
                    st.balloons()
            else:
                st.warning("Please add LIC/Loans and Bank/Cards in Master Settings first.")
        else:
            if not st.session_state.rd_mf.empty and (not st.session_state.banks.empty or not st.session_state.cards.empty):
                rd_item = st.selectbox("Select RD / Mutual Fund", st.session_state.rd_mf["Name / Scheme"].tolist(), key="spec_rd_sel")
                matched_rows = st.session_state.rd_mf[st.session_state.rd_mf["Name / Scheme"] == rd_item]
                default_amt = float(matched_rows.iloc[0]["Installment Amount"]) if not matched_rows.empty else 2000.0
                
                pay_action = st.selectbox("Action Type", ["Pay via Bank / Card (Deducts Balance)", "Mark as Paid (No Balance Deduction)"], key="rd_pay_act")
                
                rd_mode, rd_acc_card = "Cash", "Cash"
                if pay_action == "Pay via Bank / Card (Deducts Balance)":
                    rd_mode = st.selectbox("Payment Mode", ["Saving Bank Account", "Credit Card", "Cash"], key="spec_rd_mode")
                    if rd_mode == "Saving Bank Account" and not st.session_state.banks.empty:
                        rd_acc_card = st.selectbox("Select Bank Account", st.session_state.banks["Bank Name"], key="spec_rd_b")
                    elif rd_mode == "Credit Card" and not st.session_state.cards.empty:
                        rd_acc_card = st.selectbox("Select Credit Card", st.session_state.cards["Card Name"], key="spec_rd_c")
                        
                amount = st.number_input("Installment Amount", value=default_amt, key=f"spec_rd_amt_{rd_item}")
                
                if st.button("Submit RD/MF Payment"):
                    if pay_action == "Pay via Bank / Card (Deducts Balance)":
                        if rd_mode == "Saving Bank Account" and rd_acc_card in st.session_state.banks["Bank Name"].values:
                            b_idx = st.session_state.banks[st.session_state.banks["Bank Name"] == rd_acc_card].index[0]
                            st.session_state.banks.loc[b_idx, "Current Balance"] -= amount
                        elif rd_mode == "Credit Card" and rd_acc_card in st.session_state.cards["Card Name"].values:
                            c_idx = st.session_state.cards[st.session_state.cards["Card Name"] == rd_acc_card].index[0]
                            st.session_state.cards.loc[c_idx, "Current Limit"] -= amount
                            
                    save_data()
                    st.success(f"✅ Payment updated for {rd_item} successfully!")
                    st.balloons()
            else:
                st.warning("Please add RD/MF and Bank/Cards in Master Settings first.")

# ==================== 7. NEXT DUE TRACKER (Dedicated Control Room) ====================
elif menu == "Next Due Tracker":
    st.header("⏳ Dedicated Next Due Tracker & Control Room")
    st.write("Yahan aap apni saari LIC, Loans, RD, aur Mutual Funds ki due dates aur status ko ek hi jagah par aasani se manage aur rollover kar sakte hain.")
    
    tab_due1, tab_due2 = st.tabs(["📑 LIC & Loans Dues", "📈 RD & Mutual Funds Dues"])
    
    with tab_due1:
        st.subheader("Manage LIC Policies & Loans Due Dates")
        if not st.session_state.lic_loans.empty:
            disp_ll = st.session_state.lic_loans.copy()
            st.dataframe(disp_ll)
            
            sel_policy = st.selectbox("Select Policy / Loan to Update", st.session_state.lic_loans["Name / Policy No"], key="track_ll_sel")
            action_choice = st.selectbox("Select Action", ["Mark as Paid / Complete & Rollover", "Reset to Pending"], key="track_ll_act")
            
            if st.button("Execute Action on Policy"):
                p_idx = st.session_state.lic_loans[st.session_state.lic_loans["Name / Policy No"] == sel_policy].index[0]
                if action_choice == "Mark as Paid / Complete & Rollover":
                    st.session_state.lic_loans.loc[p_idx, "Status"] = "Completed"
                    freq = str(st.session_state.lic_loans.loc[p_idx, "Frequency"]).strip()
                    due_val = str(st.session_state.lic_loans.loc[p_idx, "Due Date Value"]).strip()
                    try:
                        d_parts = due_val.split("-")
                        curr_due_date = date(int(d_parts[2]), int(d_parts[1]), int(d_parts[0]))
                        new_due_date = add_months(curr_due_date, 1) if freq == "Monthly" else add_years(curr_due_date, 1)
                        st.session_state.lic_loans.loc[p_idx, "Due Date Value"] = new_due_date.strftime("%d-%m-%Y")
                        st.session_state.lic_loans.loc[p_idx, "Status"] = "Pending"
                    except Exception as e:
                        st.error(f"Date conversion error: {e}")
                    save_data()
                    st.success(f"✅ '{sel_policy}' completed & next due date successfully rolled over!")
                    st.rerun()
                else:
                    st.session_state.lic_loans.loc[p_idx, "Status"] = "Pending"
                    save_data()
                    st.success(f"✅ '{sel_policy}' status reset to Pending!")
                    st.rerun()
        else:
            st.info("No LIC or Loan entries found.")

    with tab_due2:
        st.subheader("Manage RD & Mutual Funds Due Dates")
        if not st.session_state.rd_mf.empty:
            disp_rd = st.session_state.rd_mf.copy()
            st.dataframe(disp_rd)
            
            sel_rd = st.selectbox("Select RD / MF Scheme to Update", st.session_state.rd_mf["Name / Scheme"], key="track_rd_sel")
            action_rd_choice = st.selectbox("Select Action", ["Mark as Paid / Complete & Rollover", "Reset to Pending"], key="track_rd_act")
            
            if st.button("Execute Action on Scheme"):
                r_idx = st.session_state.rd_mf[st.session_state.rd_mf["Name / Scheme"] == sel_rd].index[0]
                if action_rd_choice == "Mark as Paid / Complete & Rollover":
                    st.session_state.rd_mf.loc[r_idx, "Status"] = "Completed"
                    freq = str(st.session_state.rd_mf.loc[r_idx, "Frequency"]).strip()
                    due_val = str(st.session_state.rd_mf.loc[r_idx, "Timing Value"]).strip()
                    try:
                        d_parts = due_val.split("-")
                        curr_due = date(int(d_parts[2]), int(d_parts[1]), int(d_parts[0]))
                        new_due = add_months(curr_due, 1) if freq == "Monthly" else add_years(curr_due, 1)
                        st.session_state.rd_mf.loc[r_idx, "Timing Value"] = new_due.strftime("%d-%m-%Y")
                        st.session_state.rd_mf.loc[r_idx, "Status"] = "Pending"
                    except Exception as e:
                        st.error(f"Date conversion error: {e}")
                    save_data()
                    st.success(f"✅ Scheme '{sel_rd}' completed & next due date successfully rolled over!")
                    st.rerun()
                else:
                    st.session_state.rd_mf.loc[r_idx, "Status"] = "Pending"
                    save_data()
                    st.success(f"✅ Scheme '{sel_rd}' status reset to Pending!")
                    st.rerun()
        else:
            st.info("No RD or Mutual Fund entries found.")

# ==================== 6. REPORTS & PASSBOOK ====================
elif menu == "Reports":
    st.header("📋 Reports & Individual Item Passbook (Ledger)")
    
    tab_rep1, tab_rep2, tab_rep3 = st.tabs(["🔍 General Filter Reports", "📖 Individual Passbook / Ledger", "💰 Net Balance Summary"])
    
    with tab_rep1:
        if not st.session_state.transactions.empty:
            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                filter_type = st.selectbox("Filter Period", ["All", "Daily", "Weekly", "Monthly", "Quarterly", "Half Yearly", "Yearly", "Custom Date Range"], key="rep_per")
            with col_f2:
                tx_type_filter = st.selectbox("Transaction Type", ["All", "Expense", "Income"], key="rep_type")
            with col_f3:
                all_modes = ["All"] + list(st.session_state.transactions["Account/Card"].unique())
                account_filter = st.selectbox("Filter by Bank/Card/Cash", all_modes, key="rep_acc")
                
            df_rep = st.session_state.transactions.copy()
            df_rep["Date"] = pd.to_datetime(df_rep["Date"])
            today_dt = pd.to_datetime(current_ist_date)
            
            if filter_type == "Daily":
                df_rep = df_rep[df_rep["Date"].dt.date == current_ist_date]
            elif filter_type == "Weekly":
                start_week = today_dt - timedelta(days=7)
                df_rep = df_rep[(df_rep["Date"] >= start_week) & (df_rep["Date"] <= today_dt)]
            elif filter_type == "Monthly":
                df_rep = df_rep[(df_rep["Date"].dt.month == today_dt.month) & (df_rep["Date"].dt.year == today_dt.year)]
            elif filter_type == "Quarterly":
                current_quarter = (today_dt.month - 1) // 3 + 1
                df_rep = df_rep[(df_rep["Date"].dt.quarter == current_quarter) & (df_rep["Date"].dt.year == today_dt.year)]
            elif filter_type == "Half Yearly":
                current_half = 1 if today_dt.month <= 6 else 2
                df_rep = df_rep[(df_rep["Date"].dt.month.apply(lambda m: 1 if m <= 6 else 2) == current_half) & (df_rep["Date"].dt.year == today_dt.year)]
            elif filter_type == "Yearly":
                df_rep = df_rep[df_rep["Date"].dt.year == today_dt.year]
            elif filter_type == "Custom Date Range":
                c_start = st.date_input("Start Date", value=current_ist_date, key="rep_start")
                c_end = st.date_input("End Date", value=current_ist_date, key="rep_end")
                df_rep = df_rep[(df_rep["Date"].dt.date >= c_start) & (df_rep["Date"].dt.date <= c_end)]
                
            if tx_type_filter != "All":
                df_rep = df_rep[df_rep["Type"] == tx_type_filter]
                
            if account_filter != "All":
                df_rep = df_rep[df_rep["Account/Card"] == account_filter]
                
            df_display = df_rep.copy()
            df_display["Date"] = pd.to_datetime(df_display["Date"]).dt.date
                
            st.write(f"### Results (Total Records: {len(df_display)})")
            st.dataframe(df_display)
            
            if not df_display.empty:
                total_filtered_amt = df_display["Amount"].sum()
                st.markdown(f"### 💰 **Total Amount (Filtered View): Rs. {total_filtered_amt:,.2f}**")
            
            overall_total = st.session_state.transactions["Amount"].sum()
            st.markdown(f"📌 **Overall Total Transaction Amount (All Records): Rs. {overall_total:,.2f}**")
            
            if not df_rep.empty:
                st.subheader("📊 Category / Submenu Wise Summary")
                summary_df = df_rep.groupby(["Type", "Submenu"])["Amount"].sum().reset_index()
                st.dataframe(summary_df)

            st.markdown("---")
            st.subheader("✏️ Edit or ❌ Delete Transaction")
            
            action_type = st.radio("Choose Action", ["Delete Transaction", "Edit Transaction"], key="tx_act_radio")
            
            if action_type == "Delete Transaction":
                del_idx = st.selectbox("Select Transaction Index to Delete", df_rep.index.tolist() if not df_rep.empty else [], key="del_tx_sel")
                if st.button("Delete Selected Transaction"):
                    if del_idx in st.session_state.transactions.index:
                        tx_row = st.session_state.transactions.loc[del_idx]
                        amt = tx_row["Amount"]
                        mode = tx_row["Mode"]
                        acc_card = tx_row["Account/Card"]
                        t_type = tx_row["Type"]
                        
                        if t_type == "Expense":
                            if mode == "Credit Card" and acc_card in st.session_state.cards["Card Name"].values:
                                c_idx = st.session_state.cards[st.session_state.cards["Card Name"] == acc_card].index[0]
                                st.session_state.cards.loc[c_idx, "Current Limit"] += amt
                            elif mode == "Saving Bank Account" and acc_card in st.session_state.banks["Bank Name"].values:
                                b_idx = st.session_state.banks[st.session_state.banks["Bank Name"] == acc_card].index[0]
                                st.session_state.banks.loc[b_idx, "Current Balance"] += amt
                        elif t_type == "Income":
                            if "Credit Card" in mode and acc_card in st.session_state.cards["Card Name"].values:
                                c_idx = st.session_state.cards[st.session_state.cards["Card Name"] == acc_card].index[0]
                                st.session_state.cards.loc[c_idx, "Current Limit"] -= amt
                            elif mode == "Saving Bank Account" and acc_card in st.session_state.banks["Bank Name"].values:
                                b_idx = st.session_state.banks[st.session_state.banks["Bank Name"] == acc_card].index[0]
                                st.session_state.banks.loc[b_idx, "Current Balance"] += amt
                                
                        st.session_state.transactions = st.session_state.transactions.drop(del_idx).reset_index(drop=True)
                        save_data()
                        st.success("✅ Transaction deleted successfully!")
                        st.balloons()
                        
            elif action_type == "Edit Transaction":
                edit_idx = st.selectbox("Select Transaction Index to Edit", df_rep.index.tolist() if not df_rep.empty else [], key="edit_tx_sel")
                if edit_idx in st.session_state.transactions.index:
                    row_data = st.session_state.transactions.loc[edit_idx]
                    with st.form("edit_tx_form"):
                        st.write(f"Editing Transaction (Index: {edit_idx}, Type: {row_data['Type']})")
                        new_amt = st.number_input("New Amount", value=float(row_data["Amount"]))
                        new_note = st.text_input("New Note / Description", value=str(row_data["Note"]))
                        submitted_edit = st.form_submit_button("Update Transaction")
                        
                        if submitted_edit:
                            old_amt = row_data["Amount"]
                            mode = row_data["Mode"]
                            acc_card = row_data["Account/Card"]
                            t_type = row_data["Type"]
                            diff = new_amt - old_amt
                            
                            if t_type == "Expense":
                                if mode == "Credit Card" and acc_card in st.session_state.cards["Card Name"].values:
                                    c_idx = st.session_state.cards[st.session_state.cards["Card Name"] == acc_card].index[0]
                                    st.session_state.cards.loc[c_idx, "Current Limit"] -= diff
                                elif mode == "Saving Bank Account" and acc_card in st.session_state.banks["Bank Name"].values:
                                    b_idx = st.session_state.banks[st.session_state.banks["Bank Name"] == acc_card].index[0]
                                    st.session_state.banks.loc[b_idx, "Current Balance"] -= diff
                            elif t_type == "Income":
                                if "Credit Card" in mode and acc_card in st.session_state.cards["Card Name"].values:
                                    c_idx = st.session_state.cards[st.session_state.cards["Card Name"] == acc_card].index[0]
                                    st.session_state.cards.loc[c_idx, "Current Limit"] += diff
                                elif mode == "Saving Bank Account" and acc_card in st.session_state.banks["Bank Name"].values:
                                    b_idx = st.session_state.banks[st.session_state.banks["Bank Name"] == acc_card].index[0]
                                    st.session_state.banks.loc[b_idx, "Current Balance"] += diff
                                    
                            st.session_state.transactions.loc[edit_idx, "Amount"] = new_amt
                            st.session_state.transactions.loc[edit_idx, "Note"] = new_note
                            save_data()
                            st.success("✅ Transaction updated successfully!")
                            st.balloons()
        else:
            st.info("No transactions recorded yet.")

    with tab_rep2:
        st.subheader("📖 Individual Item Passbook / Ledger with Running Balance")
        
        item_choices = []
        if not st.session_state.banks.empty:
            item_choices.extend([f"Bank: {b}" for b in st.session_state.banks["Bank Name"]])
        if not st.session_state.cards.empty and "Card Name" in st.session_state.cards.columns:
            item_choices.extend([f"Credit Card: {c}" for c in st.session_state.cards["Card Name"]])
        if not st.session_state.rd_mf.empty:
            item_choices.extend([f"RD/MF: {r}" for r in st.session_state.rd_mf["Name / Scheme"]])
        if not st.session_state.lic_loans.empty:
            item_choices.extend([f"LIC/Loan: {l}" for l in st.session_state.lic_loans["Name / Policy No"]])
        item_choices.append("Cash")
        
        if item_choices:
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                selected_item = st.selectbox("Select Bank / Card / RD / Loan / LIC for Passbook", item_choices, key="passbook_sel")
            with col_p2:
                pass_filter_type = st.selectbox("Filter Period", ["All", "Daily", "Weekly", "Monthly", "Quarterly", "Half Yearly", "Yearly", "Custom Date Range"], key="pass_per")
            
            if not st.session_state.transactions.empty:
                df_pass = st.session_state.transactions.copy()
                df_pass["Date"] = pd.to_datetime(df_pass["Date"])
                
                today_dt = pd.to_datetime(current_ist_date)
                if pass_filter_type == "Daily":
                    df_pass = df_pass[df_pass["Date"].dt.date == current_ist_date]
                elif pass_filter_type == "Weekly":
                    start_week = today_dt - timedelta(days=7)
                    df_pass = df_pass[(df_pass["Date"] >= start_week) & (df_pass["Date"] <= today_dt)]
                elif pass_filter_type == "Monthly":
                    df_pass = df_pass[(df_pass["Date"].dt.month == today_dt.month) & (df_pass["Date"].dt.year == today_dt.year)]
                elif pass_filter_type == "Quarterly":
                    current_quarter = (today_dt.month - 1) // 3 + 1
                    df_pass = df_pass[(df_pass["Date"].dt.quarter == current_quarter) & (df_pass["Date"].dt.year == today_dt.year)]
                elif pass_filter_type == "Half Yearly":
                    current_half = 1 if today_dt.month <= 6 else 2
                    df_pass = df_pass[(df_pass["Date"].dt.month.apply(lambda m: 1 if m <= 6 else 2) == current_half) & (df_pass["Date"].dt.year == today_dt.year)]
                elif pass_filter_type == "Yearly":
                    df_pass = df_pass[df_pass["Date"].dt.year == today_dt.year]
                elif pass_filter_type == "Custom Date Range":
                    pc_start = st.date_input("Start Date", value=current_ist_date, key="pass_start")
                    pc_end = st.date_input("End Date", value=current_ist_date, key="pass_end")
                    df_pass = df_pass[(df_pass["Date"].dt.date >= pc_start) & (df_pass["Date"].dt.date <= pc_end)]

                df_pass = df_pass.sort_values(by="Date", ascending=True).reset_index(drop=True)
                
                item_type = selected_item.split(": ")[0]
                target_name = selected_item.split(": ")[-1] if ": " in selected_item else selected_item
                
                df_filtered = df_pass[
                    (df_pass["Account/Card"] == target_name) | 
                    (df_pass["Submenu"] == target_name) | 
                    (df_pass["Note"].str.contains(target_name, case=False, na=False))
                ].copy()
                
                st.write(f"### Passbook History for: **{selected_item}** (Total Entries: {len(df_filtered)})")
                
                if not df_filtered.empty:
                    running_bal = 0.0
                    if item_type == "Bank" and not st.session_state.banks.empty:
                        b_row = st.session_state.banks[st.session_state.banks["Bank Name"] == target_name]
                        if not b_row.empty:
                            running_bal = float(b_row.iloc[0]["Opening Balance"])
                    elif item_type == "Credit Card" and not st.session_state.cards.empty:
                        c_row = st.session_state.cards[st.session_state.cards["Card Name"] == target_name]
                        if not c_row.empty:
                            running_bal = float(c_row.iloc[0]["Current Limit"])
                    elif item_type in ["RD/MF", "LIC/Loan"]:
                        running_bal = 0.0
                        
                    balances = []
                    for idx, row in df_filtered.iterrows():
                        amt = float(row["Amount"])
                        t_type = row["Type"]
                        
                        if item_type == "Bank":
                            if t_type in ["Expense", "Self-Transfer Out", "CC Bill Payment Out", "LIC/Loan Payment", "Investment (RD/MF)", "Udhar Given"]:
                                running_bal -= amt
                            else:
                                running_bal += amt
                        elif item_type == "Credit Card":
                            if t_type in ["Expense", "Udhar Given"]:
                                running_bal -= amt
                            else:
                                running_bal += amt
                        else:
                            running_bal += amt
                            
                        balances.append(running_bal)
                        
                    df_filtered["Running Balance"] = balances
                    df_filtered["Date"] = df_filtered["Date"].dt.date
                    
                    display_cols = [c for c in ["Date", "Type", "Submenu", "Mode", "Account/Card", "Amount", "Running Balance", "Note"] if c in df_filtered.columns]
                    st.dataframe(df_filtered[display_cols])
                    
                    st.info(f"💡 **Current / Latest Closing Balance for {target_name}:** Rs. {running_bal:,.2f}")
                else:
                    st.info(f"No direct transaction history found for '{target_name}' in the selected period.")
            else:
                st.info("No transactions recorded yet.")
        else:
            st.warning("Please add Bank Accounts, Credit Cards, or Assets in Master Settings first.")

    with tab_rep3:
        st.subheader("💰 Net Balance Summary (Total Income - Total Expense)")
        
        net_filter_type = st.selectbox("Filter Period for Net Balance", ["All", "Daily", "Weekly", "Monthly", "Quarterly", "Half Yearly", "Yearly", "Custom Date Range"], key="net_per")
        
        if not st.session_state.transactions.empty:
            df_net = st.session_state.transactions.copy()
            df_net["Date"] = pd.to_datetime(df_net["Date"])
            today_dt = pd.to_datetime(current_ist_date)
            
            if net_filter_type == "Daily":
                df_net = df_net[df_net["Date"].dt.date == current_ist_date]
            elif net_filter_type == "Weekly":
                start_week = today_dt - timedelta(days=7)
                df_net = df_net[(df_net["Date"] >= start_week) & (df_net["Date"] <= today_dt)]
            elif net_filter_type == "Monthly":
                df_net = df_net[(df_net["Date"].dt.month == today_dt.month) & (df_net["Date"].dt.year == today_dt.year)]
            elif net_filter_type == "Quarterly":
                current_quarter = (today_dt.month - 1) // 3 + 1
                df_net = df_net[(df_net["Date"].dt.quarter == current_quarter) & (df_net["Date"].dt.year == today_dt.year)]
            elif net_filter_type == "Half Yearly":
                current_half = 1 if today_dt.month <= 6 else 2
                df_net = df_net[(df_net["Date"].dt.month.apply(lambda m: 1 if m <= 6 else 2) == current_half) & (df_net["Date"].dt.year == today_dt.year)]
            elif net_filter_type == "Yearly":
                df_net = df_net[df_net["Date"].dt.year == today_dt.year]
            elif net_filter_type == "Custom Date Range":
                nc_start = st.date_input("Start Date", value=current_ist_date, key="net_start")
                nc_end = st.date_input("End Date", value=current_ist_date, key="net_end")
                df_net = df_net[(df_net["Date"].dt.date >= nc_start) & (df_net["Date"].dt.date <= nc_end)]
                
            total_inc = df_net[df_net["Type"] == "Income"]["Amount"].sum()
            total_exp = df_net[df_net["Type"] == "Expense"]["Amount"].sum()
            net_bal = total_inc - total_exp
            
            col_n1, col_n2, col_n3 = st.columns(3)
            col_n1.metric("Total Income", f"Rs. {total_inc:,.2f}")
            col_n2.metric("Total Expense", f"Rs. {total_exp:,.2f}")
            col_n3.metric("Net Balance (Income - Expense)", f"Rs. {net_bal:,.2f}")
            
            st.markdown("---")
            st.write("### Filtered Transactions List for Net Calculation")
            df_net_disp = df_net.copy()
            df_net_disp["Date"] = df_net_disp["Date"].dt.date
            st.dataframe(df_net_disp)
        else:
            st.info("No transactions available to calculate net balance.")

# --- Permanent Footer ---
st.markdown("---")
st.markdown("<p style='text-align: center; color: gray; font-size: 14px;'>Designed and developed by Rahul</p>", unsafe_allow_html=True)
