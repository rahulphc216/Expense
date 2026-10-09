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
        st.session_state.lic_loans = pd.DataFrame(columns=["Name / Policy No", "Type", "Total Amount / Sum Assured", "Frequency", "Due Date Value", "Installment / Premium"])
        
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

# --- Sidebar Navigation ---
st.sidebar.title("Finance Manager")
menu = st.sidebar.selectbox("Navigation", ["Add Expense", "Dashboard", "Master Settings", "Add Income", "Special Transactions", "Reports"])

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
            if mode == "Credit Card" and account_or_card:
                idx = st.session_state.cards[st.session_state.cards["Card Name"] == account_or_card].index[0]
                st.session_state.cards.loc[idx, "Current Limit"] -= amount
            elif mode == "Saving Bank Account" and account_or_card:
                idx = st.session_state.banks[st.session_state.banks["Bank Name"] == account_or_card].index[0]
                st.session_state.banks.loc[idx, "Current Balance"] -= amount
                
            new_tx = {"Date": str(exp_date), "Type": "Expense", "Location": location, "Submenu": submenu, "Mode": mode, "Account/Card": account_or_card if account_or_card else "Cash", "Amount": amount, "Note": note}
            st.session_state.transactions = pd.concat([st.session_state.transactions, pd.DataFrame([new_tx])], ignore_index=True)
            save_data()
            st.success("✅ Expense recorded successfully! Action completed 100%.")
            st.balloons()

