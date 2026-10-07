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

  # Transactions table
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

  # Credit Card Management table
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS credit_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            card_name TEXT UNIQUE,
            billing_date INTEGER,
            due_date INTEGER,
            last_paid_month TEXT DEFAULT ''
        )
    """)

  # Loans & LIC (Recurring Payments) table
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS recurring_payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT UNIQUE,
            payment_type TEXT,
            amount REAL,
            frequency TEXT,
            due_day INTEGER,
            due_month INTEGER,
            payment_mode TEXT
        )
    """)

  cursor.execute("PRAGMA table_info(transactions)")
  columns = [col[1] for col in cursor.fetchall()]
  if "payment_mode" not in columns:
    cursor.execute(
        "ALTER TABLE transactions ADD COLUMN payment_mode TEXT DEFAULT 'Cash'"
    )

  cursor.execute("PRAGMA table_info(credit_cards)")
  cc_columns = [col[1] for col in cursor.fetchall()]
  if "last_paid_month" not in cc_columns:
    cursor.execute(
        "ALTER TABLE credit_cards ADD COLUMN last_paid_month TEXT DEFAULT ''"
    )

  conn.commit()
  return conn


conn = init_db()
cursor = conn.cursor()

# Pre-populate default credit cards if table is empty
cursor.execute("SELECT COUNT(*) FROM credit_cards")
if cursor.fetchone()[0] == 0:
  initial_cards = [
      ("ICICI - 6009", 1, 15, ""),
      ("ICICI - 9003", 1, 15, ""),
      ("Axis Bank - 5302", 1, 15, ""),
      ("HDFC - 9659", 1, 15, ""),
      ("HDFC - 0152", 1, 15, ""),
      ("ICICI - 5000", 1, 15, ""),
      ("ICICI - 7006", 1, 15, ""),
      ("SBI - 0160", 1, 15, ""),
      ("SBI - 2592", 1, 15, ""),
      ("SBI - 9183", 1, 15, ""),
      ("Yes Bank - 5409", 1, 15, ""),
      ("Yes Bank - 8111", 1, 15, ""),
      ("Axis Bank - 2718", 1, 15, ""),
      ("Axis Bank - 7535", 1, 15, ""),
      ("IndusInd Bank - 7035", 1, 15, ""),
      ("IndusInd Bank - 0737", 1, 15, ""),
      ("IDFC Bank - 5258", 1, 15, ""),
      ("IDFC Bank - 4878", 1, 15, ""),
      ("IDFC Bank - 9239", 1, 15, ""),
      ("Other Credit Card", 1, 15, ""),
  ]
  cursor.executemany(
      "INSERT OR IGNORE INTO credit_cards (card_name, billing_date, due_date,"
      " last_paid_month) VALUES (?, ?, ?, ?)",
      initial_cards,
  )
  conn.commit()

# Pre-populate default loans if table is empty
cursor.execute("SELECT COUNT(*) FROM recurring_payments")
if cursor.fetchone()[0] == 0:
  initial_recurring = [
      ("Kotak Bank Loan EMI", "Loan", 10051.0, "Monthly", 2, 0, "Net Banking"),
      ("HDFC Bank Loan EMI", "Loan", 47809.0, "Monthly", 6, 0, "Net Banking"),
  ]
  cursor.executemany(
      "INSERT OR IGNORE INTO recurring_payments (item_name, payment_type,"
      " amount, frequency, due_day, due_month, payment_mode) VALUES (?, ?, ?,"
      " ?, ?, ?, ?)",
      initial_recurring,
  )
  conn.commit()


# Helper function to get sorted credit card list
def get_sorted_cc_list(cursor):
  cursor.execute("SELECT card_name FROM credit_cards")
  raw_rows = cursor.fetchall()
  raw_list = [r[0] for r in raw_rows]

  preferred = ["ICICI - 6009", "ICICI - 9003", "Axis Bank - 5302"]
  sorted_list = [c for c in preferred if c in raw_list]
  for c in raw_list:
    if c not in sorted_list:
      sorted_list.append(c)
  return sorted_list


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

# ----------------- SMART 7-DAY DUE DATE RED ALERT (ONLY IF BALANCE/TRANSACTION > 0) -----------------
today = datetime.now()
current_day = today.day
current_month = today.month
current_year = today.year
current_month_str = today.strftime("%Y-%m")

