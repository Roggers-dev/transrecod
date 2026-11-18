import uuid
import pandas as pd
import sqlalchemy
import streamlit as st

# ---------------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------------
st.set_page_config(
    page_title="AlufaTanaah Transaction Record Keeper",
    page_icon="💰",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------
# STYLING & DEVELOPER FOOTER
# ---------------------------------------------------------
st.markdown(
    """
    <style>
    .developer-footer {
        position: fixed;
        bottom: 15px;
        left: 15px;
        background: linear-gradient(135deg, #FF4B4B, #FF914D);
        color: white;
        padding: 10px 15px;
        border-radius: 8px;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-size: 11px;
        text-align: left;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
        z-index: 99999;
        line-height: 1.3;
    }
    .developer-footer strong {
        font-size: 12px;
        letter-spacing: 0.5px;
    }
    @media print {
        header, footer, [data-testid="stSidebar"], .stButton, .stTextInput, .stSelectbox {
            display: none !important;
        }
        body {
            background-color: white !important;
        }
        .receipt-container {
            border: none !important;
            box-shadow: none !important;
            width: 100% !important;
            max-width: 100% !important;
        }
    }
    .receipt-container {
        max-width: 380px;
        margin: 20px auto;
        padding: 20px;
        background: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        font-family: monospace;
        color: #111111;
    }
    .receipt-title {
        text-align: center;
        font-weight: bold;
        font-size: 16px;
        margin-bottom: 0;
    }
    .receipt-subtitle {
        text-align: center;
        font-size: 11px;
        color: #666;
        margin-bottom: 15px;
    }
    </style>

    <div class="developer-footer">
        <strong>🚀 AlufaTanaah Record Keeper</strong><br>
        Developer: Rogers enterprises limited<br>
        📧 koffieroggers@gmail.com | Enchi
    </div>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# DATABASE CONNECTION & SETUP
# ---------------------------------------------------------
def get_sqlalchemy_engine():
  try:
    database_url = st.secrets["postgres"]["url"]
    if "postgresql://" in database_url and "+psycopg2" not in database_url:
      database_url = database_url.replace(
          "postgresql://", "postgresql+psycopg2://", 1
      )
    return sqlalchemy.create_engine(database_url)
  except Exception as e:
    st.error(f"Database Connection Error: {e}")
    st.stop()


engine = get_sqlalchemy_engine()


def init_db():
  with engine.connect() as conn:
    conn = conn.execution_options(isolation_level="AUTOCOMMIT")

    # Tables
    conn.execute(
        sqlalchemy.text("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                full_name TEXT NOT NULL,
                phone TEXT UNIQUE NOT NULL,
                email TEXT,
                password TEXT NOT NULL,
                role TEXT DEFAULT 'manager',
                status TEXT DEFAULT 'Active',
                recovery_pref TEXT DEFAULT 'Email',
                client_quota INT DEFAULT 50,
                edit_override BOOLEAN DEFAULT FALSE,
                note_override BOOLEAN DEFAULT FALSE
            )
        """)
    )

    conn.execute(
        sqlalchemy.text("""
            CREATE TABLE IF NOT EXISTS clients (
                id TEXT PRIMARY KEY,
                manager_name TEXT,
                client_name TEXT NOT NULL,
                client_phone TEXT,
                gender TEXT,
                location TEXT,
                target_limit FLOAT DEFAULT 0.0,
                date_registered TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    )

    conn.execute(
        sqlalchemy.text("""
            CREATE TABLE IF NOT EXISTS transactions (
                id SERIAL PRIMARY KEY,
                manager_name TEXT,
                client_name TEXT,
                amount FLOAT,
                trans_type TEXT,
                notes TEXT,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    )

    conn.execute(
        sqlalchemy.text("""
            CREATE TABLE IF NOT EXISTS support_tickets (
                id SERIAL PRIMARY KEY,
                manager_name TEXT,
                issue_message TEXT,
                status TEXT DEFAULT 'Pending',
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    )

    # Safe Column Migrations
    for col, typ in [
        ("client_quota", "INT DEFAULT 50"),
        ("edit_override", "BOOLEAN DEFAULT FALSE"),
        ("note_override", "BOOLEAN DEFAULT FALSE"),
        ("status", "TEXT DEFAULT 'Active'"),
        ("role", "TEXT DEFAULT 'manager'"),
        ("recovery_pref", "TEXT DEFAULT 'Email'"),
        ("email", "TEXT"),
    ]:
      try:
        conn.execute(
            sqlalchemy.text(
                f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {col} {typ};"
            )
        )
      except Exception:
        pass

    for col, typ in [
        ("gender", "TEXT"),
        ("location", "TEXT"),
        ("target_limit", "FLOAT DEFAULT 0.0"),
        ("client_phone", "TEXT"),
        ("manager_name", "TEXT"),
    ]:
      try:
        conn.execute(
            sqlalchemy.text(
                f"ALTER TABLE clients ADD COLUMN IF NOT EXISTS {col} {typ};"
            )
        )
      except Exception:
        pass

    for col, typ in [
        ("notes", "TEXT"),
        ("manager_name", "TEXT"),
        ("client_name", "TEXT"),
        ("amount", "FLOAT"),
        ("trans_type", "TEXT"),
    ]:
      try:
        conn.execute(
            sqlalchemy.text(
                f"ALTER TABLE transactions ADD COLUMN IF NOT EXISTS {col} {typ};"
            )
        )
      except Exception:
        pass

    # Seed Admin
    res = conn.execute(
        sqlalchemy.text("SELECT COUNT(*) FROM users WHERE role = 'admin'")
    ).fetchone()
    if res[0] == 0:
      conn.execute(
          sqlalchemy.text("""
                INSERT INTO users (full_name, phone, email, password, role, status, client_quota)
                VALUES ('System Admin', 'admin', 'admin@alufatanaah.com', 'admin123', 'admin', 'Active', 9999)
                ON CONFLICT (phone) DO NOTHING;
            """)
      )


init_db()


# ---------------------------------------------------------
# SESSION STATE
# ---------------------------------------------------------
if "logged_in" not in st.session_state:
  st.session_state.logged_in = False
  st.session_state.user = None


def render_auth():
  st.title("💰 AlufaTanaah Transaction Record Keeper")
  tab1, tab2, tab3 = st.tabs(
      ["Login", "Register Workspace", "Password Reset (No Data Loss)"]
  )

  with tab1:
    st.subheader("Sign In")
    login_phone = st.text_input("Phone Number or Email", key="login_id")
    login_pass = st.text_input("Password", type="password", key="login_pw")

    if st.button("Log In"):
      try:
        df = pd.read_sql(
            sqlalchemy.text(
                "SELECT id, full_name, phone, email, password, role, status,"
                " client_quota, edit_override, note_override, recovery_pref FROM"
                " users WHERE phone = :id OR email = :id"
            ),
            engine,
            params={"id": login_phone},
        )
      except Exception:
        df = pd.read_sql(
            sqlalchemy.text(
                "SELECT id, full_name, phone, password, role, status,"
                " client_quota, edit_override, note_override, recovery_pref FROM"
                " users WHERE phone = :id"
            ),
            engine,
            params={"id": login_phone},
        )

      if not df.empty:
        user = df.iloc[0]
        if user["password"] == login_pass:
          if user["status"] == "Frozen":
            st.error(
                "⚠️ Your account has been frozen by administration for audit."
            )
          else:
            st.session_state.logged_in = True
            st.session_state.user = user.to_dict()
            st.success("Login successful!")
            st.rerun()
        else:
          st.error("Incorrect password.")
      else:
        st.error("User not found.")

  with tab2:
    st.subheader("Create Workspace Account")
    reg_name = st.text_input("Full Name", key="reg_name_input")
    reg_phone = st.text_input("Phone Number", key="reg_phone_input")
    reg_email = st.text_input("Email (Optional)", key="reg_email_input")
    reg_pass = st.text_input("Password", type="password", key="reg_pass_input")
    recovery_choice = st.radio(
        "Recovery Channel:", ["Email", "Phone"], key="reg_rec_input"
    )

    if st.button("Register Account"):
      if reg_name and reg_phone and reg_pass:
        try:
          with engine.begin() as conn:
            conn.execute(
                sqlalchemy.text("""
                            INSERT INTO users (full_name, phone, email, password, role, recovery_pref, client_quota)
                            VALUES (:name, :phone, :email, :passwd, 'manager', :rec, 50)
                        """),
                {
                    "name": reg_name,
                    "phone": reg_phone,
                    "email": reg_email,
                    "passwd": reg_pass,
                    "rec": recovery_choice,
                },
            )
          st.success("Registration successful! You can now log in.")
          st.rerun()
        except Exception as e:
          st.error(f"Error registering user: {e}")
      else:
        st.warning("Please fill in Name, Phone, and Password.")

  with tab3:
    st.subheader("Secure Password Reset")
    reset_id = st.text_input("Phone Number or Email", key="reset_id_input")
    new_pass = st.text_input(
        "New Password", type="password", key="reset_new_pass"
    )
    confirm_pass = st.text_input(
        "Confirm Password", type="password", key="reset_confirm_pass"
    )

    if st.button("Reset Password Securely"):
      if reset_id and new_pass and confirm_pass:
        if new_pass == confirm_pass:
          df_check = pd.read_sql(
              sqlalchemy.text(
                  "SELECT id FROM users WHERE phone = :id OR email = :id"
              ),
              engine,
              params={"id": reset_id},
          )
          if not df_check.empty:
            with engine.begin() as conn:
              conn.execute(
                  sqlalchemy.text(
                      "UPDATE users SET password = :p WHERE phone = :id OR"
                      " email = :id"
                  ),
                  {"p": new_pass, "id": reset_id},
              )
            st.success(
                "Password successfully updated! Data remains fully intact."
            )
          else:
            st.error("No matching user found.")
        else:
          st.error("Passwords do not match.")
      else:
        st.warning("Please fill out all fields.")

          # ---------------------------------------------------------
# MAIN DASHBOARD
# ---------------------------------------------------------
def render_dashboard():
  user = st.session_state.user
  is_admin = user["role"] == "admin"

  if is_admin:
    st.sidebar.title(f"🛡️ Admin: {user['full_name']}")
    nav_options = [
        "👥 Register Client",
        "📥 Record Transaction & Receipts",
        "📊 My Clients & Records",
        "🎯 Client Target Limits",
        "📥 Export Encrypted Data (Excel/CSV)",
        "🛡️ [Admin] Manager Governance & Quotas",
        "🛠️ App Issues & Support Tickets",
    ]
  else:
    st.sidebar.title(f"👤 {user['full_name']}")
    st.sidebar.markdown("Workspace Manager")
    nav_options = [
        "👥 Register Client",
        "📥 Record Transaction & Receipts",
        "📊 My Clients & Records",
        "🎯 Client Target Limits",
        "📥 Export Encrypted Data (Excel/CSV)",
        "🛠️ Report App Issue / Problem",
    ]

  nav = st.sidebar.radio("Navigation", nav_options)

  if st.sidebar.button("Log Out"):
    st.session_state.logged_in = False
    st.session_state.user = None
    st.rerun()

  # 1. REGISTER CLIENT
  if nav == "👥 Register Client":
    st.subheader("👥 Register New Client")
    if not is_admin:
      df_count = pd.read_sql(
          sqlalchemy.text(
              "SELECT COUNT(*) as cnt FROM clients WHERE manager_name = :m"
          ),
          engine,
          params={"m": user["full_name"]},
      )
      current_count = df_count.iloc[0]["cnt"]
      quota = user["client_quota"]
      st.info(f"Quota Status: **{current_count} / {quota}** clients registered")
      if current_count >= quota:
        st.error("⚠️ Quota limit reached. Contact Admin.")
        return

    with st.form("client_reg_form", clear_on_submit=True):
      c_name = st.text_input("Client Full Name")
      c_phone = st.text_input("Client Phone Number")
      c_gender = st.selectbox("Gender", ["Male", "Female", "Other"])
      c_location = st.text_input("Location / Address")

      submitted = st.form_submit_button("Register Client")
      if submitted and c_name:
        try:
          unique_client_id = f"CLI-{str(uuid.uuid4()).upper()[:8]}"
          with engine.begin() as conn:
            conn.execute(
                sqlalchemy.text("""
                            INSERT INTO clients (id, manager_name, client_name, client_phone, gender, location)
                            VALUES (:id, :m, :name, :phone, :gender, :location)
                        """),
                {
                    "id": unique_client_id,
                    "m": user["full_name"],
                    "name": c_name,
                    "phone": c_phone,
                    "gender": c_gender,
                    "location": c_location,
                },
            )
          st.success(
              f"Client registered successfully! ID: `{unique_client_id}`"
          )
          st.rerun()
        except Exception as e:
          st.error(f"Error registering client: {e}")

  # 2. RECORD TRANSACTION & RECEIPT
  elif nav == "📥 Record Transaction & Receipts":
    st.subheader("📥 Record Daily Transaction & Generate Receipt")
    if is_admin:
      df_clients = pd.read_sql(
          sqlalchemy.text("SELECT client_name FROM clients"), engine
      )
    else:
      df_clients = pd.read_sql(
          sqlalchemy.text(
              "SELECT client_name FROM clients WHERE manager_name = :m"
          ),
          engine,
          params={"m": user["full_name"]},
      )

    client_list = (
        df_clients["client_name"].tolist() if not df_clients.empty else []
    )
    if not client_list:
      st.warning("⚠️ Please register at least one client first.")
      return

    with st.form("trans_form", clear_on_submit=True):
      client_name = st.selectbox("Select Client", client_list)
      amount = st.number_input("Amount (GHS)", min_value=0.0, step=1.0)
      trans_type = st.selectbox("Transaction Type", ["Deposit", "Withdrawal"])
      notes = st.text_area("Notes / Remarks (Locked after 24 hrs)")

      submitted = st.form_submit_button("Save Transaction & Generate Receipt")
      if submitted and amount > 0:
        with engine.begin() as conn:
          conn.execute(
              sqlalchemy.text("""
                        INSERT INTO transactions (manager_name, client_name, amount, trans_type, notes)
                        VALUES (:col, :client, :amt, :type, :notes)
                    """),
              {
                  "col": user["full_name"],
                  "client": client_name,
                  "amt": amount,
                  "type": trans_type,
                  "notes": notes,
              },
          )
        st.success("Transaction recorded successfully!")

        receipt_html = f"""
                <div class="receipt-container">
                    <p class="receipt-title">AlufaTanaah Record Keeper</p>
                    <p class="receipt-subtitle">Official Mobile Receipt</p>
                    <hr style="border: 0.5px dashed #ccc;">
                    <p><b>Date:</b> {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}</p>
                    <p><b>Client:</b> {client_name}</p>
                    <p><b>Manager:</b> {user['full_name']}</p>
                    <p><b>Type:</b> {trans_type}</p>
                    <p><b>Amount:</b> GHS {amount:.2f}</p>
                    <p><b>Remarks:</b> {notes if notes else 'None'}</p>
                    <hr style="border: 0.5px dashed #ccc;">
                    <p style="text-align:center; font-size:11px;">Thank you for saving with us!</p>
                </div>
                """
        st.markdown(receipt_html, unsafe_allow_html=True)
        st.markdown(
            """
                <div style="max-width: 380px; margin: 10px auto; text-align: center;">
                    <button onclick="window.print()" style="width:100%; background-color:#FF4B4B; color:white; border:none; padding:12px; border-radius:6px; font-weight:bold; cursor:pointer;">
                        🖨️ Save as PDF / Print Receipt
                    </button>
                </div>
                """,
            unsafe_allow_html=True,
        )

  # 3. MY CLIENTS & RECORDS
  elif nav == "📊 My Clients & Records":
    st.subheader("📊 Clients & Transaction Records")
    st.markdown("### 🔍 Search Clients")
    if is_admin:
      df_clients_all = pd.read_sql(
          sqlalchemy.text(
              "SELECT id, manager_name, client_name, client_phone, gender,"
              " location, target_limit, date_registered FROM clients"
          ),
          engine,
      )
    else:
      df_clients_all = pd.read_sql(
          sqlalchemy.text(
              "SELECT id, manager_name, client_name, client_phone, gender,"
              " location, target_limit, date_registered FROM clients WHERE"
              " manager_name = :m"
          ),
          engine,
          params={"m": user["full_name"]},
      )

    search_query = st.text_input("🔎 Search by name, phone, location, or ID:")
    if search_query:
      mask = (
          df_clients_all["client_name"]
          .str.contains(search_query, case=False, na=False)
          | df_clients_all["client_phone"]
          .str.contains(search_query, case=False, na=False)
          | df_clients_all["location"]
          .str.contains(search_query, case=False, na=False)
          | df_clients_all["id"]
          .str.contains(search_query, case=False, na=False)
      )
      df_clients_filtered = df_clients_all[mask]
    else:
      df_clients_filtered = df_clients_all

    st.dataframe(df_clients_filtered, use_container_width=True)

    st.markdown("---")
    st.subheader("📊 Transaction Records")
    if is_admin:
      df_trans = pd.read_sql(
          sqlalchemy.text(
              "SELECT id, manager_name, client_name, amount, trans_type, notes,"
              " date FROM transactions ORDER BY date DESC"
          ),
          engine,
      )
    else:
      df_trans = pd.read_sql(
          sqlalchemy.text(
              "SELECT id, manager_name, client_name, amount, trans_type, notes,"
              " date FROM transactions WHERE manager_name = :m ORDER BY date"
              " DESC"
          ),
          engine,
          params={"m": user["full_name"]},
      )

    trans_search = st.text_input("🔎 Search transactions by client name:")
    if trans_search:
      df_trans = df_trans[
          df_trans["client_name"].str.contains(
              trans_search, case=False, na=False
          )
      ]

    if not df_trans.empty:
      st.dataframe(df_trans, use_container_width=True)
      st.markdown("---")
      st.subheader("🔒 Edit / Audit Controls (24-Hour Rule)")
      edit_id = st.number_input(
          "Enter Transaction ID to Edit/Update", min_value=1, step=1
      )
      row_to_edit = df_trans[df_trans["id"] == edit_id]

      if not row_to_edit.empty:
        r = row_to_edit.iloc[0]
        trans_date = pd.to_datetime(r["date"])
        hours_elapsed = (
            pd.Timestamp.now() - trans_date.tz_localize(None)
        ).total_seconds() / 3600
        can_edit = is_admin or (
            hours_elapsed <= 24 or user.get("edit_override", False)
        )
        can_edit_notes = is_admin or user.get("note_override", False)

        if not can_edit:
          st.error(
              "⚠️ Transaction older than 24 hours. Admin auth required."
          )
        else:
          with st.form("edit_trans_form"):
            new_amt = st.number_input(
                "Update Amount (GHS)", value=float(r["amount"]), step=1.0
            )
            new_notes = st.text_area(
                "Update Remarks/Notes",
                value=str(r["notes"] if r["notes"] else ""),
                disabled=not can_edit_notes,
            )
            if st.form_submit_button("Save Changes"):
              with engine.begin() as conn:
                if can_edit_notes:
                  conn.execute(
                      sqlalchemy.text(
                          "UPDATE transactions SET amount = :amt, notes ="
                          " :notes WHERE id = :id"
                      ),
                      {"amt": new_amt, "notes": new_notes, "id": edit_id},
                  )
                else:
                  conn.execute(
                      sqlalchemy.text(
                          "UPDATE transactions SET amount = :amt WHERE id = :id"
                      ),
                      {"amt": new_amt, "id": edit_id},
                  )
              st.success("Transaction updated successfully!")
              st.rerun()
    else:
      st.info("No transaction records found.")

  # 4. TARGET LIMITS
  elif nav == "🎯 Client Target Limits":
    st.subheader("🎯 Client Target Limits")
    if is_admin:
      df_clients = pd.read_sql(
          sqlalchemy.text(
              "SELECT id, manager_name, client_name, target_limit FROM clients"
          ),
          engine,
      )
    else:
      df_clients = pd.read_sql(
          sqlalchemy.text(
              "SELECT id, manager_name, client_name, target_limit FROM clients"
              " WHERE manager_name = :m"
          ),
          engine,
          params={"m": user["full_name"]},
      )

    if not df_clients.empty:
      st.dataframe(df_clients, use_container_width=True)
      c_id_input = st.text_input("Enter Client Unique ID to Update Target Limit")
      if c_id_input:
        target_row = df_clients[df_clients["id"] == c_id_input]
        if not target_row.empty:
          tr = target_row.iloc[0]
          with st.form("target_form"):
            new_target = st.number_input(
                f"New Target for {tr['client_name']} (GHS)",
                value=float(tr["target_limit"]),
                step=10.0,
            )
            if st.form_submit_button("Update Target"):
              with engine.begin() as conn:
                conn.execute(
                    sqlalchemy.text(
                        "UPDATE clients SET target_limit = :t WHERE id = :id"
                    ),
                    {"t": new_target, "id": c_id_input},
                )
              st.success("Target limit updated successfully!")
              st.rerun()
        else:
          st.error("Client Unique ID not found.")
    else:
      st.info("No clients available.")

  # 5. EXPORT
  elif nav == "📥 Export Encrypted Data (Excel/CSV)":
    st.subheader("📥 Export Transaction Records")
    if is_admin:
      df_export = pd.read_sql(
          sqlalchemy.text("SELECT * FROM transactions"), engine
      )
    else:
      df_export = pd.read_sql(
          sqlalchemy.text(
              "SELECT * FROM transactions WHERE manager_name = :m"
          ),
          engine,
          params={"m": user["full_name"]},
      )

    if not df_export.empty:
      csv_data = df_export.to_csv(index=False).encode("utf-8")
      st.download_button(
          label="📥 Download CSV File",
          data=csv_data,
          file_name="alufatanaah_transactions_export.csv",
          mime="text/csv",
      )
    else:
      st.info("No data available for export.")

  # 6. REPORT ISSUE
  elif nav == "🛠️ Report App Issue / Problem":
    st.subheader("🛠️ Report App Issue to Developer")
    with st.form("issue_form", clear_on_submit=True):
      issue_msg = st.text_area("Describe the issue:")
      if st.form_submit_button("Submit Issue"):
        if issue_msg:
          with engine.begin() as conn:
            conn.execute(
                sqlalchemy.text("""
                            INSERT INTO support_tickets (manager_name, issue_message)
                            VALUES (:m, :msg)
                        """),
                {"m": user["full_name"], "msg": issue_msg},
            )
          st.success("Issue submitted successfully!")
          st.rerun()
        else:
          st.warning("Please describe the issue.")

  # 7. ADMIN GOVERNANCE
  elif nav == "🛡️ [Admin] Manager Governance & Quotas":
    if not is_admin:
      st.error("Unauthorized access.")
      return
    st.subheader("🛡️ Manager Governance & Audit Control")
    df_m_count = pd.read_sql(
        sqlalchemy.text(
            "SELECT COUNT(*) as total FROM users WHERE role != 'admin'"
        ),
        engine,
    )
    st.metric(
        label="Total Active Managers on App",
        value=df_m_count.iloc[0]["total"],
    )
    st.markdown("---")

    df_managers = pd.read_sql(
        sqlalchemy.text(
            "SELECT id, full_name, phone, client_quota, status, edit_override,"
            " note_override FROM users WHERE role != 'admin'"
        ),
        engine,
    )
    if not df_managers.empty:
      for idx, row in df_managers.iterrows():
        st.markdown(
            f"**{row['full_name']}** ({row['phone']}) | Status: `{row['status']}`"
            f" | Quota: `{row['client_quota']}`"
        )
        col1, col2, col3, col4 = st.columns(4)
        if row["status"] == "Active":
          if col1.button("Freeze", key=f"freeze_{row['id']}"):
            with engine.begin() as conn:
              conn.execute(
                  sqlalchemy.text(
                      "UPDATE users SET status = 'Frozen' WHERE id = :id"
                  ),
                  {"id": row["id"]},
              )
            st.rerun()
        else:
          if col1.button("Unfreeze", key=f"unfreeze_{row['id']}"):
            with engine.begin() as conn:
              conn.execute(
                  sqlalchemy.text(
                      "UPDATE users SET status = 'Active' WHERE id = :id"
                  ),
                  {"id": row["id"]},
              )
            st.rerun()

        if col2.button("Grant Edit Auth", key=f"edit_{row['id']}"):
          with engine.begin() as conn:
            conn.execute(
                sqlalchemy.text(
                    "UPDATE users SET edit_override = TRUE WHERE id = :id"
                ),
                {"id": row["id"]},
            )
          st.rerun()

        if col3.button("Grant Note Auth", key=f"note_{row['id']}"):
          with engine.begin() as conn:
            conn.execute(
                sqlalchemy.text(
                    "UPDATE users SET note_override = TRUE WHERE id = :id"
                ),
                {"id": row["id"]},
            )
          st.rerun()

        new_q = col4.number_input(
            "Quota",
            value=int(row["client_quota"]),
            step=5,
            key=f"q_{row['id']}",
        )
        if col4.button("Set Quota", key=f"set_q_{row['id']}"):
          with engine.begin() as conn:
            conn.execute(
                sqlalchemy.text(
                    "UPDATE users SET client_quota = :q WHERE id = :id"
                ),
                {"q": new_q, "id": row["id"]},
            )
          st.rerun()
        st.markdown("---")

    st.subheader("📋 All Registered Clients Across All Workspaces")
    df_all_clients = pd.read_sql(
        sqlalchemy.text(
            "SELECT id, client_name, client_phone, gender, location,"
            " manager_name, target_limit, date_registered FROM clients"
        ),
        engine,
    )
    st.dataframe(df_all_clients, use_container_width=True)

  # 8. SUPPORT TICKETS
  elif nav == "🛠️ App Issues & Support Tickets":
    if not is_admin:
      st.error("Unauthorized access.")
      return
    st.subheader("🛠️ Manager Issue & Problem Reports")
    df_tickets = pd.read_sql(
        sqlalchemy.text(
            "SELECT id, manager_name, issue_message, status, date FROM"
            " support_tickets ORDER BY date DESC"
        ),
        engine,
    )
    st.dataframe(df_tickets, use_container_width=True)


# ---------------------------------------------------------
# ROUTER
# ---------------------------------------------------------
if not st.session_state.logged_in:
  render_auth()
else:
  render_dashboard()
