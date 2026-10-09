import pandas as pd
import streamlit as st
from datetime import datetime, date, timedelta

st.set_page_config(page_title="Personal Finance Manager", layout="wide")

# --- Current Date Setup (Native Python) ---
current_ist_date = date.today()

# --- Initialize Session State ---
if "banks" not in st.session_state:
    st.session_state.banks = pd.DataFrame(columns=["Bank Name", "Account Type", "Opening Balance", "Current Balance", "Is OD", "OD Limit"])
    st.session_state.banks.loc[0] = ["PNB", "Current/OD", 66634.72, 66634.72, True, 211000.0]

if "cards" not in st.session_state:
    st.session_state.cards = pd.DataFrame(columns=["Card Name", "Total Limit", "Opening Balance", "Current Limit", "Billing Date", "Due Date"])

if "lic_loans" not in st.session_state:
    st.session_state.lic_loans = pd.DataFrame(columns=["Name / Policy No", "Type", "Total Amount / Sum Assured", "Due Date", "Installment / Premium"])

if "submenus" not in st.session_state:
    st.session_state.submenus = {
        "Patna": ["Rent", "Office"],
        "Barhiya": ["Vegetable", "Fruit"],
        "Lakhisarai": ["General"],
        "Others": ["Misc"]
    }

if "transactions" not in st.session_state:
    st.session_state.transactions = pd.DataFrame(columns=["Date", "Type", "Location", "Submenu", "Mode", "Account/Card", "Amount", "Note"])

# --- Helper Functions ---
def get_bank_net_balance(row):
    if row["Is OD"]:
        return row["Current Balance"] - row["OD Limit"]
    else:
        return row["Current Balance"]

# --- Sidebar Navigation (Default to Add Expense) ---
st.sidebar.title("Finance Manager")
menu = st.sidebar.selectbox("Navigation", ["Add Expense", "Dashboard", "Master Settings", "Add Income", "Special Transactions", "Reports"])