# ==================== 2. DASHBOARD ====================
elif menu == "Dashboard":
    st.header("📊 Financial Dashboard")
    
    current_day = current_ist_date.day
    current_month = current_ist_date.month

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
        for idx, row in st.session_state.lic_loans.iterrows():
            try:
                freq = row.get("Frequency", "Monthly")
                if freq == "Monthly":
                    due_day = int(row["Due Date Value"])
                    days_left = due_day - current_day
                    if 0 <= days_left <= 7:
                        st.warning(f"🚨 **LIC/Loan Alert:** **{row['Name / Policy No']}** payment due in **{days_left} days** (Due on {due_day}th)!")
                elif freq == "Yearly":
                    parts = row["Due Date Value"].split("-")
                    due_m, due_d = int(parts[0]), int(parts[1])
                    if due_m == current_month:
                        days_left = due_d - current_day
                        if 0 <= days_left <= 7:
                            st.warning(f"🚨 **LIC/Loan Alert:** **{row['Name / Policy No']}** annual payment due in **{days_left} days**!")
            except:
                pass

    # Credit Card Summary
    if not st.session_state.cards.empty and "Total Limit" in st.session_state.cards.columns:
        st.subheader("💳 All Credit Cards Combined Summary")
        c_df = st.session_state.cards.copy()
        total_limit_all = c_df["Total Limit"].sum()
        total_used_all = total_limit_all - c_df["Current Limit"].sum()
        overall_usage_pct = (total_used_all / total_limit_all) * 100 if total_limit_all > 0 else 0
        
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Combined Total Limit", f"Rs. {total_limit_all:,.2f}")
        col_m2.metric("Combined Total Used", f"Rs. {total_used_all:,.2f}")
        col_m3.metric("Overall Usage Percentage", f"{overall_usage_pct:.1f}%")
        st.markdown("---")

    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏦 Bank Accounts Overview")
        if not st.session_state.banks.empty:
            b_df = st.session_state.banks.copy()
            b_df["Net Balance (inc. OD)"] = b_df.apply(get_bank_net_balance, axis=1)
            consolidated_bank_bal = b_df["Net Balance (inc. OD)"].sum()
            st.metric("Consolidated Net Bank Balance", f"Rs. {consolidated_bank_bal:,.2f}")
            st.dataframe(b_df[["Bank Name", "Account Type", "Current Balance", "OD Limit", "Net Balance (inc. OD)"]])
        else:
            st.info("No bank accounts added yet.")

    with col2:
        st.subheader("💳 Individual Credit Cards List")
        if not st.session_state.cards.empty:
            disp_cols = [c for c in ["Card Name", "Total Limit", "Current Limit", "Billing Date", "Due Date (Day)"] if c in st.session_state.cards.columns]
            st.dataframe(st.session_state.cards[disp_cols])
        else:
            st.info("No credit cards added yet.")
            
    if not st.session_state.lic_loans.empty:
        st.markdown("---")
        st.subheader("📑 LIC Policies & Loans Summary")
        st.dataframe(st.session_state.lic_loans)

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
    
    tab1, tab2, tab3, tab4 = st.tabs(["Bank Accounts", "Credit Cards", "LIC / Loans", "Location Submenus"])
    
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
            disp_cols = [c for c in ["Card Name", "Total Limit", "Current Limit", "Billing Date", "Due Date (Day)"] if c in st.session_state.cards.columns]
            st.dataframe(st.session_state.cards[disp_cols])
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
            
            if ll_freq == "Monthly":
                ll_due_val = str(st.number_input("Due Day of Month (1-31)", min_value=1, max_value=31, value=10, key="ll_due_m"))
            else:
                col_m, col_d = st.columns(2)
                due_month = col_m.selectbox("Due Month", list(range(1, 13)), format_func=lambda x: datetime(2000, x, 1).strftime('%B'), key="ll_due_month_sel")
                due_day = col_d.number_input("Due Day", min_value=1, max_value=31, value=10, key="ll_due_d")
                ll_due_val = f"{due_month:02d}-{due_day:02d}"

            ll_installment = st.number_input("Installment / Premium Amount", value=5000.0, key="ll_inst_in")
            
            if st.button("Save LIC / Loan"):
                if ll_name:
                    if ll_name not in st.session_state.lic_loans["Name / Policy No"].values:
                        new_ll = {"Name / Policy No": ll_name, "Type": ll_type, "Total Amount / Sum Assured": ll_amount, "Frequency": ll_freq, "Due Date Value": ll_due_val, "Installment / Premium": ll_installment}
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
            st.dataframe(st.session_state.lic_loans)
            del_ll = st.selectbox("Select LIC/Loan to Delete", st.session_state.lic_loans["Name / Policy No"], key="del_ll_key")
            if st.button("Delete LIC/Loan"):
                st.session_state.lic_loans = st.session_state.lic_loans[st.session_state.lic_loans["Name / Policy No"] != del_ll]
                save_data()
                st.success("✅ LIC/Loan deleted successfully!")
                st.rerun()

    with tab4:
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
            if mode == "Credit Card (Refund)" and account_or_card:
                idx = st.session_state.cards[st.session_state.cards["Card Name"] == account_or_card].index[0]
                st.session_state.cards.loc[idx, "Current Limit"] += amount
            elif mode == "Saving Bank Account" and account_or_card:
                idx = st.session_state.banks[st.session_state.banks["Bank Name"] == account_or_card].index[0]
                st.session_state.banks.loc[idx, "Current Balance"] += amount
                
            new_tx = {"Date": str(inc_date), "Type": "Income", "Location": "N/A", "Submenu": inc_source, "Mode": mode, "Account/Card": account_or_card if account_or_card else "Cash", "Amount": amount, "Note": note}
            st.session_state.transactions = pd.concat([st.session_state.transactions, pd.DataFrame([new_tx])], ignore_index=True)
            save_data()
            st.success("✅ Income recorded successfully! Action completed 100%.")
            st.balloons()

