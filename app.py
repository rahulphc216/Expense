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

# --- Initialize Session State from File ---
if "data_loaded" not in st.session_state:
    saved_data = load_data()
    st.session_state.banks = pd.DataFrame(saved_data["banks"])
    st.session_state.cards = pd.DataFrame(saved_data["cards"])
    st.session_state.lic_loans = pd.DataFrame(saved_data["lic_loans"])
    st.session_state.submenus = saved_data["submenus"]
    st.session_state.transactions = pd.DataFrame(saved_data["transactions"])
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
        if not st.session_state.cards.empty:
            account_or_card = st.selectbox("Select Credit Card", st.session_state.cards["Card Name"], key="exp_cc_input")
        else:
            st.warning("Please add a credit card first in Master Settings.")
    elif mode == "Saving Bank Account":
        if not st.session_state.banks.empty:
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
            st.success("Expense recorded successfully!")

# ==================== 2. DASHBOARD ====================
elif menu == "Dashboard":
    st.header("📊 Financial Dashboard")
    
    today = current_ist_date
    if not st.session_state.cards.empty:
        for idx, row in st.session_state.cards.iterrows():
            try:
                due_date = pd.to_datetime(row["Due Date"]).date()
                days_left = (due_date - today).days
                if 0 <= days_left <= 7:
                    st.warning(f"🚨 **Credit Card Alert:** **{row['Card Name']}** bill due in **{days_left} days** (Due Date: {row['Due Date']})!")
            except:
                pass
                
    if not st.session_state.lic_loans.empty:
        for idx, row in st.session_state.lic_loans.iterrows():
            try:
                due_date = pd.to_datetime(row["Due Date"]).date()
                days_left = (due_date - today).days
                if 0 <= days_left <= 7:
                    st.warning(f"🚨 **LIC/Loan Alert:** **{row['Name / Policy No']}** ({row['Type']}) payment due in **{days_left} days**!")
            except:
                pass

    if not st.session_state.cards.empty:
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
            st.dataframe(b_df[["Bank Name", "Account Type", "Current Balance", "OD Limit", "Net Balance (inc. OD)"]])
        else:
            st.info("No bank accounts added yet.")

    with col2:
        st.subheader("💳 Individual Credit Cards List")
        if not st.session_state.cards.empty:
            st.dataframe(st.session_state.cards[["Card Name", "Total Limit", "Current Limit", "Due Date"]])
        else:
            st.info("No credit cards added yet.")
            
    if not st.session_state.lic_loans.empty:
        st.markdown("---")
        st.subheader("📑 LIC Policies & Loans Summary")
        st.dataframe(st.session_state.lic_loans)

    st.markdown("---")
    st.subheader("📋 Transaction History & Reports")
    if not st.session_state.transactions.empty:
        st.dataframe(st.session_state.transactions)
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
                        st.success(f"Bank {b_name} added successfully!")
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
                st.rerun()

    with tab2:
        st.subheader("Manage Credit Cards")
        with st.expander("➕ Click here to Add New Credit Card"):
            with st.form("add_card_form"):
                c_name = st.text_input("Credit Card Name")
                c_limit = st.number_input("Total Limit", value=50000.0)
                c_open = st.number_input("Current Used Amount", value=0.0)
                c_bill = st.number_input("Billing Date (Day of month)", min_value=1, max_value=31, value=1)
                c_due = st.date_input("Due Date", value=current_ist_date)
                submitted_c = st.form_submit_button("Save Credit Card")
                if submitted_c and c_name:
                    if c_name not in st.session_state.cards["Card Name"].values:
                        new_card = {"Card Name": c_name, "Total Limit": c_limit, "Opening Balance": c_open, "Current Limit": c_limit - c_open, "Billing Date": c_bill, "Due Date": str(c_due)}
                        st.session_state.cards = pd.concat([st.session_state.cards, pd.DataFrame([new_card])], ignore_index=True)
                        save_data()
                        st.success(f"Credit Card {c_name} added successfully!")
                    else:
                        st.warning("Credit Card already exists!")
        
        st.write("### Existing Credit Cards")
        if not st.session_state.cards.empty:
            st.dataframe(st.session_state.cards)
            del_card = st.selectbox("Select Card to Delete", st.session_state.cards["Card Name"], key="del_card_sel")
            if st.button("Delete Credit Card"):
                st.session_state.cards = st.session_state.cards[st.session_state.cards["Card Name"] != del_card]
                save_data()
                st.rerun()

    with tab3:
        st.subheader("Manage LIC Policies & Loans")
        with st.expander("➕ Click here to Add New LIC / Loan"):
            with st.form("add_lic_loan_form"):
                ll_name = st.text_input("Name / Policy Number / Loan Title")
                ll_type = st.selectbox("Type", ["LIC Policy", "Loan"])
                ll_amount = st.number_input("Total Amount / Sum Assured / Loan Amount", value=100000.0)
                ll_due = st.date_input("Next Premium / Due Date", value=current_ist_date)
                ll_installment = st.number_input("Installment / Premium Amount", value=5000.0)
                submitted_ll = st.form_submit_button("Save LIC / Loan")
                if submitted_ll and ll_name:
                    if ll_name not in st.session_state.lic_loans["Name / Policy No"].values:
                        new_ll = {"Name / Policy No": ll_name, "Type": ll_type, "Total Amount / Sum Assured": ll_amount, "Due Date": str(ll_due), "Installment / Premium": ll_installment}
                        st.session_state.lic_loans = pd.concat([st.session_state.lic_loans, pd.DataFrame([new_ll])], ignore_index=True)
                        save_data()
                        st.success(f"{ll_type} added successfully!")
                    else:
                        st.warning("LIC/Loan entry already exists!")
        
        st.write("### Existing LIC & Loans")
        if not st.session_state.lic_loans.empty:
            st.dataframe(st.session_state.lic_loans)
            del_ll = st.selectbox("Select LIC/Loan to Delete", st.session_state.lic_loans["Name / Policy No"], key="del_ll_key")
            if st.button("Delete LIC/Loan"):
                st.session_state.lic_loans = st.session_state.lic_loans[st.session_state.lic_loans["Name / Policy No"] != del_ll]
                save_data()
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
                        st.success(f"Added '{new_sub}' to {loc_choice}!")
                        st.rerun()
                    else:
                        st.warning("Submenu already exists in this location!")
        
        current_subs = get_submenus_for_location(loc_choice)
        st.write(f"Current Submenus in **{loc_choice}**:", current_subs)
        if current_subs:
            sub_to_del = st.selectbox("Select Submenu to Delete", current_subs, key="del_sub")
            if st.button("Delete Submenu"):
                st.session_state.submenus[loc_choice].remove(sub_to_del)
                save_data()
                st.rerun()