# ==================== 1. ADD EXPENSE (Default Home Window) ====================
if menu == "Add Expense":
    st.header("📉 Add Expense")
    
    with st.form("expense_form"):
        exp_date = st.date_input("Date", value=current_ist_date)
        location = st.selectbox("Location", ["Patna", "Barhiya", "Lakhisarai", "Others"])
        available_subs = st.session_state.submenus.get(location, ["General"])
        submenu = st.selectbox("Submenu Category", available_subs)
        
        mode = st.selectbox("Payment Mode", ["Cash", "Credit Card", "Saving Bank Account"])
        
        account_or_card = None
        if mode == "Credit Card":
            if not st.session_state.cards.empty:
                account_or_card = st.selectbox("Select Credit Card", st.session_state.cards["Card Name"])
            else:
                st.warning("Please add a credit card first in Master Settings.")
        elif mode == "Saving Bank Account":
            if not st.session_state.banks.empty:
                account_or_card = st.selectbox("Select Bank Account", st.session_state.banks["Bank Name"])
            else:
                st.warning("Please add a bank account first in Master Settings.")
                
        amount = st.number_input("Amount", min_value=1.0, value=100.0)
        note = st.text_input("Note / Description")
        
        submitted_exp = st.form_submit_button("Save Expense")
        
        if submitted_exp:
            if mode == "Credit Card" and account_or_card:
                idx = st.session_state.cards[st.session_state.cards["Card Name"] == account_or_card].index[0]
                st.session_state.cards.loc[idx, "Current Limit"] -= amount
            elif mode == "Saving Bank Account" and account_or_card:
                idx = st.session_state.banks[st.session_state.banks["Bank Name"] == account_or_card].index[0]
                st.session_state.banks.loc[idx, "Current Balance"] -= amount
                
            new_tx = {"Date": exp_date, "Type": "Expense", "Location": location, "Submenu": submenu, "Mode": mode, "Account/Card": account_or_card if account_or_card else "Cash", "Amount": amount, "Note": note}
            st.session_state.transactions = pd.concat([st.session_state.transactions, pd.DataFrame([new_tx])], ignore_index=True)
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
        st.subheader("Manage Bank Accounts (Multiple Banks & OD Accounts)")
        with st.form("add_bank_form"):
            b_name = st.text_input("Bank Name")
            b_type = st.selectbox("Account Type", ["Saving", "Current/OD"])
            b_open = st.number_input("Opening/Current Balance", value=0.0, format="%.2f")
            is_od = st.checkbox("Is this an OD Account?")
            od_limit = st.number_input("OD Limit (if applicable)", value=0.0, format="%.2f")
            submitted_b = st.form_submit_button("Add Bank")
            if submitted_b and b_name:
                new_row = {"Bank Name": b_name, "Account Type": b_type, "Opening Balance": b_open, "Current Balance": b_open, "Is OD": is_od, "OD Limit": od_limit if is_od else 0.0}
                st.session_state.banks = pd.concat([st.session_state.banks, pd.DataFrame([new_row])], ignore_index=True)
                st.success(f"Bank {b_name} added successfully!")
        
        st.write("### Existing Banks")
        if not st.session_state.banks.empty:
            b_display = st.session_state.banks.copy()
            b_display["Net Balance"] = b_display.apply(get_bank_net_balance, axis=1)
            st.dataframe(b_display)
            
            del_bank = st.selectbox("Select Bank to Delete", st.session_state.banks["Bank Name"])
            if st.button("Delete Bank"):
                st.session_state.banks = st.session_state.banks[st.session_state.banks["Bank Name"] != del_bank]
                st.rerun()

    with tab2:
        st.subheader("Manage Credit Cards (10+ Cards Support)")
        with st.form("add_card_form"):
            c_name = st.text_input("Credit Card Name")
            c_limit = st.number_input("Total Limit", value=50000.0)
            c_open = st.number_input("Current Used Amount", value=0.0)
            c_bill = st.number_input("Billing Date (Day of month)", min_value=1, max_value=31, value=1)
            c_due = st.date_input("Due Date", value=current_ist_date)
            submitted_c = st.form_submit_button("Add Credit Card")
            if submitted_c and c_name:
                new_card = {"Card Name": c_name, "Total Limit": c_limit, "Opening Balance": c_open, "Current Limit": c_limit - c_open, "Billing Date": c_bill, "Due Date": c_due}
                st.session_state.cards = pd.concat([st.session_state.cards, pd.DataFrame([new_card])], ignore_index=True)
                st.success(f"Credit Card {c_name} added successfully!")
        
        st.write("### Existing Credit Cards")
        if not st.session_state.cards.empty:
            st.dataframe(st.session_state.cards)
            del_card = st.selectbox("Select Card to Delete", st.session_state.cards["Card Name"])
            if st.button("Delete Credit Card"):
                st.session_state.cards = st.session_state.cards[st.session_state.cards["Card Name"] != del_card]
                st.rerun()

    with tab3:
        st.subheader("Manage LIC Policies & Loans")
        with st.form("add_lic_loan_form"):
            ll_name = st.text_input("Name / Policy Number / Loan Title")
            ll_type = st.selectbox("Type", ["LIC Policy", "Loan"])
            ll_amount = st.number_input("Total Amount / Sum Assured / Loan Amount", value=100000.0)
            ll_due = st.date_input("Next Premium / Due Date", value=current_ist_date)
            ll_installment = st.number_input("Installment / Premium Amount", value=5000.0)
            submitted_ll = st.form_submit_button("Add LIC / Loan")
            if submitted_ll and ll_name:
                new_ll = {"Name / Policy No": ll_name, "Type": ll_type, "Total Amount / Sum Assured": ll_amount, "Due Date": ll_due, "Installment / Premium": ll_installment}
                st.session_state.lic_loans = pd.concat([st.session_state.lic_loans, pd.DataFrame([new_ll])], ignore_index=True)
                st.success(f"{ll_type} added successfully!")
        
        st.write("### Existing LIC & Loans")
        if not st.session_state.lic_loans.empty:
            st.dataframe(st.session_state.lic_loans)
            del_ll = st.selectbox("Select LIC/Loan to Delete", st.session_state.lic_loans["Name / Policy No"], key="del_ll_key")
            if st.button("Delete LIC/Loan"):
                st.session_state.lic_loans = st.session_state.lic_loans[st.session_state.lic_loans["Name / Policy No"] != del_ll]
                st.rerun()

    with tab4:
        st.subheader("Manage Location Submenus")
        loc_choice = st.selectbox("Select Location", ["Patna", "Barhiya", "Lakhisarai", "Others"])
        
        new_sub = st.text_input("New Submenu Name")
        if st.button("Add Submenu"):
            if new_sub:
                st.session_state.submenus[loc_choice].append(new_sub)
                st.success(f"Added '{new_sub}' to {loc_choice}!")
                st.rerun()
        
        st.write(f"Current Submenus in **{loc_choice}**:", st.session_state.submenus[loc_choice])
        if st.session_state.submenus[loc_choice]:
            sub_to_del = st.selectbox("Select Submenu to Delete", st.session_state.submenus[loc_choice], key="del_sub")
            if st.button("Delete Submenu"):
                st.session_state.submenus[loc_choice].remove(sub_to_del)
                st.rerun()

