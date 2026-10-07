from datetime import datetime
import sqlite3
import pandas as pd
import streamlit as st

# पेज की सेटिंग
st.set_page_config(
    page_title="Kharcha Paani - Personal Finance", page_icon="💰", layout="centered"
)


# डेटाबेस कनेक्शन और इनिशियलाइज़ेशन
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
            remarks TEXT
        )
    """)
  conn.commit()
  return conn


conn = init_db()
cursor = conn.cursor()

st.title("💰 Kharcha Paani")
st.write(
    "अपने दैनिक, मासिक और वार्षिक आय-व्यय (Income & Expense) का पूरा हिसाब रखें।"
)

# मेनू चयन
menu = ["Add Transaction", "Reports & Dashboard"]
choice = st.sidebar.selectbox("Menu", menu)

# ----------------- 1. TRANSACTION ADD SECTION -----------------
if choice == "Add Transaction":
  st.subheader("📝 नया लेनदेन दर्ज करें (Add New Entry)")

  # फॉर्म के बाहर टाइप और लोकेशन रखेंगे ताकि तुरंत स्क्रीन अपडेट हो सके
  t_type = st.selectbox("Type", ["Expense", "Income"])

  location = "Income Source"
  sub_cat_options = []

  if t_type == "Expense":
    location = st.selectbox(
        "Location", ["Patna", "Barhiya", "Lakhisarai", "Others"]
    )

    if location == "Patna":
      sub_cat_options = [
          "Office",
          "Room Rent",
          "Room Misc.",
          "Room Others",
          "Room Rishi",
          "Lagguage",
          "Others",
      ]
    elif location == "Barhiya":
      sub_cat_options = [
          "Chhotu",
          "Breakfast Market",
          "Pagla Shop",
          "Ice Cream",
          "Mukhiya G",
          "Munni G",
          "Mother",
          "Father",
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

  with st.form("transaction_form"):
    sub_cat = st.selectbox("Sub-Category", sub_cat_options)

    manual_cat = ""
    if sub_cat == "Others" or location == "Others":
      manual_cat = st.text_input("Type custom category name if Others")

    amount = st.number_input("Amount (Rs)", min_value=0.0, format="%.2f")
    remarks = st.text_area("Remarks (विवरण या नोट)")

    submit_button = st.form_submit_button(label="Save Transaction")

    if submit_button:
      final_sub_cat = manual_cat.strip() if manual_cat.strip() else sub_cat

      if amount <= 0:
        st.error("कृपया सही राशि (Amount) दर्ज करें!")
      elif not final_sub_cat:
        st.error("कृपया कैटेगरी की जानकारी दें!")
      else:
        date_str = datetime.now().strftime("%Y-%m-%d")
        cursor.execute(
            "INSERT INTO transactions (date, type, location, category,"
            " sub_category, amount, remarks) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                date_str,
                t_type,
                location,
                final_sub_cat,
                final_sub_cat,
                amount,
                remarks,
            ),
        )
        conn.commit()
        st.success("🎉 लेनदेन सफलतापूर्वक सुरक्षित हो गया!")

# ----------------- 2. REPORT & DASHBOARD SECTION -----------------
elif choice == "Reports & Dashboard":
  st.subheader("📊 रिपोर्ट और विश्लेषण (Reports & View)")

  period = st.selectbox(
      "Select Period", ["All Time", "Monthly", "Yearly", "Custom Date"]
  )

  query = "SELECT id, date, type, location, sub_category, amount, remarks FROM transactions WHERE 1=1"
  params = []

  if period == "Monthly":
    month_val = st.text_input(
        "Enter Month (YYYY-MM)",
        value=datetime.now().strftime("%Y-%m"),
        placeholder="e.g. 2026-10",
    )
    if month_val:
      query += " AND date LIKE ?"
      params.append(f"{month_val}%")
  elif period == "Yearly":
    year_val = st.text_input(
        "Enter Year (YYYY)", value=datetime.now().strftime("%Y")
    )
    if year_val:
      query += " AND date LIKE ?"
      params.append(f"{year_val}%")
  elif period == "Custom Date":
    start_date = st.date_input("Start Date")
    end_date = st.date_input("End Date")
    query += " AND date BETWEEN ? AND ?"
    params.extend([str(start_date), str(end_date)])

  query += " ORDER BY id DESC"

  cursor.execute(query, params)
  rows = cursor.fetchall()

  if rows:
    df = pd.DataFrame(
        rows,
        columns=["ID", "Date", "Type", "Location", "Sub-Category", "Amount", "Remarks"],
    )

    total_income = df[df["Type"] == "Income"]["Amount"].sum()
    total_expense = df[df["Type"] == "Expense"]["Amount"].sum()
    net_balance = total_income - total_expense

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Income", f"Rs {total_income:,.2f}")
    col2.metric("Total Expense", f"Rs {total_expense:,.2f}")
    col3.metric("Net Balance", f"Rs {net_balance:,.2f}")

    st.markdown("---")
    st.dataframe(df, use_container_width=True)

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
    st.info("इस अवधि के लिए कोई डेटा उपलब्ध नहीं है।")