# ==================== 5. SPECIAL TRANSACTIONS ====================
elif menu == "Special Transactions":
    st.header("🔄 Special Transactions (Payments & Transfers)")
    
    st_type = st.selectbox("Transaction Type", ["Lent / Borrow (Udhar)", "Self-Transfer Between Accounts", "Credit Card Bill Payment", "LIC / Loan Installment Payment"])
    
    if st_type == "Lent / Borrow (Udhar)":
        with st.form("lent_form"):
            l_date = st.date_input("Date", value=current_ist_date)
            action = st.selectbox("Action", ["Given to Friend (Udhar Diya)", "Received Back from Friend"])
            mode = st.selectbox("Mode", ["Cash", "Bank Account", "Credit Card"])
            acc = None
            if mode == "Bank Account":
                acc = st.selectbox("Bank", st.session_state.banks["Bank Name"])
            elif mode == "Credit Card":
                acc = st.selectbox("Card", st.session_state.cards["Card Name"])
            amount = st.number_input("Amount", value=5000.0)
            note = st.text_input("Person Name / Detail")
            
            if st.form_submit_button("Submit Special Transaction"):
                if "Given" in action:
                    if mode == "Bank Account" and acc:
                        idx = st.session_state.banks[st.session_state.banks["Bank Name"] == acc].index[0]
                        st.session_state.banks.loc[idx, "Current Balance"] -= amount
                    elif mode == "Credit Card" and acc:
                        idx = st.session_state.cards[st.session_state.cards["Card Name"] == acc].index[0]
                        st.session_state.cards.loc[idx, "Current Limit"] -= amount
                else:
                    if mode == "Bank Account" and acc:
                        idx = st.session_state.banks[st.session_state.banks["Bank Name"] == acc].index[0]
                        st.session_state.banks.loc[idx, "Current Balance"] += amount
                    elif mode == "Credit Card" and acc:
                        idx = st.session_state.cards[st.session_state.cards["Card Name"] == acc].index[0]
                        st.session_state.cards.loc[idx, "Current Limit"] += amount
                save_data()
                st.success("✅ Special transaction recorded successfully!")
                st.balloons()

    elif st_type == "Self-Transfer Between Accounts":
        with st.form("transfer_form"):
            t_date = st.date_input("Transfer Date", value=current_ist_date)
            from_acc = st.selectbox("From Bank Account", st.session_state.banks["Bank Name"], key="from_b")
            to_acc = st.selectbox("To Bank Account", st.session_state.banks["Bank Name"], key="to_b")
            amount = st.number_input("Transfer Amount", value=1000.0)
            
            if st.form_submit_button("Complete Transfer"):
                if from_acc == to_acc:
                    st.error("Source and destination accounts cannot be the same!")
                else:
                    idx_from = st.session_state.banks[st.session_state.banks["Bank Name"] == from_acc].index[0]
                    idx_to = st.session_state.banks[st.session_state.banks["Bank Name"] == to_acc].index[0]
                    st.session_state.banks.loc[idx_from, "Current Balance"] -= amount
                    st.session_state.banks.loc[idx_to, "Current Balance"] += amount
                    save_data()
                    st.success("✅ Self-transfer completed successfully!")
                    st.balloons()

    elif st_type == "Credit Card Bill Payment":
        with st.form("cc_bill_form"):
            cc_name = st.selectbox("Select Credit Card to Pay", st.session_state.cards["Card Name"])
            bank_name = st.selectbox("Pay via Bank Account", st.session_state.banks["Bank Name"])
            amount = st.number_input("Bill Payment Amount", value=5000.0)
            
            if st.form_submit_button("Pay Bill (Clears Alert & Restores Limit)"):
                b_idx = st.session_state.banks[st.session_state.banks["Bank Name"] == bank_name].index[0]
                c_idx = st.session_state.cards[st.session_state.cards["Card Name"] == cc_name].index[0]
                
                st.session_state.banks.loc[b_idx, "Current Balance"] -= amount
                st.session_state.cards.loc[c_idx, "Current Limit"] += amount
                save_data()
                st.success(f"✅ Bill paid successfully for {cc_name} via {bank_name}!")
                st.balloons()

    elif st_type == "LIC / Loan Installment Payment":
        with st.form("lic_pay_form"):
            if not st.session_state.lic_loans.empty:
                ll_item = st.selectbox("Select LIC Policy / Loan", st.session_state.lic_loans["Name / Policy No"])
                bank_name = st.selectbox("Pay via Bank Account", st.session_state.banks["Bank Name"])
                amount = st.number_input("Installment Amount Paid", value=5000.0)
                
                if st.form_submit_button("Pay Installment (Clears Alert)"):
                    b_idx = st.session_state.banks[st.session_state.banks["Bank Name"] == bank_name].index[0]
                    st.session_state.banks.loc[b_idx, "Current Balance"] -= amount
                    save_data()
                    st.success(f"✅ Installment paid for {ll_item} via {bank_name}!")
                    st.balloons()
            else:
                st.warning("No LIC or Loan added yet in Master Settings.")

