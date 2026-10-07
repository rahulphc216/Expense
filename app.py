from datetime import datetime, timedelta
import sqlite3
import pandas as pd
import streamlit as st

# page setting
st.set_page_config(
    page_title="Kharcha Paani - Personal Finance", page_icon="💰", layout="centered"
)


# database connection and initialization
def init_db():
  conn = sqlite3.connect("comprehensive_finance.db", check_same_thread=False)
  cursor = conn.cursor()
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            type TEXT,
            location TEXT,
            category TEXT,
            sub_category TEXT,
            amount REAL,
            payment_mode TEXT,
            remarks TEXT
        )
    """)
  cursor.execute("PRAGMA table_info(transactions)")
  columns = [col[1] for col in cursor.fetchall()]
  if "payment_mode" not in columns:
    cursor.execute(
        "ALTER TABLE transactions ADD COLUMN payment_mode TEXT DEFAULT 'Cash'"
    )
  conn.commit()
  return conn


conn = init_db()
cursor = conn.cursor()

# title & developer branding
col1, col2 = st.columns([3, 2])
with col1:
  st.title("💰 Kharcha Paani")
with col2:
  st.markdown(
      "<p style='text-align: right; color: gray; margin-top: 20px;'><i>Developed"
      " & Designed by Rahul</i></p>",
      unsafe_allow_html=True,
  )

st.write(
    "अपने दैनिक, मासिक, वार्षिक और क्रेडिट कार्ड / भुगतान माध्यम के हिसाब से"
    " आय-व्यय का पूरा हिसाब रखें।"
)

# menu selection including the new Detailed Summary option
menu = [
    "Add Transaction",
    "Reports & Dashboard",
    "Detailed Summary (Expense/Income)",
    "Edit Transaction",
]
choice = st.sidebar.selectbox("Menu", menu)

# ----------------- 1. TRANSACTION ADD SECTION -----------------
if choice == "Add Transaction":
  st.subheader("📝 नया लेनदेन दर्ज करें (Add New Entry)")

  t_type = st.selectbox("Type", ["Expense", "Income"], key="add_type")

  location = "Income Source"
  sub_cat_options = []

  if t_type == "Expense":
    location = st.selectbox(
        "Location", ["Patna", "Barhiya", "Lakhisarai", "Others"], key="add_loc"
    )

    if location == "Patna":
      sub_cat_options = [
          "Room Misc.",
          "Room Rishi",
          "Office",
          "Room Rent",
          "Loan/LIC",
          "Self",
          "Room Others",
          "Lagguage",
          "Others",
      ]
    elif location == "Barhiya":
      sub_cat_options = [
          "Vegetable",
          "Fruit",
          "Medicine",
          "Chhotu",
          "Breakfast Market",
          "Pagla Shop",
          "Ice Cream",
          "Mukhiya G",
          "Munni G",
          "Mother",
          "Father",
          "Self",
          "Festival",
          "Misc.",
          "Others",
      ]
    elif location == "Lakhisarai":
      sub_cat_options = ["Breakfast", "Toys", "Books", "Smita G", "Others"]
    else:
      sub_cat_options = ["Manual Entry (Others)"]
  else:
    sub_cat_options = [
        "Salary",
        "Refund From Amazon",
        "Refund From Flipkart",
        "Refund From Other Online Platform",
        "Smita G",
        "Office",
        "Advocate",
        "Others",
    ]

  sub_cat = st.selectbox("Sub-Category", sub_cat_options, key="add_subcat")

  manual_cat = ""
  if sub_cat == "Others" or location == "Others":
    manual_cat = st.text_input(
        "Type custom category name if Others", key="add_manual"
    )

  amount = st.number_input(
      "Amount (Rs)", min_value=0.0, format="%.2f", value=0.0, key="add_amount"
  )

  pay_modes = ["Cash", "Credit Card", "UPI", "Debit Card", "Net Banking", "Other"]
  base_payment_mode = st.selectbox(
      "Payment Mode", pay_modes, key="add_paymode"
  )

  final_payment_mode = base_payment_mode

  if base_payment_mode == "Credit Card":
    cc_list = [
        "ICICI - 6009",
        "ICICI - 9003",
        "Axis Bank - 5302",
        "HDFC - 9659",
        "HDFC - 0152",
        "ICICI - 5000",
        "ICICI - 7006",
        "SBI - 0160",
        "SBI - 2592",
        "SBI - 9183",
        "Yes Bank - 5409",
        "Yes Bank - 8111",
        "Axis Bank - 2718",
        "Axis Bank - 7535",
        "IndusInd Bank - 7035",
        "IndusInd Bank - 0737",
        "IDFC Bank - 5258",
        "IDFC Bank - 4878",
        "IDFC Bank - 9239",
        "Other Credit Card",
    ]
    credit_card_choice = st.selectbox(
        "Select Credit Card", cc_list, key="add_cc_choice"
    )
    final_payment_mode = f"CC: {credit_card_choice}"

  remarks = st.text_area("Remarks (विवरण या नोट)", key="add_remarks")

  if st.button("Save Transaction", key="add_submit"):
    final_sub_cat = manual_cat.strip() if manual_cat.strip() else sub_cat

    if amount <= 0:
      st.error("कृपया सही राशि (Amount) दर्ज करें!")
    elif not final_sub_cat:
      st.error("कृपया कैटेगरी की जानकारी दें!")
    else:
      date_str = datetime.now().strftime("%Y-%m-%d")
      cursor.execute(
          "INSERT INTO transactions (date, type, location, category,"
          " sub_category, amount, payment_mode, remarks) VALUES (?, ?, ?, ?, ?,"
          " ?, ?, ?)",
          (
              date_str,
              t_type,
              location,
              final_sub_cat,
              final_sub_cat,
              amount,
              final_payment_mode,
              remarks,
          ),
      )
      conn.commit()
      st.success("🎉 लेनदेन सफलतापूर्वक सुरक्षित हो गया!")

# ----------------- 2. REPORT & DASHBOARD SECTION -----------------
elif choice == "Reports & Dashboard":
  st.subheader("📊 रिपोर्ट और विस्तृत विश्लेषण (Reports & Dashboard)")

  cursor.execute(
      "SELECT id, date, type, location, sub_category, amount, payment_mode,"
      " remarks FROM transactions ORDER BY id DESC"
  )
  rows = cursor.fetchall()

  if rows:
    df = pd.DataFrame(
        rows,
        columns=[
            "ID",
            "Date",
            "Type",
            "Location",
            "Sub-Category",
            "Amount",
            "Payment_Mode",
            "Remarks",
        ],
    )
    df["DateTime"] = pd.to_datetime(df["Date"])

    st.markdown("### 🔍 Filter Options")
    col_f1, col_f2, col_f3 = st.columns(3)

    with col_f1:
      filter_type = st.selectbox("Filter by Type", ["All", "Expense", "Income"])
      period = st.selectbox(
          "Select Time Period",
          [
              "All Time",
              "Monthly",
              "Quarterly",
              "Half Yearly",
              "Yearly",
              "Custom Date Range",
          ],
      )

    with col_f2:
      filter_loc = st.selectbox(
          "Filter by Location", ["All"] + list(df["Location"].unique())
      )
      filter_cat = st.selectbox(
          "Filter by Sub-Category", ["All"] + list(df["Sub-Category"].unique())
      )

    with col_f3:
      filter_pay = st.selectbox(
          "Filter by Payment Mode", ["All"] + list(df["Payment_Mode"].unique())
      )

    filtered_df = df.copy()

    if filter_type != "All":
      filtered_df = filtered_df[filtered_df["Type"] == filter_type]

    if filter_loc != "All":
      filtered_df = filtered_df[filtered_df["Location"] == filter_loc]

    if filter_cat != "All":
      filtered_df = filtered_df[filtered_df["Sub-Category"] == filter_cat]

    if filter_pay != "All":
      filtered_df = filtered_df[filtered_df["Payment_Mode"] == filter_pay]

    current_year = datetime.now().year

    if period == "Monthly":
      selected_month_str = st.text_input(
          "Enter Month (YYYY-MM)", value=datetime.now().strftime("%Y-%m")
      )
      if selected_month_str:
        filtered_df = filtered_df[
            filtered_df["Date"].str.startswith(selected_month_str)
        ]
    elif period == "Yearly":
      selected_year_str = st.text_input("Enter Year (YYYY)", value=str(current_year))
      if selected_year_str:
        filtered_df = filtered_df[
            filtered_df["Date"].str.startswith(selected_year_str)
        ]
    elif period == "Quarterly":
      q_choice = st.selectbox(
          "Select Quarter",
          ["Q1 (Jan-Mar)", "Q2 (Apr-Jun)", "Q3 (Jul-Sep)", "Q4 (Oct-Dec)"],
      )
      year_for_q = st.text_input(
          "Enter Year for Quarter", value=str(current_year), key="q_year"
      )
      if year_for_q:
        if "Q1" in q_choice:
          months = [
              f"{year_for_q}-01",
              f"{year_for_q}-02",
              f"{year_for_q}-03",
          ]
        elif "Q2" in q_choice:
          months = [
              f"{year_for_q}-04",
              f"{year_for_q}-05",
              f"{year_for_q}-06",
          ]
        elif "Q3" in q_choice:
          months = [
              f"{year_for_q}-07",
              f"{year_for_q}-08",
              f"{year_for_q}-09",
          ]
        else:
          months = [
              f"{year_for_q}-10",
              f"{year_for_q}-11",
              f"{year_for_q}-12",
          ]
        filtered_df = filtered_df[
            filtered_df["Date"].str[:7].isin(months)
        ]
    elif period == "Half Yearly":
      h_choice = st.selectbox(
          "Select Half Year",
          ["H1 (Jan - Jun)", "H2 (Jul - Dec)"],
      )
      year_for_h = st.text_input(
          "Enter Year for Half Year", value=str(current_year), key="h_year"
      )
      if year_for_h:
        if "H1" in h_choice:
          months = [f"{year_for_h}-{m:02d}" for m in range(1, 7)]
        else:
          months = [f"{year_for_h}-{m:02d}" for m in range(7, 13)]
        filtered_df = filtered_df[
            filtered_df["Date"].str[:7].isin(months)
        ]
    elif period == "Custom Date Range":
      col_d1, col_d2 = st.columns(2)
      with col_d1:
        start_date = st.date_input("Start Date")
      with col_d2:
        end_date = st.date_input("End Date")
      filtered_df = filtered_df[
          (filtered_df["DateTime"].dt.date >= start_date)
          & (filtered_df["DateTime"].dt.date <= end_date)
      ]

    st.markdown("---")

    tot_income = filtered_df[filtered_df["Type"] == "Income"]["Amount"].sum()
    tot_expense = filtered_df[filtered_df["Type"] == "Expense"]["Amount"].sum()
    net_val = tot_income - tot_expense

    m1, m2, m3 = st.columns(3)
    m1.metric("Filtered Income", f"Rs {tot_income:,.2f}")
    m2.metric("Filtered Expense", f"Rs {tot_expense:,.2f}")
    m3.metric("Net Balance", f"Rs {net_val:,.2f}")

    st.markdown("### 📋 Transaction Records")
    display_df = filtered_df[
        [
            "ID",
            "Date",
            "Type",
            "Location",
            "Sub-Category",
            "Amount",
            "Payment_Mode",
            "Remarks",
        ]
    ]
    st.dataframe(display_df, use_container_width=True)

    if not filtered_df.empty:
      col_sum1, col_sum2 = st.columns(2)

      with col_sum1:
        st.markdown("### 📊 Category Wise Breakdown")
        cat_summary = (
            filtered_df.groupby(["Type", "Location", "Sub-Category"])["Amount"]
            .sum()
            .reset_index()
        )
        cat_summary.columns = [
            "Type",
            "Location",
            "Category/Sub-Category",
            "Total (Rs)",
        ]
        st.dataframe(cat_summary, use_container_width=True)

      with col_sum2:
        st.markdown("### 💳 Payment Mode Wise Breakdown")
        pay_summary = (
            filtered_df.groupby(["Payment_Mode", "Type"])["Amount"]
            .sum()
            .reset_index()
        )
        pay_summary.columns = ["Payment Mode", "Type", "Total (Rs)"]
        st.dataframe(pay_summary, use_container_width=True)

    st.markdown("### 🗑️ Delete Transaction")
    del_id = st.number_input(
        "Enter Transaction ID to Delete", min_value=0, step=1
    )
    if st.button("Delete Entry"):
      if del_id > 0:
        cursor.execute("DELETE FROM transactions WHERE id = ?", (del_id,))
        conn.commit()
        st.success(f"ID {del_id} सफलतापूर्वक हटा दिया गया!")
        st.rerun()
  else:
    st.info("डेटाबेस में अभी कोई लेनदेन दर्ज नहीं है।")

# ----------------- 3. DETAILED SUMMARY (EXPENSE / INCOME) SECTION -----------------
elif choice == "Detailed Summary (Expense/Income)":
  st.subheader("🔍 विस्तृत आय या खर्च विवरण (Detailed Expense/Income View)")

  cursor.execute(
      "SELECT id, date, type, location, sub_category, amount, payment_mode,"
      " remarks FROM transactions ORDER BY id DESC"
  )
  rows = cursor.fetchall()

  if rows:
    df = pd.DataFrame(
        rows,
        columns=[
            "ID",
            "Date",
            "Type",
            "Location",
            "Sub-Category",
            "Amount",
            "Payment_Mode",
            "Remarks",
        ],
    )
    df["DateTime"] = pd.to_datetime(df["Date"])

    # 1. Choose between Expense or Income
    view_type = st.radio(
        "Select What You Want to View:", ["Expense (खर्च)", "Income (आय)"]
    )
    selected_type = "Expense" if "Expense" in view_type else "Income"

    # 2. Choose Time Period Option
    period_options = [
        "Daily",
        "Weekly",
        "Monthly",
        "Quarterly",
        "Half Yearly",
        "Yearly",
        "Custom Date Range",
    ]
    selected_period = st.selectbox("Select Period Type", period_options)

    current_date = datetime.now().date()
    current_year = current_date.year
    filtered_view_df = df[df["Type"] == selected_type].copy()

    # Filter based on period
    if selected_period == "Daily":
      sel_date = st.date_input("Select Date", value=current_date)
      filtered_view_df = filtered_view_df[
          filtered_view_df["DateTime"].dt.date == sel_date
      ]

    elif selected_period == "Weekly":
      # current week start and end
      start_of_week = current_date - timedelta(days=current_date.weekday())
      end_of_week = start_of_week + timedelta(days=6)
      col_w1, col_w2 = st.columns(2)
      with col_w1:
        w_start = st.date_input("Week Start Date", value=start_of_week)
      with col_w2:
        w_end = st.date_input("Week End Date", value=end_of_week)
      filtered_view_df = filtered_view_df[
          (filtered_view_df["DateTime"].dt.date >= w_start)
          & (filtered_view_df["DateTime"].dt.date <= w_end)
      ]

    elif selected_period == "Monthly":
      m_str = st.text_input(
          "Enter Month (YYYY-MM)", value=datetime.now().strftime("%Y-%m")
      )
      if m_str:
        filtered_view_df = filtered_view_df[
            filtered_view_df["Date"].str.startswith(m_str)
        ]

    elif selected_period == "Quarterly":
      q_choice = st.selectbox(
          "Select Quarter",
          ["Q1 (Jan-Mar)", "Q2 (Apr-Jun)", "Q3 (Jul-Sep)", "Q4 (Oct-Dec)"],
      )
      yr_q = st.text_input("Enter Year", value=str(current_year), key="det_q_yr")
      if yr_q:
        if "Q1" in q_choice:
          months = [f"{yr_q}-01", f"{yr_q}-02", f"{yr_q}-03"]
        elif "Q2" in q_choice:
          months = [f"{yr_q}-04", f"{yr_q}-05", f"{yr_q}-06"]
        elif "Q3" in q_choice:
          months = [f"{yr_q}-07", f"{yr_q}-08", f"{yr_q}-09"]
        else:
          months = [f"{yr_q}-10", f"{yr_q}-11", f"{yr_q}-12"]
        filtered_view_df = filtered_view_df[
            filtered_view_df["Date"].str[:7].isin(months)
        ]

    elif selected_period == "Half Yearly":
      h_choice = st.selectbox(
          "Select Half Year", ["H1 (Jan - Jun)", "H2 (Jul - Dec)"]
      )
      yr_h = st.text_input("Enter Year", value=str(current_year), key="det_h_yr")
      if yr_h:
        if "H1" in h_choice:
          months = [f"{yr_h}-{m:02d}" for m in range(1, 7)]
        else:
          months = [f"{yr_h}-{m:02d}" for m in range(7, 13)]
        filtered_view_df = filtered_view_df[
            filtered_view_df["Date"].str[:7].isin(months)
        ]

    elif selected_period == "Yearly":
      yr_str = st.text_input("Enter Year (YYYY)", value=str(current_year))
      if yr_str:
        filtered_view_df = filtered_view_df[
            filtered_view_df["Date"].str.startswith(yr_str)
        ]

    elif selected_period == "Custom Date Range":
      col_cd1, col_cd2 = st.columns(2)
      with col_cd1:
        c_start = st.date_input("Start Date", key="det_start")
      with col_cd2:
        c_end = st.date_input("End Date", key="det_end")
      filtered_view_df = filtered_view_df[
          (filtered_view_df["DateTime"].dt.date >= c_start)
          & (filtered_view_df["DateTime"].dt.date <= c_end)
      ]

    st.markdown("---")

    # Display Total Amount
    total_amt = filtered_view_df["Amount"].sum()
    st.metric(
        label=f"Total {selected_type} for Selected Period",
        value=f"Rs {total_amt:,.2f}",
    )

    st.markdown(f"### 📋 {selected_type} Records")
    if not filtered_view_df.empty:
      st.dataframe(
          filtered_view_df[
              [
                  "ID",
                  "Date",
                  "Location",
                  "Sub-Category",
                  "Amount",
                  "Payment_Mode",
                  "Remarks",
              ]
          ],
          use_container_width=True,
      )

      st.markdown("### 📊 Category & Payment Mode Wise Breakdown")
      col_b1, col_b2 = st.columns(2)

      with col_b1:
        st.markdown("**Category Breakdown**")
        cat_brk = (
            filtered_view_df.groupby(["Location", "Sub-Category"])["Amount"]
            .sum()
            .reset_index()
        )
        cat_brk.columns = ["Location", "Category", "Total (Rs)"]
        st.dataframe(cat_brk, use_container_width=True)

      with col_b2:
        st.markdown("**Payment Mode Breakdown**")
        pay_brk = (
            filtered_view_df.groupby(["Payment_Mode"])["Amount"]
            .sum()
            .reset_index()
        )
        pay_brk.columns = ["Payment Mode", "Total (Rs)"]
        st.dataframe(pay_brk, use_container_width=True)
    else:
      st.info(f"इस अवधि में कोई {selected_type} डेटा उपलब्ध नहीं है।")
  else:
    st.info("डेटाबेस में अभी कोई लेनदेन दर्ज नहीं है।")

# ----------------- 4. TRANSACTION EDIT SECTION -----------------
elif choice == "Edit Transaction":
  st.subheader("✏️ लेनदेन संपादित करें (Edit Existing Entry)")

  edit_id = st.number_input(
      "Enter Transaction ID to Edit", min_value=1, step=1
  )

  cursor.execute(
      "SELECT id, date, type, location, sub_category, amount, payment_mode,"
      " remarks FROM transactions WHERE id = ?",
      (edit_id,),
  )
  record = cursor.fetchone()

  if record:
    (
        r_id,
        r_date,
        r_type,
        r_location,
        r_sub_cat,
        r_amount,
        r_pay_mode,
        r_remarks,
    ) = record

    st.info(f"Editing Transaction ID: {r_id} (Date: {r_date})")

    new_type = st.selectbox(
        "Type",
        ["Expense", "Income"],
        index=0 if r_type == "Expense" else 1,
        key="edit_type",
    )

    loc_list = ["Patna", "Barhiya", "Lakhisarai", "Others"]
    try:
      loc_index = loc_list.index(r_location)
    except:
      loc_index = 0

    new_location = st.selectbox(
        "Location", loc_list, index=loc_index, key="edit_loc"
    )

    new_sub_cat = st.text_input(
        "Sub-Category / Category", value=r_sub_cat, key="edit_subcat"
    )
    new_amount = st.number_input(
        "Amount (Rs)",
        min_value=0.0,
        format="%.2f",
        value=float(r_amount),
        key="edit_amount",
    )

    pay_modes = ["Cash", "Credit Card", "UPI", "Debit Card", "Net Banking", "Other"]
    default_pay_idx = 0
    if r_pay_mode.startswith("CC: "):
      default_pay_idx = 1

    new_pay_mode = st.selectbox(
        "Payment Mode", pay_modes, index=default_pay_idx, key="edit_paymode"
    )

    final_edit_pay_mode = new_pay_mode
    if new_pay_mode == "Credit Card":
      cc_list = [
          "ICICI - 6009",
          "ICICI - 9003",
          "Axis Bank - 5302",
          "HDFC - 9659",
          "HDFC - 0152",
          "ICICI - 5000",
          "ICICI - 7006",
          "SBI - 0160",
          "SBI - 2592",
          "SBI - 9183",
          "Yes Bank - 5409",
          "Yes Bank - 8111",
          "Axis Bank - 2718",
          "Axis Bank - 7535",
          "IndusInd Bank - 7035",
          "IndusInd Bank - 0737",
          "IDFC Bank - 5258",
          "IDFC Bank - 4878",
          "IDFC Bank - 9239",
          "Other Credit Card",
      ]
      cc_index = 0
      extracted_card = r_pay_mode.replace("CC: ", "")
      if extracted_card in cc_list:
        cc_index = cc_list.index(extracted_card)

      selected_cc_edit = st.selectbox(
          "Select Credit Card", cc_list, index=cc_index, key="edit_cc_choice"
      )
      final_edit_pay_mode = f"CC: {selected_cc_edit}"

    new_remarks = st.text_area("Remarks", value=r_remarks, key="edit_remarks")

    if st.button("Update Transaction", key="edit_submit"):
      if new_amount <= 0:
        st.error("कृपया सही राशि दर्ज करें!")
      elif not new_sub_cat.strip():
        st.error("कृपया कैटेगरी दर्ज करें!")
      else:
        cursor.execute(
            "UPDATE transactions SET type = ?, location = ?, category = ?,"
            " sub_category = ?, amount = ?, payment_mode = ?, remarks = ? WHERE"
            " id = ?",
            (
                new_type,
                new_location,
                new_sub_cat,
                new_sub_cat,
                new_amount,
                final_edit_pay_mode,
                new_remarks,
                edit_id,
            ),
        )
        conn.commit()
        st.success(
            f"🎉 Transaction ID {edit_id} सफलतापूर्वक अपडेट हो गया!"
        )
        st.rerun()
  else:
    st.warning("दर्ज की गई ID का कोई डेटा नहीं मिला। सही ID दर्ज करें।")
