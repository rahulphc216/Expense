import pandas as pd
import streamlit as st
from datetime import datetime, date, timedelta

st.set_page_config(page_title="Personal Finance Manager", layout="wide")

# --- Initialize Session State ---
if "banks" not in st.session_state:
    st.session_state.banks = pd.DataFrame(columns=["Bank Name", "Account Type", "Opening Balance", "Current Balance", "Is OD", "OD Limit"])
    # Default PNB OD account setup as per your example
    st.session_state.banks.loc[0] = ["PNB", "Current/OD", 66634.72, 66634.72, True, 211000.0]

if "cards" not in st.session_state:
    st.session_state.cards = pd.DataFrame(columns=["Card Name", "Total Limit", "Opening Balance", "Current Limit", "Billing Date", "Due Date"])

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
        # OD Logic: Current Balance - OD Limit (e.g., 66634.72 - 211000 = -144365.28)
        return row["Current Balance"] - row["OD Limit"]
    else:
        return row["Current Balance"]

# --- Sidebar Navigation ---
st.sidebar.title("Finance Manager")
menu = st.sidebar.selectbox("Navigation", ["Dashboard", "Master Settings", "Add Expense", "Add Income", "Special Transactions", "Reports"])

# ==================== 1. MASTER SETTINGS ====================
if menu == "Master Settings":
    st.header("⚙️ Master Settings (Add/Edit/Delete)")
    
    tab1, tab2, tab3 = st.tabs(["Bank Accounts", "Credit Cards", "Location Submenus"])
    
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
        st.subheader("Manage Credit Cards (Unlimited / 10+ Cards Support)")
        with st.form("add_card_form"):
            c_name = st.text_input("Credit Card Name")
            c_limit = st.number_input("Total Limit", value=50000.0)
            c_open = st.number_input("Current Used Amount", value=0.0)
            c_bill = st.number_input("Billing Date (Day of month)", min_value=1, max_value=31, value=1)
            c_due = st.date_input("Due Date", value=date.today())
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
        st.subheader("Manage Location Submenus (Dynamic Add/Edit/Delete)")
        loc_choice = st.selectbox("Select Location", ["Patna", "Barhiya", "Lakhisarai", "Others"])
        
        col_sub1, col_sub2 = st.columns(2)
        with col_sub1:
            new_sub = st.text_input("New Submenu Name")
            if st.button("Add Submenu"):
                if new_sub:
                    # Allows same submenu name across different locations as requested
                    st.session_state.submenus[loc_choice].append(new_sub)
                    st.success(f"Added '{new_sub}' to {loc_choice}!")
                    st.rerun()
        
        st.write(f"Current Submenus in **{loc_choice}**:", st.session_state.submenus[loc_choice])
        if st.session_state.submenus[loc_choice]:
            sub_to_del = st.selectbox("Select Submenu to Delete", st.session_state.submenus[loc_choice], key="del_sub")
            if st.button("Delete Submenu"):
                st.session_state.submenus[loc_choice].remove(sub_to_del)
                st.rerun()

# ==================== 2. ADD EXPENSE ====================
elif menu == "Add Expense":
    st.header("📉 Add Expense")
    
    with st.form("expense_form"):
        exp_date = st.date_input("Date", value=date.today())
        location = st.selectbox("Location", ["Patna", "Barhiya", "Lakhisarai", "Others"])
        
        # Dynamic submenus check
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
            # Update balances accordingly
            if mode == "Credit Card" and account_or_card:
                idx = st.session_state.cards[st.session_state.cards["Card Name"] == account_or_card].index[0]
                st.session_state.cards.loc[idx, "Current Limit"] -= amount
            elif mode == "Saving Bank Account" and account_or_card:
                idx = st.session_state.banks[st.session_state.banks["Bank Name"] == account_or_card].index[0]
                st.session_state.banks.loc[idx, "Current Balance"] -= amount
                
            # Log transaction
            new_tx = {"Date": exp_date, "Type": "Expense", "Location": location, "Submenu": submenu, "Mode": mode, "Account/Card": account_or_card if account_or_card else "Cash", "Amount": amount, "Note": note}
            st.session_state.transactions = pd.concat([st.session_state.transactions, pd.DataFrame([new_tx])], ignore_index=True)
            st.success("Expense recorded successfully!")

# ==================== 3. ADD INCOME ====================
elif menu == "Add Income":
    st.header("📈 Add Income")
    
    with st.form("income_form"):
        inc_date = st.date_input("Date", value=date.today())
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

# ==================== 4. SPECIAL TRANSACTIONS ====================
elif menu == "Special Transactions":
    st.header("🔄 Special Transactions (No Income/Expense Impact)")
    
    st_type = st.selectbox("Transaction Type", ["Lent / Borrow (Udhar)", "Self-Transfer Between Accounts", "Credit Card Bill Payment"])
    
    if st_type == "Lent / Borrow (Udhar)":
        with st.form("lent_form"):
            l_date = st.date_input("Date")
            action = st.selectbox("Action", ["Given to Friend (Udhar Diya - Minus from Bank/Card, No Expense)", "Received Back from Friend (Plus to Bank/Card, No Income)"])
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
            t_date = st.date_input("Transfer Date")
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

# ==================== 5. DASHBOARD & REPORTS ====================
else:
    st.header("📊 Financial Dashboard")
    
    # 7 Days Due Date Alerts
    if not st.session_state.cards.empty:
        today = date.today()
        for idx, row in st.session_state.cards.iterrows():
            try:
                due_date = pd.to_datetime(row["Due Date"]).date()
                days_left = (due_date - today).days
                if 0 <= days_left <= 7:
                    st.warning(f"🚨 **Alert:** Credit card **{row['Card Name']}** bill due in **{days_left} days** (Due Date: {row['Due Date']})!")
            except:
                pass

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
        st.subheader("💳 Credit Cards Overview")
        if not st.session_state.cards.empty:
            c_df = st.session_state.cards.copy()
            total_limit = c_df["Total Limit"].sum()
            total_used = total_limit - c_df["Current Limit"].sum()
            usage_pct = (total_used / total_limit) * 100 if total_limit > 0 else 0
            
            st.metric("Total Credit Limit (All Cards)", f"Rs. {total_limit:,.2f}")
            st.metric("Total Used Limit", f"Rs. {total_used:,.2f}", f"{usage_pct:.1f}% used")
            st.dataframe(c_df[["Card Name", "Total Limit", "Current Limit", "Due Date"]])
        else:
            st.info("No credit cards added yet.")

    st.markdown("---")
    st.subheader("📋 Transaction History & Reports")
    if not st.session_state.transactions.empty:
        filter_type = st.selectbox("Filter Report Type", ["All", "Daily", "Weekly", "Monthly", "Yearly"])
        st.dataframe(st.session_state.transactions)
    else:
        st.info("No transactions recorded yet.")