cursor.execute(
    "SELECT payment_mode, remarks FROM transactions WHERE date LIKE ?",
    (f"{current_month_str}%",),
)
trans_rows = cursor.fetchall()

for t_mode, t_remarks in trans_rows:
  if t_mode and t_mode.startswith("CC:"):
    card_n = t_mode.replace("CC: ", "").strip()
    cursor.execute(
        "UPDATE credit_cards SET last_paid_month = ? WHERE card_name = ?",
        (current_month_str, card_n),
    )
conn.commit()

cursor.execute(
    "SELECT payment_mode, amount FROM transactions WHERE date LIKE ? AND"
    " payment_mode LIKE 'CC:%'",
    (f"{current_month_str}%",),
)
cc_trans = cursor.fetchall()
card_spent_map = {}
for p_mode, amt in cc_trans:
  c_name = p_mode.replace("CC: ", "").strip()
  card_spent_map[c_name] = card_spent_map.get(c_name, 0.0) + amt

cursor.execute("SELECT card_name, due_date, last_paid_month FROM credit_cards")
all_cards_for_alert = cursor.fetchall()

alerts = []
for c_name, d_date, l_paid in all_cards_for_alert:
  if l_paid == current_month_str:
    continue

  spent_amount = card_spent_map.get(c_name, 0.0)
  if spent_amount <= 0:
    continue

  try:
    due_dt = datetime(current_year, current_month, int(d_date))
    days_left = (due_dt - today).days
    if 0 <= days_left <= 7:
      alerts.append(
          f"⚠️ **Alert:** '{c_name}' (Spent: Rs {spent_amount:,.0f}) की Due Date"
          f" **{d_date} तारीख** को है! (सिर्फ {days_left} दिन बाकी)"
      )
    elif -3 <= days_left < 0:
      alerts.append(
          f"🚨 **Urgent:** '{c_name}' (Spent: Rs {spent_amount:,.0f}) की Due"
          " Date निकल चुकी है! कृपया तुरंत भुगतान करें।"
      )
  except:
    pass

cursor.execute(
    "SELECT item_name, payment_type, amount, frequency, due_day, due_month,"
    " payment_mode FROM recurring_payments"
)
rec_payments = cursor.fetchall()

for item_name, p_type, amt, freq, d_day, d_mon, p_mode in rec_payments:
  try:
    if freq == "Monthly":
      due_dt = datetime(current_year, current_month, int(d_day))
      days_left = (due_dt - today).days
      if 0 <= days_left <= 7:
        alerts.append(
            f"⚠️ **Upcoming {p_type}:** '{item_name}' (Rs {amt:,.0f}) की Due"
            f" Date **{d_day} तारीख** को है! ({days_left} दिन बाकी)"
        )
    elif freq == "Yearly":
      due_dt = datetime(current_year, int(d_mon), int(d_day))
      days_left = (due_dt - today).days
      if 0 <= days_left <= 7:
        alerts.append(
            f"⚠️ **Upcoming Yearly {p_type}:** '{item_name}' (Rs {amt:,.0f}) की"
            f" Due Date **{d_day}-{d_mon}** को है! ({days_left} दिन बाकी)"
        )
  except:
    pass

if alerts:
  st.error("### 🔔 Payment & Due Date Alerts")
  for alert in alerts:
    st.markdown(alert)

cursor.execute(
    "SELECT type, amount, payment_mode FROM transactions WHERE date LIKE ?",
    (f"{current_month_str}%",),
)
month_rows = cursor.fetchall()
m_income = sum([r[1] for r in month_rows if r[0] == "Income"])
m_expense = sum([r[1] for r in month_rows if r[0] == "Expense"])
m_cc_expense = sum(
    [r[1] for r in month_rows if r[0] == "Expense" and str(r[2]).startswith("CC:")]
)
m_net = m_income - m_expense

st.markdown("### 📌 इस महीने का ओवरव्यू (Current Month Dashboard)")
d1, d2, d3, d4 = st.columns(4)
d1.metric("Income", f"Rs {m_income:,.0f}")
d2.metric("Expense", f"Rs {m_expense:,.0f}")
d3.metric("Net Balance", f"Rs {m_net:,.0f}")
d4.metric("CC Expense", f"Rs {m_cc_expense:,.0f}")

