from datetime import datetime, timedelta
import sqlite3
import pandas as pd
import streamlit as st
import time

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

  # Credit Card Management table with Dynamic Limits & Opening Balance
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS credit_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            card_name TEXT UNIQUE,
            billing_date INTEGER,
            due_date INTEGER,
            total_limit REAL DEFAULT 0.0,
            opening_balance REAL DEFAULT 0.0,
            last_paid_month TEXT DEFAULT ''
        )
    """)

  # Savings Bank Accounts Management table with Overdraft Support
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS bank_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bank_name TEXT UNIQUE,
            account_number TEXT,
            opening_balance REAL DEFAULT 0.0,
            is_od INTEGER DEFAULT 0,
            od_limit REAL DEFAULT 0.0
        )
    """)

  # Loans & LIC (Recurring Payments) table
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS recurring_payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT,
            payment_type TEXT,
            amount REAL,
            frequency TEXT,
            due_day INTEGER,
            due_month INTEGER,
            payment_mode TEXT,
            last_paid_period TEXT DEFAULT ''
        )
    """)

  # Custom Sub-Categories table for Locations & Income Sources
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS custom_subcategories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_type TEXT,
            location TEXT,
            sub_category_name TEXT
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
  if "total_limit" not in cc_columns:
    cursor.execute(
        "ALTER TABLE credit_cards ADD COLUMN total_limit REAL DEFAULT 0.0"
    )
  if "opening_balance" not in cc_columns:
    cursor.execute(
        "ALTER TABLE credit_cards ADD COLUMN opening_balance REAL DEFAULT 0.0"
    )

  cursor.execute("PRAGMA table_info(bank_accounts)")
  bank_cols = [col[1] for col in cursor.fetchall()]
  if "is_od" not in bank_cols:
    cursor.execute(
        "ALTER TABLE bank_accounts ADD COLUMN is_od INTEGER DEFAULT 0"
    )
  if "od_limit" not in bank_cols:
    cursor.execute(
        "ALTER TABLE bank_accounts ADD COLUMN od_limit REAL DEFAULT 0.0"
    )

  cursor.execute("PRAGMA table_info(recurring_payments)")
  rec_columns = [col[1] for col in cursor.fetchall()]
  if "last_paid_period" not in rec_columns:
    cursor.execute(
        "ALTER TABLE recurring_payments ADD COLUMN last_paid_period TEXT DEFAULT"
        " ''"
    )

  cursor.execute("PRAGMA table_info(custom_subcategories)")
  cat_columns = [col[1] for col in cursor.fetchall()]
  if "transaction_type" not in cat_columns:
    cursor.execute(
        "ALTER TABLE custom_subcategories ADD COLUMN transaction_type TEXT"
        " DEFAULT 'Expense'"
    )

  conn.commit()
  return conn


conn = init_db()
cursor = conn.cursor()

# Pre-populate default credit cards if table is empty
cursor.execute("SELECT COUNT(*) FROM credit_cards")
if cursor.fetchone()[0] == 0:
  initial_cards = [
      ("ICICI - 6009", 1, 15, 100000.0, 0.0, ""),
      ("ICICI - 9003", 1, 15, 100000.0, 0.0, ""),
      ("Axis Bank - 5302", 1, 15, 100000.0, 0.0, ""),
      ("HDFC - 9659", 1, 15, 100000.0, 0.0, ""),
      ("HDFC - 0152", 1, 15, 100000.0, 0.0, ""),
      ("ICICI - 5000", 1, 15, 100000.0, 0.0, ""),
      ("ICICI - 7006", 1, 15, 100000.0, 0.0, ""),
      ("SBI - 0160", 1, 15, 100000.0, 0.0, ""),
      ("SBI - 2592", 1, 15, 100000.0, 0.0, ""),
      ("SBI - 9183", 1, 15, 100000.0, 0.0, ""),
      ("Yes Bank - 5409", 1, 15, 100000.0, 0.0, ""),
      ("Yes Bank - 8111", 1, 15, 100000.0, 0.0, ""),
      ("Axis Bank - 2718", 1, 15, 100000.0, 0.0, ""),
      ("Axis Bank - 7535", 1, 15, 100000.0, 0.0, ""),
      ("IndusInd Bank - 7035", 1, 15, 100000.0, 0.0, ""),
      ("IndusInd Bank - 0737", 1, 15, 100000.0, 0.0, ""),
      ("IDFC Bank - 5258", 1, 15, 100000.0, 0.0, ""),
      ("IDFC Bank - 4878", 1, 15, 100000.0, 0.0, ""),
      ("IDFC Bank - 9239", 1, 15, 100000.0, 0.0, ""),
      ("Other Credit Card", 1, 15, 100000.0, 0.0, ""),
  ]
  cursor.executemany(
      "INSERT OR IGNORE INTO credit_cards (card_name, billing_date, due_date,"
      " total_limit, opening_balance, last_paid_month) VALUES (?, ?, ?, ?, ?,"
      " ?)",
      initial_cards,
  )
  conn.commit()

# Pre-populate default savings/OD bank accounts if table is empty
cursor.execute("SELECT COUNT(*) FROM bank_accounts")
if cursor.fetchone()[0] == 0:
  initial_banks = [
      ("PNB OD A/c", "XXXX9999", 66000.0, 1, 211000.0),
      ("SBI Salary A/c", "XXXX1234", 25000.0, 0, 0.0),
      ("HDFC Savings A/c", "XXXX5678", 10000.0, 0, 0.0),
  ]
  cursor.executemany(
      "INSERT OR IGNORE INTO bank_accounts (bank_name, account_number,"
      " opening_balance, is_od, od_limit) VALUES (?, ?, ?, ?, ?)",
      initial_banks,
  )
  conn.commit()

# Pre-populate default loans if table is empty
cursor.execute("SELECT COUNT(*) FROM recurring_payments")
if cursor.fetchone()[0] == 0:
  initial_recurring = [
      (
          "Kotak Bank Loan EMI",
          "Loan",
          10051.0,
          "Monthly",
          2,
          0,
          "Net Banking",
          "",
      ),
      ("HDFC Bank Loan EMI", "Loan", 47809.0, "Monthly", 6, 0, "Net Banking", ""),
  ]
  cursor.executemany(
      "INSERT OR IGNORE INTO recurring_payments (item_name, payment_type,"
      " amount, frequency, due_day, due_month, payment_mode, last_paid_period)"
      " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
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


# Helper function to get bank accounts list
def get_sorted_bank_list(cursor):
  cursor.execute("SELECT bank_name FROM bank_accounts")
  rows = cursor.fetchall()
  return [r[0] for r in rows]


# Helper function for dynamic locations/sources
def get_locations_for_type(cursor, trans_type):
  if trans_type == "Expense":
    base_locs = ["Patna", "Barhiya", "Lakhisarai", "Others"]
  elif trans_type == "Income":
    base_locs = ["Income Source"]
  else:
    base_locs = ["Bank Transfer"]

  cursor.execute(
      "SELECT DISTINCT location FROM custom_subcategories WHERE"
      " transaction_type = ?",
      (trans_type,),
  )
  rows = cursor.fetchall()
  for r in rows:
    if r[0] not in base_locs:
      base_locs.insert(-1, r[0])
  return base_locs


def get_subcategories_for_location(cursor, trans_type, location):
  if trans_type == "Expense":
    defaults = {
        "Patna": [
            "Room Misc.",
            "Room Rishi",
            "Office",
            "Room Rent",
            "Loan/LIC",
            "Self",
            "Room Others",
            "Lagguage",
            "Lending to Friend / Advance",
            "Others",
        ],
        "Barhiya": [
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
        ],
        "Lakhisarai": ["Breakfast", "Toys", "Books", "Smita G", "Others"],
        "Others": ["Manual Entry (Others)"],
    }
    base_list = defaults.get(location, ["Others"])
  elif trans_type == "Income":
    defaults_inc = {
        "Income Source": [
            "Salary",
            "Refund From Amazon",
            "Refund From Flipkart",
            "Refund From Other Online Platform",
            "Loan Recovery / Friend Return",
            "Non-Income Deposit",
            "Smita G",
            "Office",
            "Advocate",
            "Others",
        ]
    }
    base_list = defaults_inc.get(location, ["Others"])
  else:
    base_list = ["Self Bank Transfer"]

  cursor.execute(
      "SELECT sub_category_name FROM custom_subcategories WHERE"
      " transaction_type = ? AND location = ?",
      (trans_type, location),
  )
  custom_rows = cursor.fetchall()
  for r in custom_rows:
    if r[0] not in base_list:
      base_list.insert(-1, r[0])

  return base_list


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
    "अपने दैनिक, मासिक, वार्षिक और क्रेडिट कार्ड / बैंक खातों के हिसाब से"
    " आय-व्यय का पूरा हिसाब रखें।"
)

# Helper for Indian Standard Time (IST)
IST_OFFSET = timedelta(hours=5, minutes=30)


def get_current_ist_date():
  return (datetime.utcnow() + IST_OFFSET).date()


def get_current_ist_datetime():
  return datetime.utcnow() + IST_OFFSET


today = get_current_ist_datetime()
current_day = today.day
current_month = today.month
current_year = today.year
current_month_str = today.strftime("%Y-%m")
current_year_str = str(current_year)

# ----------------- SMART ALERTS WITH AUTO-DETECT FOR CC & LOANS/LIC -----------------
cursor.execute(
    "SELECT payment_mode FROM transactions WHERE date LIKE ?",
    (f"{current_month_str}%",),
)
trans_rows = cursor.fetchall()

for (t_mode,) in trans_rows:
  if t_mode and t_mode.startswith("CC:"):
    card_n = t_mode.replace("CC: ", "").strip()
    cursor.execute(
        "UPDATE credit_cards SET last_paid_month = ? WHERE card_name = ?",
        (current_month_str, card_n),
    )

cursor.execute(
    "SELECT sub_category, remarks, amount FROM transactions WHERE date LIKE ?",
    (f"{current_month_str}%",),
)
all_trans = cursor.fetchall()

cursor.execute(
    "SELECT id, item_name, frequency, due_month FROM recurring_payments"
)
rec_items = cursor.fetchall()

for r_id, i_name, freq, d_mon in rec_items:
  paid_matched = False
  for sub_c, rem, amt in all_trans:
    if (i_name.lower() in str(sub_c).lower()) or (
        i_name.lower() in str(rem).lower()
    ):
      paid_matched = True
      break

  if paid_matched:
    paid_period_val = (
        current_month_str if freq == "Monthly" else current_year_str
    )
    cursor.execute(
        "UPDATE recurring_payments SET last_paid_period = ? WHERE id = ?",
        (paid_period_val, r_id),
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
    "SELECT id, item_name, payment_type, amount, frequency, due_day,"
    " due_month, payment_mode, last_paid_period FROM recurring_payments"
)
rec_payments = cursor.fetchall()

for r_id, item_name, p_type, amt, freq, d_day, d_mon, p_mode, l_paid_per in (
    rec_payments
):
  if freq == "Monthly" and l_paid_per == current_month_str:
    continue
  if freq == "Yearly" and l_paid_per == current_year_str:
    continue

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
      if current_month == int(d_mon):
        month_name = datetime(2026, int(d_mon), 1).strftime("%B")
        due_dt = datetime(current_year, int(d_mon), int(d_day))
        days_left = (due_dt - today).days
        if 0 <= days_left <= 7:
          alerts.append(
              f"⚠️ **Upcoming Yearly {p_type}:** '{item_name}' (Rs {amt:,.0f})"
              f" की Due Date **{d_day} {month_name}** को है! ({days_left} दिन"
              f" बाकी)"
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
    "Self Bank Transfer",
    "Credit Card Bill Payment",
    "Reports & Dashboard",
    "Detailed Summary (Expense/Income)",
    "Edit Transaction",
    "Manage Credit Cards",
    "Manage Bank Accounts",
    "Manage Loans & LIC",
    "Manage Categories",
]
choice = st.sidebar.selectbox("Menu", menu, key="main_menu_selectbox")

# ----------------- 1. TRANSACTION ADD SECTION -----------------
if choice == "Add Transaction":
  st.subheader("📝 नया लेनदेन दर्ज करें (Add New Entry)")

  t_type = st.selectbox("Type", ["Expense", "Income"])

  base_pay_category = st.selectbox(
      "Payment Mode / Source Category",
      ["Cash", "Savings Bank Account", "Credit Card", "UPI", "Net Banking", "Debit Card", "Other"]
  )

  final_payment_mode = base_pay_category
  if base_pay_category == "Credit Card":
    cc_list = get_sorted_cc_list(cursor)
    if cc_list:
      selected_card = st.selectbox("Select Specific Credit Card", cc_list)
      final_payment_mode = f"CC: {selected_card}"
    else:
      st.warning("कोई क्रेडिट कार्ड उपलब्ध नहीं है। कृपया पहले कार्ड जोड़ें।")
  elif base_pay_category == "Savings Bank Account":
    bank_list = get_sorted_bank_list(cursor)
    if bank_list:
      selected_bank = st.selectbox("Select Specific Bank Account", bank_list)
      final_payment_mode = f"Bank: {selected_bank}"
    else:
      st.warning("कोई बैंक खाता उपलब्ध नहीं है। कृपया पहले बैंक जोड़ें।")

  with st.form("add_trans_form", clear_on_submit=True):
    trans_date = st.date_input("Transaction Date", value=get_current_ist_date())

    loc_options = get_locations_for_type(cursor, t_type)
    location = st.selectbox(
        "Location / Main Menu" if t_type == "Expense" else "Income Source Menu",
        loc_options,
    )

    sub_cat_options = get_subcategories_for_location(cursor, t_type, location)
    sub_cat = st.selectbox("Sub-Category / Item", sub_cat_options)

    manual_cat = ""
    if sub_cat == "Others" or location == "Others":
      manual_cat = st.text_input("Type custom category name if Others")

    amount = st.number_input(
        "Amount (Rs)", min_value=0.0, format="%.2f", value=0.0
    )

    remarks = st.text_area("Remarks (विवरण या नोट)")
    submit_btn = st.form_submit_button("Save Transaction")

    if submit_btn:
      final_sub_cat = manual_cat.strip() if manual_cat.strip() else sub_cat

      if amount <= 0:
        st.error("कृपया सही राशि (Amount) दर्ज करें!")
      elif not final_sub_cat:
        st.error("कृपया कैटेगरी की जानकारी दें!")
      else:
        date_str = trans_date.strftime("%Y-%m-%d")
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
        success_ph = st.empty()
        success_ph.success("🎉 लेनदेन सफलतापूर्वक सुरक्षित हो गया!")
        time.sleep(1.5)
        success_ph.empty()
        st.rerun()

# ----------------- 1.1 SELF BANK TRANSFER SECTION -----------------
elif choice == "Self Bank Transfer":
  st.subheader("🔄 आपसी बैंक ट्रांसफर (Self Bank Transfer)")
  st.write(
      "अपने ही एक बैंक खाते से दूसरे बैंक खाते में पैसे ट्रांसफर करने के लिए"
      " यहाँ दर्ज करें।"
  )

  bank_list = get_sorted_bank_list(cursor)
  if len(bank_list) >= 2:
    with st.form("self_transfer_form", clear_on_submit=True):
      t_date = st.date_input("Transfer Date", value=get_current_ist_date())
      from_bank = st.selectbox(
          "From Bank Account (कहाँ से पैसे कटे - Debit)", bank_list, index=0
      )
      to_bank = st.selectbox(
          "To Bank Account (कहाँ पैसे पहुंचे - Credit)",
          bank_list,
          index=1 if len(bank_list) > 1 else 0,
      )
      transfer_amt = st.number_input(
          "Transfer Amount (Rs)", min_value=0.0, format="%.2f", value=0.0
      )
      transfer_remarks = st.text_area("Remarks / Note (विवरण)")
      transfer_btn = st.form_submit_button("Complete Self Transfer")

      if transfer_btn:
        if from_bank == to_bank:
          st.error("श्रोत (From) और गंतव्य (To) बैंक खाता एक ही नहीं हो सकता!")
        elif transfer_amt <= 0:
          st.error("कृपया सही ट्रांसफर राशि दर्ज करें!")
        else:
          date_s = t_date.strftime("%Y-%m-%d")
          cursor.execute(
              "INSERT INTO transactions (date, type, location, category,"
              " sub_category, amount, payment_mode, remarks) VALUES (?, ?, ?, ?,"
              " ?, ?, ?, ?)",
              (
                  date_s,
                  "Transfer",
                  "Bank Transfer",
                  "Self Transfer Out",
                  "Self Transfer Out",
                  transfer_amt,
                  f"Bank: {from_bank}",
                  (
                      f"Transferred to {to_bank}. "
                      + transfer_remarks
                  ).strip(),
              ),
          )
          cursor.execute(
              "INSERT INTO transactions (date, type, location, category,"
              " sub_category, amount, payment_mode, remarks) VALUES (?, ?, ?, ?,"
              " ?, ?, ?, ?)",
              (
                  date_s,
                  "Transfer",
                  "Bank Transfer",
                  "Self Transfer In",
                  "Self Transfer In",
                  transfer_amt,
                  f"Bank: {to_bank}",
                  (
                      f"Received from {from_bank}. "
                      + transfer_remarks
                  ).strip(),
              ),
          )
          conn.commit()
          success_ph = st.empty()
          success_ph.success(
              "🎉 आपसी बैंक ट्रांसफर सफलतापूर्वक दर्ज हो गया!"
          )
          time.sleep(1.5)
          success_ph.empty()
          st.rerun()
  else:
    st.warning(
        "सेल्फ ट्रांसफर के लिए कम से कम 2 बैंक खाते होने आवश्यक हैं। कृपया 'Manage"
        " Bank Accounts' में जाकर और बैंक जोड़ें।"
    )

# ----------------- 1.2 CREDIT CARD BILL PAYMENT SECTION -----------------
elif choice == "Credit Card Bill Payment":
  st.subheader("💳 क्रेडिट कार्ड बिल भुगतान (Credit Card Bill Payment)")
  st.write(
      "अपने बैंक खाते से क्रेडिट कार्ड का बिल चुकाने के लिए यहाँ दर्ज करें।"
      " इससे आपके बैंक खाते से पैसे कट जाएंगे और क्रेडिट कार्ड का बकाया चुकता हो जाएगा,"
      " बिना आपके दैनिक खर्चों (Expense) को प्रभावित किए।"
  )

  cc_list = get_sorted_cc_list(cursor)
  bank_list = get_sorted_bank_list(cursor)

  if cc_list and bank_list:
    with st.form("cc_bill_payment_form", clear_on_submit=True):
      pay_date = st.date_input("Payment Date", value=get_current_ist_date())
      selected_cc = st.selectbox("Select Credit Card to Pay (किस कार्ड का बिल है)", cc_list)
      selected_bank = st.selectbox("Select Bank Account (किस बैंक से भुगतान हो रहा है)", bank_list)
      bill_amount = st.number_input("Bill Payment Amount (Rs)", min_value=0.0, format="%.2f", value=0.0)
      bill_remarks = st.text_area("Remarks / Note (विवरण)")
      pay_btn = st.form_submit_button("Complete Bill Payment")

      if pay_btn:
        if bill_amount <= 0:
          st.error("कृपया सही भुगतान राशि दर्ज करें!")
        else:
          date_str = pay_date.strftime("%Y-%m-%d")
          # 1. Deduct money from Bank Account (Recorded as Transfer Out)
          cursor.execute(
              "INSERT INTO transactions (date, type, location, category, sub_category, amount, payment_mode, remarks) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
              (
                  date_str,
                  "Transfer",
                  "Bank Transfer",
                  "CC Bill Payment Out",
                  "CC Bill Payment Out",
                  bill_amount,
                  f"Bank: {selected_bank}",
                  (f"Paid bill for {selected_cc}. " + bill_remarks).strip(),
              ),
          )
          # 2. Credit/Settle amount to Credit Card (Recorded as Income/Refund to clear dues)
          cursor.execute(
              "INSERT INTO transactions (date, type, location, category, sub_category, amount, payment_mode, remarks) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
              (
                  date_str,
                  "Income",
                  "Income Source",
                  "Credit Card Bill Payment In",
                  "Credit Card Bill Payment In",
                  bill_amount,
                  f"CC: {selected_cc}",
                  (f"Bill paid via {selected_bank}. " + bill_remarks).strip(),
              ),
          )
          # Automatically mark the card as paid for current month
          cursor.execute(
              "UPDATE credit_cards SET last_paid_month = ? WHERE card_name = ?",
              (current_month_str, selected_cc),
          )
          conn.commit()
          success_ph = st.empty()
          success_ph.success("🎉 क्रेडिट कार्ड बिल भुगतान सफलतापूर्वक दर्ज हो गया!")
          time.sleep(1.5)
          success_ph.empty()
          st.rerun()
  else:
    st.warning("कृपया सुनिश्चित करें कि कम से कम 1 क्रेडिट कार्ड और 1 बैंक खाता सिस्टम में मौजूद हो।")

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
      filter_type = st.selectbox(
          "Filter by Type", ["All", "Expense", "Income", "Transfer"]
      )
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

    current_year = get_current_ist_date().year

    if period == "Monthly":
      selected_month_str = st.text_input(
          "Enter Month (YYYY-MM)",
          value=get_current_ist_date().strftime("%Y-%m"),
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
        success_ph = st.empty()
        success_ph.success(f"ID {del_id} सफलतापूर्वक हटा दिया गया!")
        time.sleep(1.5)
        success_ph.empty()
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
        "Select What You Want to View:",
        ["Expense (खर्च)", "Income (आय)", "Transfer (स्थानांतरण)"],
    )
    selected_type = (
        "Expense"
        if "Expense" in view_type
        else ("Income" if "Income" in view_type else "Transfer")
    )

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

    current_date = get_current_ist_date()
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
          "Enter Month (YYYY-MM)", value=get_current_ist_date().strftime("%Y-%m")
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

    try:
      parsed_existing_date = datetime.strptime(r_date, "%Y-%m-%d").date()
    except:
      parsed_existing_date = get_current_ist_date()

    new_date_input = st.date_input("Transaction Date", value=parsed_existing_date)

    new_type = st.selectbox(
        "Type",
        ["Expense", "Income", "Transfer"],
        index=(
            0
            if r_type == "Expense"
            else (1 if r_type == "Income" else 2)
        ),
        key="edit_type",
    )

    loc_list = get_locations_for_type(cursor, new_type)
    try:
      loc_index = loc_list.index(r_location)
    except:
      loc_index = 0

    new_location = st.selectbox(
        "Location / Main Menu", loc_list, index=loc_index, key="edit_loc"
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

    base_edit_cat = "Cash"
    specific_edit_val = ""
    if r_pay_mode.startswith("CC: "):
      base_edit_cat = "Credit Card"
      specific_edit_val = r_pay_mode.replace("CC: ", "")
    elif r_pay_mode.startswith("Bank: "):
      base_edit_cat = "Savings Bank Account"
      specific_edit_val = r_pay_mode.replace("Bank: ", "")
    else:
      base_edit_cat = r_pay_mode

    edit_pay_categories = ["Cash", "Savings Bank Account", "Credit Card", "UPI", "Net Banking", "Debit Card", "Other"]
    default_cat_idx = (
        edit_pay_categories.index(base_edit_cat)
        if base_edit_cat in edit_pay_categories
        else 0
    )

    new_base_pay = st.selectbox(
        "Payment Mode / Source Category",
        edit_pay_categories,
        index=default_cat_idx,
        key="edit_base_pay",
    )

    final_edit_pay_mode = new_base_pay
    if new_base_pay == "Credit Card":
      cc_list = get_sorted_cc_list(cursor)
      cc_idx = cc_list.index(specific_edit_val) if specific_edit_val in cc_list else 0
      sel_edit_cc = st.selectbox("Select Specific Credit Card", cc_list, index=cc_idx, key="edit_cc_sel")
      final_edit_pay_mode = f"CC: {sel_edit_cc}"
    elif new_base_pay == "Savings Bank Account":
      bank_list = get_sorted_bank_list(cursor)
      bank_idx = bank_list.index(specific_edit_val) if specific_edit_val in bank_list else 0
      sel_edit_bank = st.selectbox("Select Specific Bank Account", bank_list, index=bank_idx, key="edit_bank_sel_dyn")
      final_edit_pay_mode = f"Bank: {sel_edit_bank}"

    new_remarks = st.text_area("Remarks", value=r_remarks, key="edit_remarks")

    if st.button("Update Transaction", key="edit_submit"):
      if new_amount <= 0:
        st.error("कृपया सही राशि दर्ज करें!")
      elif not new_sub_cat.strip():
        st.error("कृपया कैटेगरी दर्ज करें!")
      else:
        new_date_str = new_date_input.strftime("%Y-%m-%d")
        cursor.execute(
            "UPDATE transactions SET date = ?, type = ?, location = ?, category"
            " = ?, sub_category = ?, amount = ?, payment_mode = ?, remarks = ?"
            " WHERE id = ?",
            (
                new_date_str,
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
        success_ph = st.empty()
        success_ph.success(f"🎉 Transaction ID {edit_id} सफलतापूर्वक अपडेट हो गया!")
        time.sleep(1.5)
        success_ph.empty()
        st.rerun()
  else:
    st.warning("दर्ज की गई ID का कोई डेटा नहीं मिला। सही ID दर्ज करें।")

# ----------------- 5. MANAGE CREDIT CARDS SECTION -----------------
elif choice == "Manage Credit Cards":
  st.subheader(
      "💳 क्रेडिट कार्ड लेजर, लिमिट और स्टेटमेंट मैनेजर (Advanced CC Ledger)"
  )
  st.write(
      "यहाँ आप सभी क्रेडिट कार्ड्स की **Dynamic Total Limit**, **Opening"
      " Balance (पुराना बकाया)** और **Billing/Due Dates** मैनेज कर सकते हैं।"
  )

  with st.expander("➕ नया क्रेडिट कार्ड जोड़ें (Click to Open)"):
    with st.form("add_cc_form", clear_on_submit=True):
      new_card_name = st.text_input("Card Name (जैसे: HDFC - XXXX)")
      b_date = st.number_input(
          "Billing Date (1-31)", min_value=1, max_value=31, value=1
      )
      d_date = st.number_input(
          "Due Date (1-31)", min_value=1, max_value=31, value=15
      )
      t_limit = st.number_input(
          "Total Credit Limit (Rs)",
          min_value=0.0,
          format="%.2f",
          value=100000.0,
      )
      o_bal = st.number_input(
          "Opening Balance / Past Unsettled Dues (Rs)",
          min_value=0.0,
          format="%.2f",
          value=0.0,
      )
      add_cc_btn = st.form_submit_button("Save Card Details")

      if add_cc_btn:
        if new_card_name.strip():
          try:
            cursor.execute(
                "INSERT INTO credit_cards (card_name, billing_date, due_date,"
                " total_limit, opening_balance, last_paid_month) VALUES (?, ?,"
                " ?, ?, ?, ?)",
                (
                    new_card_name.strip(),
                    b_date,
                    d_date,
                    t_limit,
                    o_bal,
                    "",
                ),
            )
            conn.commit()
            success_ph = st.empty()
            success_ph.success(f"कार्ड '{new_card_name}' सफलतापूर्वक जुड़ गया!")
            time.sleep(1.5)
            success_ph.empty()
            st.rerun()
          except:
            st.error("यह कार्ड पहले से मौजूद है!")
        else:
          st.error("कृपया कार्ड का नाम दर्ज करें!")

  cursor.execute(
      "SELECT id, card_name, billing_date, due_date, total_limit,"
      " opening_balance, last_paid_month FROM credit_cards"
  )
  cc_records = cursor.fetchall()

  if cc_records:
    grand_total_limit = 0.0
    grand_total_spent = 0.0
    grand_total_credited = 0.0
    grand_total_opening = 0.0

    cc_summary_list = []
    for c_id, c_name, b_dt, d_dt, t_lim, o_b, l_paid in cc_records:
      grand_total_limit += t_lim
      grand_total_opening += o_b

      cursor.execute(
          "SELECT SUM(amount) FROM transactions WHERE payment_mode = ?",
          (f"CC: {c_name}",),
      )
      spent_res = cursor.fetchone()[0]
      total_spent = spent_res if spent_res else 0.0
      grand_total_spent += total_spent

      cursor.execute(
          "SELECT SUM(amount) FROM transactions WHERE type = 'Income' AND"
          " (sub_category LIKE ? OR remarks LIKE ? OR payment_mode LIKE ?)",
          (f"%{c_name}%", f"%{c_name}%", f"%CC: {c_name}%"),
      )
      credit_res = cursor.fetchone()[0]
      total_credited = credit_res if credit_res else 0.0
      grand_total_credited += total_credited

      net_outstanding = o_b + total_spent - total_credited
      available_limit = t_lim - net_outstanding

      cc_summary_list.append({
          "ID": c_id,
          "Card Name": c_name,
          "Billing Date": b_dt,
          "Due Date": d_dt,
          "Total Limit (Rs)": t_lim,
          "Opening Dues (Rs)": o_b,
          "Total Spent (Rs)": total_spent,
          "Total Paid/Refund (Rs)": total_credited,
          "Outstanding (Rs)": net_outstanding,
          "Available Limit (Rs)": available_limit,
      })

    grand_total_outstanding = (
        grand_total_opening + grand_total_spent - grand_total_credited
    )
    grand_total_available = grand_total_limit - grand_total_outstanding
    utilization_pct = (
        (grand_total_outstanding / grand_total_limit * 100)
        if grand_total_limit > 0
        else 0.0
    )

    st.markdown("### 🌐 सभी क्रेडिट कार्ड्स का मास्टर सारांश (Master Overview)")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Limit", f"Rs {grand_total_limit:,.0f}")
    m2.metric("Total Used", f"Rs {grand_total_outstanding:,.0f}")
    m3.metric("Total Available", f"Rs {grand_total_available:,.0f}")
    m4.metric("Utilization", f"{utilization_pct:.1f}%")

    st.markdown("---")
    st.markdown("### 📋 आपके सभी क्रेडिट कार्ड्स की व्यक्तिगत स्थिति")
    cc_summary_df = pd.DataFrame(cc_summary_list)
    st.dataframe(cc_summary_df, use_container_width=True)

    st.markdown("---")
    st.markdown("### 📊 विस्तृत क्रेडिट कार्ड लेजर और समय-सीमा (Detailed Statement)")

    card_names_list = get_sorted_cc_list(cursor)
    selected_ledger_card = st.selectbox(
        "Select Card to View Statement", card_names_list, key="ledger_card_sel"
    )

    cc_period = st.selectbox(
        "Select Time Period for Statement",
        [
            "All Time",
            "Monthly",
            "Quarterly",
            "Half Yearly",
            "Yearly",
            "Custom Date Range",
        ],
        key="cc_period_sel",
    )

    cursor.execute(
        "SELECT total_limit, opening_balance FROM credit_cards WHERE"
        " card_name = ?",
        (selected_ledger_card,),
    )
    card_meta = cursor.fetchone()
    c_lim = card_meta[0] if card_meta else 0.0
    c_opn = card_meta[1] if card_meta else 0.0

    cursor.execute(
        "SELECT id, date, type, location, sub_category, amount, remarks FROM"
        " transactions WHERE payment_mode = ? ORDER BY date DESC",
        (f"CC: {selected_ledger_card}",),
    )
    card_trans = cursor.fetchall()

    cursor.execute(
        "SELECT id, date, type, location, sub_category, amount, remarks FROM"
        " transactions WHERE type = 'Income' AND (sub_category LIKE ? OR"
        " remarks LIKE ?) ORDER BY date DESC",
        (f"%{selected_ledger_card}%", f"%{selected_ledger_card}%"),
    )
    card_refunds = cursor.fetchall()

    all_card_rows = card_trans + card_refunds
    if all_card_rows:
      unique_rows = {r[0]: r for r in all_card_rows}.values()
      c_df = pd.DataFrame(
          list(unique_rows),
          columns=[
              "ID",
              "Date",
              "Type",
              "Location",
              "Category",
              "Amount",
              "Remarks",
          ],
      )
      c_df["DateTime"] = pd.to_datetime(c_df["Date"])

      current_date = get_current_ist_date()
      current_year = current_date.year

      if cc_period == "Monthly":
        sel_m_str = st.text_input(
            "Enter Month (YYYY-MM)",
            value=get_current_ist_date().strftime("%Y-%m"),
            key="cc_m_input",
        )
        if sel_m_str:
          c_df = c_df[c_df["Date"].str.startswith(sel_m_str)]
      elif cc_period == "Yearly":
        sel_y_str = st.text_input(
            "Enter Year (YYYY)", value=str(current_year), key="cc_y_input"
        )
        if sel_y_str:
          c_df = c_df[c_df["Date"].str.startswith(sel_y_str)]
      elif cc_period == "Quarterly":
        q_ch = st.selectbox(
            "Select Quarter",
            ["Q1 (Jan-Mar)", "Q2 (Apr-Jun)", "Q3 (Jul-Sep)", "Q4 (Oct-Dec)"],
            key="cc_q_sel",
        )
        yr_q = st.text_input(
            "Enter Year", value=str(current_year), key="cc_q_yr"
        )
        if yr_q:
          if "Q1" in q_ch:
            m_list = [f"{yr_q}-01", f"{yr_q}-02", f"{yr_q}-03"]
          elif "Q2" in q_ch:
            m_list = [f"{yr_q}-04", f"{yr_q}-05", f"{yr_q}-06"]
          elif "Q3" in q_ch:
            m_list = [f"{yr_q}-07", f"{yr_q}-08", f"{yr_q}-09"]
          else:
            m_list = [f"{yr_q}-10", f"{yr_q}-11", f"{yr_q}-12"]
          c_df = c_df[c_df["Date"].str[:7].isin(m_list)]
      elif cc_period == "Half Yearly":
        h_ch = st.selectbox(
            "Select Half Year",
            ["H1 (Jan - Jun)", "H2 (Jul - Dec)"],
            key="cc_h_sel",
        )
        yr_h = st.text_input(
            "Enter Year", value=str(current_year), key="cc_h_yr"
        )
        if yr_h:
          if "H1" in h_ch:
            m_list = [f"{yr_h}-{m:02d}" for m in range(1, 7)]
          else:
            m_list = [f"{yr_h}-{m:02d}" for m in range(7, 13)]
          c_df = c_df[c_df["Date"].str[:7].isin(m_list)]
      elif cc_period == "Custom Date Range":
        col_cd1, col_cd2 = st.columns(2)
        with col_cd1:
          c_start = st.date_input("Start Date", key="cc_start_date")
        with col_cd2:
          c_end = st.date_input("End Date", key="cc_end_date")
        c_df = c_df[
            (c_df["DateTime"].dt.date >= c_start)
            & (c_df["DateTime"].dt.date <= c_end)
        ]

      filtered_spent = c_df[c_df["Type"] == "Expense"]["Amount"].sum()
      filtered_credited = c_df[c_df["Type"] == "Income"]["Amount"].sum()
      filtered_avail = c_lim - (
          c_opn + filtered_spent - filtered_credited
      )

      col_l1, col_l2, col_l3 = st.columns(3)
      col_l1.metric("Total Limit", f"Rs {c_lim:,.2f}")
      col_l2.metric(
          f"Spent ({cc_period})",
          f"Rs {filtered_spent:,.2f}",
      )
      col_l3.metric("Available Limit", f"Rs {filtered_avail:,.2f}")

      disp_card_df = c_df[
          ["ID", "Date", "Type", "Location", "Category", "Amount", "Remarks"]
      ]
      st.dataframe(disp_card_df, use_container_width=True)
    else:
      col_l1, col_l2, col_l3 = st.columns(3)
      col_l1.metric("Total Limit", f"Rs {c_lim:,.2f}")
      col_l2.metric("Spent (Selected Period)", "Rs 0.00")
      col_l3.metric(
          "Available Limit", f"Rs {c_lim - c_opn:,.2f}"
      )
      st.info(f"इस कार्ड से संबंधित इस अवधि में कोई लेनदेन डेटा नहीं मिला है।")

    st.markdown("---")
    with st.expander("⚙️ कार्ड की लिमिट या तारीखें एडिट करें (Click to Open)"):
      selected_card_to_edit = st.selectbox(
          "Choose Card to Modify", card_names_list, key="update_card_meta_sel"
      )

      cursor.execute(
          "SELECT billing_date, due_date, total_limit, opening_balance FROM"
          " credit_cards WHERE card_name = ?",
          (selected_card_to_edit,),
      )
      curr_b, curr_d, curr_lim, curr_opn = cursor.fetchone()

      with st.form("update_cc_meta_form", clear_on_submit=True):
        up_b = st.number_input(
            "Billing Date", min_value=1, max_value=31, value=int(curr_b)
        )
        up_d = st.number_input(
            "Due Date", min_value=1, max_value=31, value=int(curr_d)
        )
        up_lim = st.number_input(
            "Total Credit Limit (Rs)",
            min_value=0.0,
            format="%.2f",
            value=float(curr_lim),
        )
        up_opn = st.number_input(
            "Opening Balance / Past Dues (Rs)",
            min_value=0.0,
            format="%.2f",
            value=float(curr_opn),
        )
        up_btn = st.form_submit_button("Update Card Settings")

        if up_btn:
          cursor.execute(
              "UPDATE credit_cards SET billing_date = ?, due_date = ?,"
              " total_limit = ?, opening_balance = ? WHERE card_name = ?",
              (up_b, up_d, up_lim, up_opn, selected_card_to_edit),
          )
          conn.commit()
          success_ph = st.empty()
          success_ph.success(
              f"🎉 कार्ड '{selected_card_to_edit}' की डिटेल्स सफलतापूर्वक अपडेट"
              " हो गईं!"
          )
          time.sleep(1.5)
          success_ph.empty()
          st.rerun()

    st.markdown("---")
    st.markdown(
        "### ⚡ Quick Action: Mark Card as Paid for Current Month ("
        + current_month_str
        + ")"
    )
    selected_card_to_pay = st.selectbox(
        "Select Card to Mark Paid", card_names_list, key="mark_paid_sel"
    )

    if st.button("✅ Mark as Paid (भुगतान हो गया)"):
      cursor.execute(
          "UPDATE credit_cards SET last_paid_month = ? WHERE card_name = ?",
          (current_month_str, selected_card_to_pay),
      )
      conn.commit()
      success_ph = st.empty()
      success_ph.success(
          f"🎉 कार्ड '{selected_card_to_pay}' को इस महीने के लिए Paid मार्क कर"
          " दिया गया है! अलर्ट हट गया है।"
      )
      time.sleep(1.5)
      success_ph.empty()
      st.rerun()
  else:
    st.info("कोई क्रेडिट कार्ड दर्ज नहीं है।")

# ----------------- 6. MANAGE SAVINGS BANK ACCOUNTS (WITH CORRECT OD NET BALANCE LOGIC) -----------------
elif choice == "Manage Bank Accounts":
  st.subheader("🏦 सेविंग्स बैंक अकाउंट और PNB OD मैनेजर (Bank & OD Ledger)")
  st.write(
      "यहाँ आप अपने सभी सेविंग्स बैंक खाते और ओवरड्राफ्ट (OD) सुविधा वाले PNB"
      " खाते को मैनेज कर सकते हैं।"
  )

  with st.expander("➕ नया बैंक खाता या OD खाता जोड़ें (Click to Open)"):
    with st.form("add_bank_form", clear_on_submit=True):
      new_bank_name = st.text_input("Bank Name (जैसे: PNB OD A/c, SBI Salary)")
      new_acc_num = st.text_input("Account Number / Details (जैसे: XXXX1234)")
      is_od_account = st.checkbox("Is this an Overdraft (OD) Account? (क्या यह OD खाता है?)")
      new_bank_opn = st.number_input(
          "Available Balance / Opening Balance (Rs)", min_value=0.0, format="%.2f", value=0.0,
          help="यदि OD खाता है, तो वर्तमान में बचा हुआ उपलब्ध बैलेंस दर्ज करें।"
      )
      new_od_limit = st.number_input(
          "Total Sanctioned OD Limit (Rs)", min_value=0.0, format="%.2f", value=0.0,
          help="जैसे PNB के लिए 211000"
      )
      add_bank_btn = st.form_submit_button("Save Bank Account")

      if add_bank_btn:
        if new_bank_name.strip():
          try:
            od_val = 1 if is_od_account else 0
            limit_val = new_od_limit if is_od_account else 0.0
            cursor.execute(
                "INSERT INTO bank_accounts (bank_name, account_number, opening_balance, is_od, od_limit) VALUES (?, ?, ?, ?, ?)",
                (new_bank_name.strip(), new_acc_num.strip(), new_bank_opn, od_val, limit_val),
            )
            conn.commit()
            success_ph = st.empty()
            success_ph.success(f"बैंक खाता '{new_bank_name}' सफलतापूर्वक जुड़ गया!")
            time.sleep(1.5)
            success_ph.empty()
            st.rerun()
          except:
            st.error("यह बैंक खाता पहले से मौजूद है!")
        else:
          st.error("कृपया बैंक का नाम दर्ज करें!")

  cursor.execute("SELECT id, bank_name, account_number, opening_balance, is_od, od_limit FROM bank_accounts")
  bank_records = cursor.fetchall()

  if bank_records:
    bank_summary_list = []
    grand_bank_balance = 0.0

    for b_id, b_name, b_acc, b_opn, b_is_od, b_od_lim in bank_records:
      cursor.execute("SELECT SUM(amount) FROM transactions WHERE payment_mode = ?", (f"Bank: {b_name}",))
      spent_res = cursor.fetchone()[0]
      total_spent = spent_res if spent_res else 0.0

      cursor.execute("SELECT SUM(amount) FROM transactions WHERE type = 'Income' AND (sub_category LIKE ? OR remarks LIKE ? OR payment_mode LIKE ?)", (f"%{b_name}%", f"%{b_name}%", f"%Bank: {b_name}%"))
      credit_res = cursor.fetchone()[0]
      total_credited = credit_res if credit_res else 0.0

      cursor.execute("SELECT SUM(amount) FROM transactions WHERE type = 'Transfer' AND payment_mode = ? AND sub_category = 'Self Transfer Out'", (f"Bank: {b_name}",))
      tr_out_res = cursor.fetchone()[0]
      total_tr_out = tr_out_res if tr_out_res else 0.0

      cursor.execute("SELECT SUM(amount) FROM transactions WHERE type = 'Transfer' AND payment_mode = ? AND sub_category = 'Self Transfer In'", (f"Bank: {b_name}",))
      tr_in_res = cursor.fetchone()[0]
      total_tr_in = tr_in_res if tr_in_res else 0.0

      current_balance = b_opn + total_credited + total_tr_in - total_spent - total_tr_out

      if b_is_od == 1:
        used_od_amt = b_od_lim - current_balance
        net_contribution = -used_od_amt 
        display_bal_str = f"Avail: Rs {current_balance:,.2f} | Used OD (Negative): -Rs {used_od_amt:,.2f}"
        grand_bank_balance += net_contribution
      else:
        display_bal_str = f"Rs {current_balance:,.2f}"
        grand_bank_balance += current_balance

      bank_summary_list.append({
          "ID": b_id,
          "Bank Name": b_name,
          "Type": "Overdraft (OD)" if b_is_od == 1 else "Savings",
          "Account Details": b_acc,
          "Opening / Base": b_opn,
          "Current Status": display_bal_str,
      })

    st.markdown("### 🌐 सभी बैंक खातों का कुल सारांश (Master Consolidated Summary)")
    st.metric(
        "Total Net Bank Balance (Including OD Negative Dues)",
        f"Rs {grand_bank_balance:,.2f}",
    )

    st.markdown("---")
    st.markdown("### 📋 बैंक खातों की सूची और लाइव स्टेटस")
    bank_summary_df = pd.DataFrame(bank_summary_list)
    st.dataframe(bank_summary_df, use_container_width=True)

    st.markdown("---")
    st.markdown("### 📊 विशिष्ट बैंक खाते का लेजर / स्टेटमेंट (Bank Statement)")
    bank_names_list = get_sorted_bank_list(cursor)
    selected_bank_stmt = st.selectbox(
        "Select Bank Account", bank_names_list, key="bank_stmt_sel"
    )

    cursor.execute(
        "SELECT opening_balance, is_od, od_limit FROM bank_accounts WHERE bank_name = ?",
        (selected_bank_stmt,),
    )
    b_opn_val, b_is_od_val, b_od_lim_val = cursor.fetchone()

    cursor.execute(
        "SELECT id, date, type, location, sub_category, amount, remarks FROM"
        " transactions WHERE payment_mode = ? ORDER BY date DESC",
        (f"Bank: {selected_bank_stmt}",),
    )
    b_trans = cursor.fetchall()

    cursor.execute(
        "SELECT id, date, type, location, sub_category, amount, remarks FROM"
        " transactions WHERE type = 'Income' AND (sub_category LIKE ? OR"
        " remarks LIKE ?) ORDER BY date DESC",
        (f"%{selected_bank_stmt}%", f"%{selected_bank_stmt}%"),
    )
    b_inc_credits = cursor.fetchall()

    all_b_rows = b_trans + b_inc_credits
    if all_b_rows:
      unique_b_rows = {r[0]: r for r in all_b_rows}.values()
      b_df = pd.DataFrame(
          list(unique_b_rows),
          columns=[
              "ID",
              "Date",
              "Type",
              "Location",
              "Category",
              "Amount",
              "Remarks",
          ],
      )
      b_df["DateTime"] = pd.to_datetime(b_df["Date"])

      b_cred_tot = b_df[
          (b_df["Type"] == "Income")
          | (b_df["Sub-Category"] == "Self Transfer In")
      ]["Amount"].sum()
      b_deb_tot = b_df[
          (b_df["Type"] == "Expense")
          | (b_df["Sub-Category"] == "Self Transfer Out")
      ]["Amount"].sum()

      b_live_bal = b_opn_val + b_cred_tot - b_deb_tot

      col_bk1, col_bk2, col_bk3 = st.columns(3)
      if b_is_od_val == 1:
        used_od = b_od_lim_val - b_live_bal
        col_bk1.metric("Sanctioned OD Limit", f"Rs {b_od_lim_val:,.2f}")
        col_bk2.metric("Available Limit", f"Rs {b_live_bal:,.2f}")
        col_bk3.metric("Used OD (Negative)", f"-Rs {used_od:,.2f}")
      else:
        col_bk1.metric("Opening Balance", f"Rs {b_opn_val:,.2f}")
        col_bk2.metric("Money In / Out", f"In: {b_cred_tot:,.2f} | Out: {b_deb_tot:,.2f}")
        col_bk3.metric("Current Balance", f"Rs {b_live_bal:,.2f}")

      disp_bank_df = b_df[
          ["ID", "Date", "Type", "Location", "Category", "Amount", "Remarks"]
      ]
      st.dataframe(disp_bank_df, use_container_width=True)
    else:
      col_bk1, col_bk2, col_bk3 = st.columns(3)
      if b_is_od_val == 1:
        used_od = b_od_lim_val - b_opn_val
        col_bk1.metric("Sanctioned OD Limit", f"Rs {b_od_lim_val:,.2f}")
        col_bk2.metric("Available Limit", f"Rs {b_opn_val:,.2f}")
        col_bk3.metric("Used OD (Negative)", f"-Rs {used_od:,.2f}")
      else:
        col_bk1.metric("Opening Balance", f"Rs {b_opn_val:,.2f}")
        col_bk2.metric("Money In / Out", "In: 0.00 | Out: 0.00")
        col_bk3.metric("Current Balance", f"Rs {b_opn_val:,.2f}")
      st.info("इस बैंक खाते से संबंधित कोई लेनदेन डेटा नहीं मिला है।")

    st.markdown("---")
    with st.expander("⚙️ बैंक खाता या OD डिटेल्स संपादित करें / डिलीट करें (Click to Open)"):
      selected_bank_to_edit = st.selectbox(
          "Choose Bank to Modify / Delete", bank_names_list, key="edit_bank_sel"
      )
      cursor.execute(
          "SELECT id, account_number, opening_balance, is_od, od_limit FROM bank_accounts WHERE"
          " bank_name = ?",
          (selected_bank_to_edit,),
      )
      b_id_val, curr_acc, curr_b_opn, curr_is_od, curr_od_lim = cursor.fetchone()

      with st.form("update_bank_form", clear_on_submit=True):
        up_acc_num = st.text_input("Account Number", value=str(curr_acc))
        up_is_od = st.checkbox("Is Overdraft Account?", value=bool(curr_is_od))
        up_b_opn = st.number_input(
            "Available / Opening Balance (Rs)",
            min_value=0.0,
            format="%.2f",
            value=float(curr_b_opn),
        )
        up_od_lim = st.number_input(
            "Total OD Limit (Rs)",
            min_value=0.0,
            format="%.2f",
            value=float(curr_od_lim),
        )
        up_bank_btn = st.form_submit_button("Update Bank Details")

        if up_bank_btn:
          cursor.execute(
              "UPDATE bank_accounts SET account_number = ?, opening_balance = ?, is_od = ?, od_limit = ?"
              " WHERE bank_name = ?",
              (up_acc_num, up_b_opn, 1 if up_is_od else 0, up_od_lim, selected_bank_to_edit),
          )
          conn.commit()
          success_ph = st.empty()
          success_ph.success("🎉 बैंक विवरण सफलतापूर्वक अपडेट हो गया!")
          time.sleep(1.5)
          success_ph.empty()
          st.rerun()

      if st.button("🗑️ Delete Selected Bank Account", key="del_bank_btn"):
        cursor.execute("DELETE FROM bank_accounts WHERE id = ?", (b_id_val,))
        conn.commit()
        success_ph = st.empty()
        success_ph.success(
            f"बैंक खाता '{selected_bank_to_edit}' सफलतापूर्वक हटा दिया गया!"
        )
        time.sleep(1.5)
        success_ph.empty()
        st.rerun()
  else:
    st.info("कोई बैंक खाता दर्ज नहीं है। कृपया नया बैंक खाता जोड़ें।")

# ----------------- 7. MANAGE LOANS & LIC (RECURRING PAYMENTS) -----------------
elif choice == "Manage Loans & LIC":
  st.subheader(
      "🏦 लोन और LIC / वार्षिक भुगतान मैनेजर (Loans & LIC Date Manager)"
  )
  st.write(
      "यहाँ आप अपने सभी मासिक (Monthly) लोन ईएमआई और वार्षिक (Yearly) LIC या"
      " अन्य भुगतानों को जोड़ और मैनेज कर सकते हैं।"
  )

  with st.expander("➕ नया लोन या LIC जोड़ें (Click to Open)"):
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
        r_month_name = st.selectbox(
            "Due Month (महीना चुनें)",
            [
                "January",
                "February",
                "March",
                "April",
                "May",
                "June",
                "July",
                "August",
                "September",
                "October",
                "November",
                "December",
            ],
        )
        months_dict = {
            "January": 1,
            "February": 2,
            "March": 3,
            "April": 4,
            "May": 5,
            "June": 6,
            "July": 7,
            "August": 8,
            "September": 9,
            "October": 10,
            "November": 11,
            "December": 12,
        }
        r_month = months_dict[r_month_name]
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
          cursor.execute(
              "INSERT INTO recurring_payments (item_name, payment_type, amount,"
              " frequency, due_day, due_month, payment_mode, last_paid_period)"
              " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
              (
                  r_name.strip(),
                  r_type,
                  r_amount,
                  r_freq,
                  r_day,
                  r_month,
                  r_pmode,
                  "",
              ),
          )
          conn.commit()
          success_ph = st.empty()
          success_ph.success(f"'{r_name}' सफलतापूर्वक जोड़ दिया गया!")
          time.sleep(1.5)
          success_ph.empty()
          st.rerun()
        else:
          st.error("कृपया सही नाम और राशि दर्ज करें!")

  cursor.execute(
      "SELECT id, item_name, payment_type, amount, frequency, due_day,"
      " due_month, payment_mode, last_paid_period FROM recurring_payments"
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
            "Last Paid",
        ],
    )
    months_map = {
        1: "Jan",
        2: "Feb",
        3: "Mar",
        4: "Apr",
        5: "May",
        6: "Jun",
        7: "Jul",
        8: "Aug",
        9: "Sep",
        10: "Oct",
        11: "Nov",
        12: "Dec",
    }
    rec_df["Due Month"] = rec_df["Due Month"].apply(
        lambda x: months_map.get(int(x), "-") if int(x) in months_map else "-"
    )
    st.dataframe(rec_df, use_container_width=True)

    st.markdown("---")
    st.markdown(
        "### ⚡ Quick Action: Mark Loan / LIC as Paid ("
        + current_month_str
        + " / "
        + current_year_str
        + ")"
    )
    rec_names_list = [r[1] for r in rec_records]
    selected_rec_to_pay = st.selectbox(
        "Select Loan / LIC to Mark Paid", rec_names_list, key="mark_rec_paid_sel"
    )

    cursor.execute(
        "SELECT frequency FROM recurring_payments WHERE item_name = ?",
        (selected_rec_to_pay,),
    )
    rec_freq_res = cursor.fetchone()
    item_freq = rec_freq_res[0] if rec_freq_res else "Monthly"

    if st.button("✅ Mark Loan/LIC as Paid (भुगतान हो गया)"):
      paid_val = (
          current_month_str if item_freq == "Monthly" else current_year_str
      )
      cursor.execute(
          "UPDATE recurring_payments SET last_paid_period = ? WHERE item_name"
          " = ?",
          (paid_val, selected_rec_to_pay),
      )
      conn.commit()
      success_ph = st.empty()
      success_ph.success(
          f"🎉 '{selected_rec_to_pay}' का भुगतान दर्ज हो गया है! अलर्ट हट गया"
          " है।"
      )
      time.sleep(1.5)
      success_ph.empty()
      st.rerun()

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
        success_ph = st.empty()
        success_ph.success(f"ID {del_rec_id} सफलतापूर्वक हटा दिया गया!")
        time.sleep(1.5)
        success_ph.empty()
        st.rerun()
  else:
    st.info("कोई लोन या LIC दर्ज नहीं है।")

# ----------------- 8. MANAGE CATEGORIES (DYNAMIC TYPES & SUB-CATEGORIES) -----------------
elif choice == "Manage Categories":
  st.subheader(
      "🏷️ मेनू और सब-कैटेगरी मैनेजर (Dynamic Menu & Sub-Category Manager)"
  )
  st.write(
      "यहाँ आप **Expense** या **Income** दोनों के लिए नए मेनू और सब-कैटेगरी"
      " खुद जोड़ सकते हैं।"
  )

  with st.expander("➕ नई कैटेगरी जोड़ें (Click to Open)"):
    with st.form("add_cat_form", clear_on_submit=True):
      sel_type = st.selectbox("Select Transaction Type", ["Expense", "Income"])

      current_locs = get_locations_for_type(cursor, sel_type)
      sel_loc = st.selectbox("Select Main Menu / Location", current_locs)

      new_sub_name = st.text_input(
          "New Sub-Category / Item Name (जैसे: Bonus, Fuel, Rent...)"
      )
      add_cat_btn = st.form_submit_button("Add Sub-Category / Item")

      if add_cat_btn:
        if new_sub_name.strip():
          try:
            cursor.execute(
                "INSERT INTO custom_subcategories (transaction_type, location,"
                " sub_category_name) VALUES (?, ?, ?)",
                (sel_type, sel_loc, new_sub_name.strip()),
            )
            conn.commit()
            success_ph = st.empty()
            success_ph.success(
                f"'{new_sub_name.strip()}' को [{sel_type} -> {sel_loc}] के अंतर्गत"
                " सफलतापूर्वक जोड़ दिया गया है!"
            )
            time.sleep(1.5)
            success_ph.empty()
            st.rerun()
          except:
            st.error("यह सब-कैटेगरी पहले से इस मेनू में मौजूद है!")
        else:
          st.error("कृपया सब-कैटेगरी का नाम दर्ज करें!")

  cursor.execute(
      "SELECT id, transaction_type, location, sub_category_name FROM"
      " custom_subcategories"
  )
  cat_records = cursor.fetchall()

  if cat_records:
    st.markdown("### 📋 आपके द्वारा जोड़ी गई कस्टम कैटेगरी की सूचियाँ")
    cat_df = pd.DataFrame(
        cat_records,
        columns=["ID", "Type", "Main Menu / Location", "Sub-Category Name"],
    )
    st.dataframe(cat_df, use_container_width=True)

    st.markdown("---")
    st.markdown("### 🗑️ कोई कस्टम कैटेगरी हटाएं")
    del_cat_id = st.number_input(
        "Enter ID to Delete Category", min_value=0, step=1, key="del_cat"
    )
    if st.button("Delete Category", key="del_cat_btn"):
      if del_cat_id > 0:
        cursor.execute(
            "DELETE FROM custom_subcategories WHERE id = ?", (del_cat_id,)
        )
        conn.commit()
        success_ph = st.empty()
        success_ph.success(f"ID {del_cat_id} सफलतापूर्वक हटा दिया गया!")
        time.sleep(1.5)
        success_ph.empty()
        st.rerun()
  else:
    st.info("अभी कोई नई कस्टम कैटेगरी नहीं जोड़ी गई है।")