# ==================== 6. REPORTS & TRANSACTION MANAGEMENT ====================
elif menu == "Reports":
    st.header("📋 Detailed Reports, Filters & Transaction Management")
    
    if not st.session_state.transactions.empty:
        st.subheader("🔍 Filter Reports")
        
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            filter_type = st.selectbox("Filter Period", ["All", "Daily", "Weekly", "Monthly", "Quarterly", "Half Yearly", "Yearly", "Custom Date Range"])
        with col_f2:
            tx_type_filter = st.selectbox("Transaction Type", ["All", "Expense", "Income"])
        with col_f3:
            all_modes = ["All"] + list(st.session_state.transactions["Account/Card"].unique())
            account_filter = st.selectbox("Filter by Bank/Card/Cash", all_modes)
            
        df_rep = st.session_state.transactions.copy()
        df_rep["Date"] = pd.to_datetime(df_rep["Date"])
        today_dt = pd.to_datetime(current_ist_date)
        
        # Period Filter
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
            c_start = st.date_input("Start Date", value=current_ist_date)
            c_end = st.date_input("End Date", value=current_ist_date)
            df_rep = df_rep[(df_rep["Date"].dt.date >= c_start) & (df_rep["Date"].dt.date <= c_end)]
            
        # Type Filter
        if tx_type_filter != "All":
            df_rep = df_rep[df_rep["Type"] == tx_type_filter]
            
        # Account/Card Filter
        if account_filter != "All":
            df_rep = df_rep[df_rep["Account/Card"] == account_filter]
            
        # Format Date to remove 00:00:00 time
        df_display = df_rep.copy()
        df_display["Date"] = pd.to_datetime(df_display["Date"]).dt.date
            
        st.write(f"### Results (Total Records: {len(df_display)})")
        st.dataframe(df_display)
        
        # Category / Submenu Wise Sum
        if not df_rep.empty:
            st.subheader("📊 Category / Submenu Wise Summary")
            summary_df = df_rep.groupby(["Type", "Submenu"])["Amount"].sum().reset_index()
            st.dataframe(summary_df)

        st.markdown("---")
        st.subheader("✏️ Edit or ❌ Delete Transaction")
        
        action_type = st.radio("Choose Action", ["Delete Transaction", "Edit Transaction"])
        
        if action_type == "Delete Transaction":
            del_idx = st.selectbox("Select Transaction Index to Delete", df_rep.index.tolist() if not df_rep.empty else [], key="del_tx_sel")
            if st.button("Delete Selected Transaction"):
                if del_idx in st.session_state.transactions.index:
                    tx_row = st.session_state.transactions.loc[del_idx]
                    amt = tx_row["Amount"]
                    mode = tx_row["Mode"]
                    acc_card = tx_row["Account/Card"]
                    t_type = tx_row["Type"]
                    
                    # Reverse Balance Effect
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
                            st.session_state.banks.loc[b_idx, "Current Balance"] -= amt
                            
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

# --- Permanent Footer ---
st.markdown("---")
st.markdown("<p style='text-align: center; color: gray; font-size: 14px;'>Designed and developed by Rahul</p>", unsafe_allow_html=True)