st.markdown("---")

menu = [
    "Add Transaction",
    "Reports & Dashboard",
    "Detailed Summary (Expense/Income)",
    "Edit Transaction",
    "Manage Credit Cards (Dates)",
    "Manage Loans & LIC",
]
choice = st.sidebar.selectbox("Menu", menu)

# ----------------- 1. TRANSACTION ADD SECTION -----------------
if choice == "Add Transaction":
  st.subheader("📝 नया लेनदेन दर्ज करें (Add New Entry)")

  with st.form("add_trans_form", clear_on_submit=True):
    t_type = st.selectbox("Type", ["Expense", "Income"])

    location = "Income Source"
    sub_cat_options = []

    if t_type == "Expense":
      location = st.selectbox(
          "Location", ["Patna", "Barhiya", "Lakhisarai", "Others"]
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

    sub_cat = st.selectbox("Sub-Category", sub_cat_options)

    manual_cat = ""
    if sub_cat == "Others" or location == "Others":
      manual_cat = st.text_input("Type custom category name if Others")

    amount = st.number_input(
        "Amount (Rs)", min_value=0.0, format="%.2f", value=0.0
    )

    pay_modes = [
        "Cash",
        "Credit Card",
        "UPI",
        "Debit Card",
        "Net Banking",
        "Other",
    ]
    base_payment_mode = st.selectbox("Payment Mode", pay_modes)

    final_payment_mode = base_payment_mode

    if base_payment_mode == "Credit Card":
      cc_list = get_sorted_cc_list(cursor)
      credit_card_choice = st.selectbox("Select Credit Card", cc_list)
      final_payment_mode = f"CC: {credit_card_choice}"

    remarks = st.text_area("Remarks (विवरण या नोट)")
    submit_btn = st.form_submit_button("Save Transaction")

    if submit_btn:
      final_sub_cat = manual_cat.strip() if manual_cat.strip() else sub_cat

      if amount <= 0:
        st.error("कृपया सही राशि (Amount) दर्ज करें!")
      elif not final_sub_cat:
        st.error("कृपया कैटेगरी की जानकारी दें!")
      else:
        date_str = datetime.now().strftime("%Y-%m-%d")
        cursor.execute(
            "INSERT INTO transactions (date, type, location, category,"
            " sub_category, amount, payment_mode, remarks) VALUES (?, ?, ?, ?,"
            " ?, ?, ?, ?)",
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
        st.rerun()

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

    disp_df = filtered_df[
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

    export_df = disp_df.copy()
    export_df.rename(
        columns={
            "Type": "Transaction Type (Credit/Debit)",
            "Sub-Category": "Category",
            "Payment_Mode": "Payment Mode",
        },
        inplace=True,
    )
    csv_data = export_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="📥 Download Formatted Report as Excel/CSV",
        data=csv_data,
        file_name="kharcha_paani_formatted_report.csv",
        mime="text/csv",
    )

    st.markdown("### 📋 Transaction Records")
    st.dataframe(disp_df, use_container_width=True)

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

    view_type = st.radio(
        "Select What You Want to View:", ["Expense (खर्च)", "Income (आय)"]
    )
    selected_type = "Expense" if "Expense" in view_type else "Income"

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

    if selected_period == "Daily":
      sel_date = st.date_input("Select Date", value=current_date)
      filtered_view_df = filtered_view_df[
          filtered_view_df["DateTime"].dt.date == sel_date
      ]

    elif selected_period == "Weekly":
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

    total_amt = filtered_view_df["Amount"].sum()
    st.metric(
        label=f"Total {selected_type} for Selected Period",
        value=f"Rs {total_amt:,.2f}",
    )

    disp_det_df = filtered_view_df[
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

    d_export = disp_det_df.copy()
    d_export.rename(
        columns={
            "Type": "Transaction Type (Credit/Debit)",
            "Sub-Category": "Category",
            "Payment_Mode": "Payment Mode",
        },
        inplace=True,
    )
    d_csv = d_export.to_csv(index=False).encode("utf-8")

    st.download_button(
        label=f"📥 Download {selected_type} Formatted Report as CSV/Excel",
        data=d_csv,
        file_name=f"{selected_type.lower()}_detailed_report.csv",
        mime="text/csv",
    )

    st.markdown(f"### 📋 {selected_type} Records")
    if not filtered_view_df.empty:
      st.dataframe(disp_det_df, use_container_width=True)

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
      cc_list = get_sorted_cc_list(cursor)
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

# ----------------- 5. MANAGE CREDIT CARDS (BILLING & DUE DATES) -----------------
elif choice == "Manage Credit Cards (Dates)":
  st.subheader(
      "💳 क्रेडिट कार्ड बिलिंग और ड्यू डेट मैनेजर (Credit Card Date Setup)"
  )
  st.write(
      "यहाँ आप अपने सभी क्रेडिट कार्ड्स की **Billing Date** और **Due Date** सेट"
      " या अपडेट कर सकते हैं। साथ ही 'Mark as Paid' से इस महीने का अलर्ट हटा सकते"
      " हैं।"
  )

  with st.expander("➕ नया क्रेडिट कार्ड जोड़ें"):
    with st.form("add_cc_form", clear_on_submit=True):
      new_card_name = st.text_input("Card Name (जैसे: HDFC - XXXX)")
      b_date = st.number_input(
          "Billing Date (1-31)", min_value=1, max_value=31, value=1
      )
      d_date = st.number_input(
          "Due Date (1-31)", min_value=1, max_value=31, value=15
      )
      add_cc_btn = st.form_submit_button("Save Card Details")

      if add_cc_btn:
        if new_card_name.strip():
          try:
            cursor.execute(
                "INSERT INTO credit_cards (card_name, billing_date, due_date,"
                " last_paid_month) VALUES (?, ?, ?, ?)",
                (new_card_name.strip(), b_date, d_date, ""),
            )
            conn.commit()
            st.success(f"कार्ड '{new_card_name}' सफलतापूर्वक जुड़ गया!")
            st.rerun()
          except:
            st.error("यह कार्ड पहले से मौजूद है!")
        else:
          st.error("कृपया कार्ड का नाम दर्ज करें!")

  cursor.execute(
      "SELECT id, card_name, billing_date, due_date, last_paid_month FROM"
      " credit_cards"
  )
  cc_records = cursor.fetchall()

  if cc_records:
    st.markdown("### 📋 आपके सभी क्रेडिट कार्ड्स की सूचियाँ और तिथियाँ")
    cc_df = pd.DataFrame(
        cc_records,
        columns=["ID", "Card Name", "Billing Date", "Due Date", "Last Paid"],
    )
    st.dataframe(cc_df, use_container_width=True)

    st.markdown("---")
    st.markdown(
        "### ⚡ Quick Action: Mark Card as Paid for Current Month ("
        + current_month_str
        + ")"
    )
    card_names_list = get_sorted_cc_list(cursor)
    selected_card_to_pay = st.selectbox(
        "Select Card to Mark Paid", card_names_list, key="mark_paid_sel"
    )

    if st.button("✅ Mark as Paid (भुगतान हो गया)"):
      cursor.execute(
          "UPDATE credit_cards SET last_paid_month = ? WHERE card_name = ?",
          (current_month_str, selected_card_to_pay),
      )
      conn.commit()
      st.success(
          f"🎉 कार्ड '{selected_card_to_pay}' को इस महीने के लिए Paid मार्क कर"
          " दिया गया है! अलर्ट हट गया है।"
      )
      st.rerun()

    st.markdown("---")
    st.markdown("### ✏️ किसी कार्ड की तारीख अपडेट करें")
    selected_card_to_edit = st.selectbox(
        "Choose Card to Update", card_names_list, key="update_date_sel"
    )

    cursor.execute(
        "SELECT billing_date, due_date FROM credit_cards WHERE card_name = ?",
        (selected_card_to_edit,),
    )
    curr_b, curr_d = cursor.fetchone()

    with st.form("update_cc_form", clear_on_submit=True):
      up_b = st.number_input(
          "New Billing Date",
          min_value=1,
          max_value=31,
          value=int(curr_b),
      )
      up_d = st.number_input(
          "New Due Date",
          min_value=1,
          max_value=31,
          value=int(curr_d),
      )
      up_btn = st.form_submit_button("Update Card Dates")

      if up_btn:
        cursor.execute(
            "UPDATE credit_cards SET billing_date = ?, due_date = ? WHERE"
            " card_name = ?",
            (up_b, up_d, selected_card_to_edit),
        )
        conn.commit()
        st.success(
            f"🎉 कार्ड '{selected_card_to_edit}' की तारीखें सफलतापूर्वक अपडेट"
            " हो गईं!"
        )
        st.rerun()
  else:
    st.info("कोई क्रेडिट कार्ड दर्ज नहीं है।")

# ----------------- 6. MANAGE LOANS & LIC (RECURRING PAYMENTS) -----------------
elif choice == "Manage Loans & LIC":
  st.subheader(
      "🏦 लोन और LIC / वार्षिक भुगतान मैनेजर (Loans & LIC Date Manager)"
  )
  st.write(
      "यहाँ आप अपने सभी मासिक (Monthly) लोन ईएमआई और वार्षिक (Yearly) LIC या"
      " अन्य भुगतानों को जोड़ और मैनेज कर सकते हैं।"
  )

  with st.expander("➕ नया लोन या LIC जोड़ें"):
    # Using radio outside form to trigger instant UI refresh when frequency changes
    r_freq = st.radio("Frequency", ["Monthly", "Yearly"], horizontal=True)

    with st.form("add_rec_form", clear_on_submit=True):
      r_name = st.text_input("Name (जैसे: Kotak Loan, LIC Policy No...)")
      r_type = st.selectbox("Type", ["Loan", "LIC", "Insurance", "Other"])
      r_amount = st.number_input(
          "Amount (Rs)", min_value=0.0, format="%.2f", value=0.0
      )

      r_month = 0
      r_day = 2

      if r_freq == "Yearly":
        r_month = st.selectbox(
            "Due Month (महीना चुनें)",
            list(range(1, 13)),
            format_func=lambda x: datetime(2026, x, 1).strftime("%B"),
        )
        r_day = st.number_input(
            "Due Date / Day (तारीख: 1-31)", min_value=1, max_value=31, value=1
        )
      else:
        r_day = st.number_input(
            "Due Day of Month (तारीख: 1-31)", min_value=1, max_value=31, value=2
        )

      r_pmode = st.selectbox(
          "Payment Mode", ["Net Banking", "Auto Debit", "UPI", "Cash", "Other"]
      )
      add_rec_btn = st.form_submit_button("Save Recurring Payment")

      if add_rec_btn:
        if r_name.strip() and r_amount > 0:
          try:
            cursor.execute(
                "INSERT INTO recurring_payments (item_name, payment_type,"
                " amount, frequency, due_day, due_month, payment_mode) VALUES"
                " (?, ?, ?, ?, ?, ?, ?)",
                (
                    r_name.strip(),
                    r_type,
                    r_amount,
                    r_freq,
                    r_day,
                    r_month,
                    r_pmode,
                ),
            )
            conn.commit()
            st.success(f"'{r_name}' सफलतापूर्वक जोड़ दिया गया!")
            st.rerun()
          except:
            st.error("यह नाम पहले से मौजूद है!")
        else:
          st.error("कृपया सही नाम और राशि दर्ज करें!")

  cursor.execute(
      "SELECT id, item_name, payment_type, amount, frequency, due_day,"
      " due_month, payment_mode FROM recurring_payments"
  )
  rec_records = cursor.fetchall()

  if rec_records:
    st.markdown("### 📋 आपके सभी लोन और LIC की सूचियाँ")
    rec_df = pd.DataFrame(
        rec_records,
        columns=[
            "ID",
            "Name",
            "Type",
            "Amount (Rs)",
            "Frequency",
            "Due Day",
            "Due Month",
            "Payment Mode",
        ],
    )
    st.dataframe(rec_df, use_container_width=True)

    st.markdown("---")
    st.markdown("### 🗑️ कोई लोन या LIC हटाएं")
    del_rec_id = st.number_input(
        "Enter ID to Delete", min_value=0, step=1, key="del_rec"
    )
    if st.button("Delete Entry", key="del_rec_btn"):
      if del_rec_id > 0:
        cursor.execute(
            "DELETE FROM recurring_payments WHERE id = ?", (del_rec_id,)
        )
        conn.commit()
        st.success(f"ID {del_rec_id} सफलतापूर्वक हटा दिया गया!")
        st.rerun()
  else:
    st.info("कोई लोन या LIC दर्ज नहीं है।")