# ==================== 4. ADD INCOME ====================
elif menu == "Add Income":
    st.header("📈 Add Income")
    
    inc_date = st.date_input("Date", value=current_ist_date, key="inc_date_input")
    inc_source = st.selectbox("Income Source", ["Salary", "Advocate", "Refund from Online Platform", "Other"], key="inc_source_input")
    mode = st.selectbox("Receive Mode", ["Cash", "Credit Card (Refund)", "Saving Bank Account"], key="inc_mode_input")
    
    account_or_card = None
    if mode == "Credit Card (Refund)":
        if not st.session_state.cards.empty:
            account_or_card = st.selectbox("Select Credit Card", st.session_state.cards["Card Name"], key="inc_cc_input")
        else:
            st.warning("Please add a credit card first in Master Settings.")
    elif mode == "Saving Bank Account":
        if not st.session_state.banks.empty:
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
            st.success("Income recorded successfully!")

# ==================== 5. SPECIAL TRANSACTIONS ====================
elif menu == "Special Transactions":
    st.header("🔄 Special Transactions (No Income/Expense Impact)")
    
    st_type = st.selectbox("Transaction Type", ["Lent / Borrow (Udhar)", "Self-Transfer Between Accounts", "Credit Card Bill Payment"])
    
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
                st.success("Recorded successfully without affecting Income or Expense!")

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
                    st.success("Self-transfer completed successfully!")

    elif st_type == "Credit Card Bill Payment":
        with st.form("cc_bill_form"):
            cc_name = st.selectbox("Select Credit Card to Pay", st.session_state.cards["Card Name"])
            bank_name = st.selectbox("Pay via Bank Account", st.session_state.banks["Bank Name"])
            amount = st.number_input("Bill Payment Amount", value=5000.0)
            
            if st.form_submit_button("Pay Bill (Clears Due Alert & Updates Limits)"):
                b_idx = st.session_state.banks[st.session_state.banks["Bank Name"] == bank_name].index[0]
                c_idx = st.session_state.cards[st.session_state.cards["Card Name"] == cc_name].index[0]
                
                st.session_state.banks.loc[b_idx, "Current Balance"] -= amount
                st.session_state.cards.loc[c_idx, "Current Limit"] += amount
                save_data()
                st.success(f"Bill paid successfully for {cc_name} via {bank_name}!")

# ==================== 6. REPORTS ====================
elif menu == "Reports":
    st.header("📋 Detailed Reports & Transaction History")
    
    if not st.session_state.transactions.empty:
        filter_type = st.selectbox("Filter Report Type", ["All", "Daily", "Weekly", "Monthly", "Quarterly", "Half Yearly", "Yearly"])
        
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
            
        st.write(f"Showing **{filter_type}** Transactions:")
        st.dataframe(df_rep)
    else:
        st.info("No transactions recorded yet.")

# --- Permanent Footer ---
st.markdown("---")
st.markdown("<p style='text-align: center; color: gray; font-size: 14px;'>Designed and developed by Rahul</p>", unsafe_allow_html=True)