# ==================== 4. ADD INCOME ====================
elif menu == "Add Income":
    st.header("📈 Add Income")
    
    with st.form("income_form"):
        inc_date = st.date_input("Date", value=current_ist_date)
        inc_source = st.selectbox("Income Source", ["Salary", "Advocate", "Refund from Online Platform", "Other"])
        
        mode = st.selectbox("Receive Mode", ["Cash", "Credit Card (Refund)", "Saving Bank Account"])
        
        account_or_card = None
        if mode == "Credit Card (Refund)":
            if not st.session_state.cards.empty:
                account_or_card = st.selectbox("Select Credit Card", st.session_state.cards["Card Name"])
        elif mode == "Saving Bank Account":
            if not st.session_state.banks.empty:
                account_or_card = st.selectbox("Select Bank Account", st.session_state.banks["Bank Name"])
                
        amount = st.number_input("Amount", min_value=1.0, value=1000.0)
        note = st.text_input("Note / Description")
        
        submitted_inc = st.form_submit_button("Save Income")
        
        if submitted_inc:
            if mode == "Credit Card (Refund)" and account_or_card:
                idx = st.session_state.cards[st.session_state.cards["Card Name"] == account_or_card].index[0]
                st.session_state.cards.loc[idx, "Current Limit"] += amount
            elif mode == "Saving Bank Account" and account_or_card:
                idx = st.session_state.banks[st.session_state.banks["Bank Name"] == account_or_card].index[0]
                st.session_state.banks.loc[idx, "Current Balance"] += amount
                
            new_tx = {"Date": inc_date, "Type": "Income", "Location": "N/A", "Submenu": inc_source, "Mode": mode, "Account/Card": account_or_card if account_or_card else "Cash", "Amount": amount, "Note": note}
            st.session_state.transactions = pd.concat([st.session_state.transactions, pd.DataFrame([new_tx])], ignore_index=True)
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
                st.success(f"Bill paid successfully for {cc_name} via {bank_name}!")

# ==================== 6. REPORTS ====================
elif menu == "Reports":
    st.header("📋 Detailed Reports & Transaction History")
    if not st.session_state.transactions.empty:
        filter_type = st.selectbox("Filter Report Type", ["All", "Daily", "Weekly", "Monthly", "Yearly"])
        st.dataframe(st.session_state.transactions)
    else:
        st.info("No transactions recorded yet.")

# --- Permanent Footer ---
st.markdown("---")
st.markdown("<p style='text-align: center; color: gray; font-size: 14px;'>Designed and developed by Rahul</p>", unsafe_allow_html=True)
