from datetime import datetime, timedelta
import hashlib
import io
import os
import urllib.parse
import openpyxl
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import sqlalchemy
import streamlit as st

# ==========================================
# 1. PAGE CONFIGURATION & CUSTOM CSS STYLING
# ==========================================
st.set_page_config(
    page_title="SusuFlow Enterprise",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .main {
        background-color: #f4f6f9;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .dev-badge {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        color: white;
        padding: 12px 18px;
        border-radius: 8px;
        text-align: center;
        font-weight: 600;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-top: 15px;
        margin-bottom: 15px;
        letter-spacing: 0.5px;
        font-size: 0.9em;
        line-height: 1.5em;
    }
    .landing-banner {
        background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
        padding: 40px;
        border-radius: 15px;
        color: white;
        box-shadow: 0 10px 25px rgba(0,0,0,0.2);
        margin-bottom: 25px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ==========================================
# 2. CLOUD POSTGRESQL DATABASE & GOVERNANCE
# ==========================================
def get_db_connection():
  database_url = st.secrets["postgres"]["url"]
  return psycopg2.connect(database_url, sslmode="require")


def get_sqlalchemy_engine():
  database_url = st.secrets["postgres"]["url"]
  return sqlalchemy.create_engine(database_url)


def init_system_registry():
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password_hash TEXT,
            identifier TEXT,
            role TEXT DEFAULT 'collector',
            max_clients INTEGER DEFAULT 50,
            can_edit INTEGER DEFAULT 0
        )
    """)
  conn.commit()

  # Seed default master admin account if empty
  cursor.execute("SELECT COUNT(*) FROM users")
  count = cursor.fetchone()[0]
  if count == 0:
    cursor.execute(
        """
            INSERT INTO users (username, password_hash, identifier, role, max_clients, can_edit)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (username) DO NOTHING
        """,
        (
            "admin",
            hashlib.sha256("admin123".encode()).hexdigest(),
            "koffieroggers@gmail.com",
            "manager",
            500,
            1,
        ),
    )
    conn.commit()
  cursor.close()
  conn.close()


init_system_registry()


def register_user(username, password_hash, identifier):
  if not username:
    return False, "Username cannot be empty."
  clean_username = username.strip().lower()
  
  # Force all sign-ups to be standard collectors automatically
  role = "collector"
  max_clients = 50
  can_edit = 0

  conn = get_db_connection()
  cursor = conn.cursor()
  try:
    cursor.execute(
        """
            INSERT INTO users (username, password_hash, identifier, role, max_clients, can_edit)
            VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (
            clean_username,
            password_hash,
            identifier.strip().lower(),
            role,
            max_clients,
            can_edit,
        ),
    )
    conn.commit()
    cursor.close()
    conn.close()
    return True, "Registration successful!"
  except Exception as e:
    conn.rollback()
    cursor.close()
    conn.close()
    return False, "Username already exists. Choose a different username."


def get_user_credentials(username):
  if not username or not isinstance(username, str) or not username.strip():
    return None
  clean_username = username.strip().lower()
  conn = get_db_connection()
  cursor = conn.cursor(cursor_factory=RealDictCursor)
  cursor.execute(
      "SELECT username, password_hash, identifier, role, max_clients,"
      " can_edit FROM users WHERE username = %s",
      (clean_username,),
  )
  row = cursor.fetchone()
  cursor.close()
  conn.close()
  if row:
    return dict(row)
  return None


def get_all_users():
  engine = get_sqlalchemy_engine()
  df = pd.read_sql(
      "SELECT username, identifier, role, max_clients, can_edit FROM users",
      engine,
  )
  return df


def update_user_governance(username, max_clients, can_edit):
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute(
      "UPDATE users SET max_clients = %s, can_edit = %s WHERE username = %s",
      (max_clients, can_edit, username),
  )
  conn.commit()
  cursor.close()
  conn.close()


def reset_user_password(username, identifier, new_password_hash):
  clean_username = username.strip().lower()
  clean_identifier = identifier.strip().lower()
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute(
      "SELECT username FROM users WHERE username = %s AND identifier = %s",
      (clean_username, clean_identifier),
  )
  row = cursor.fetchone()
  if row:
    cursor.execute(
        "UPDATE users SET password_hash = %s WHERE username = %s",
        (new_password_hash, clean_username),
    )
    conn.commit()
    cursor.close()
    conn.close()
    return True, "Password successfully reset!"
  cursor.close()
  conn.close()
  return False, "Username and Phone/Email identifier did not match records."


def init_user_tables(username):
  clean_username = username.strip().lower()
  clients_table = f"clients_{clean_username}"
  tx_table = f"transactions_{clean_username}"
  audit_table = f"audit_log_{clean_username}"

  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {clients_table} (
            acc_id TEXT PRIMARY KEY,
            full_name TEXT,
            phone_number TEXT,
            location TEXT,
            occupation TEXT,
            registration_date TEXT
        )
    """)
  cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {tx_table} (
            transaction_id TEXT PRIMARY KEY,
            timestamp TEXT,
            acc_id TEXT,
            client_name TEXT,
            phone_number TEXT,
            transaction_type TEXT,
            location TEXT,
            amount REAL,
            notes TEXT
        )
    """)
  cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {audit_table} (
            log_id TEXT PRIMARY KEY,
            timestamp TEXT,
            record_id TEXT,
            action_type TEXT,
            authorized_by TEXT,
            reason TEXT
        )
    """)
  conn.commit()
  cursor.close()
  conn.close()


def get_client_records(username):
  init_user_tables(username)
  clean_username = username.strip().lower()
  engine = get_sqlalchemy_engine()
  df = pd.read_sql(f"SELECT * FROM clients_{clean_username}", engine)
  return df


def save_client_record(
    username, acc_id, full_name, phone_number, location, occupation
):
  init_user_tables(username)
  clean_username = username.strip().lower()
  creds = get_user_credentials(username)
  df_existing = get_client_records(username)
  max_limit = creds["max_clients"] if creds else 50

  if (
      len(df_existing) >= max_limit
      and acc_id not in df_existing["acc_id"].values
  ):
    return (
        False,
        f"❌ Quota exceeded! Your account limit is {max_limit} registered"
        " clients.",
    )

  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute(
      f"""
        INSERT INTO clients_{clean_username} (acc_id, full_name, phone_number, location, occupation, registration_date)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (acc_id) DO UPDATE SET
            full_name = EXCLUDED.full_name,
            phone_number = EXCLUDED.phone_number,
            location = EXCLUDED.location,
            occupation = EXCLUDED.occupation
    """,
      (
          acc_id,
          full_name,
          phone_number,
          location,
          occupation,
          datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
      ),
  )
  conn.commit()
  cursor.close()
  conn.close()
  return True, f"Client **{full_name}** ({acc_id}) successfully registered!"


def get_transaction_records(username):
  init_user_tables(username)
  clean_username = username.strip().lower()
  engine = get_sqlalchemy_engine()
  df = pd.read_sql(
      f"SELECT * FROM transactions_{clean_username} ORDER BY timestamp DESC",
      engine,
  )
  return df


def save_transaction_record(
    username,
    tx_id,
    timestamp,
    acc_id,
    client_name,
    phone_number,
    tx_type,
    location,
    amount,
    notes,
):
  init_user_tables(username)
  clean_username = username.strip().lower()
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute(
      f"""
        INSERT INTO transactions_{clean_username} (transaction_id, timestamp, acc_id, client_name, phone_number, transaction_type, location, amount, notes)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """,
      (
          tx_id,
          timestamp,
          acc_id,
          client_name,
          phone_number,
          tx_type,
          location,
          amount,
          notes,
      ),
  )
  conn.commit()
  cursor.close()
  conn.close()


def get_audit_logs(username):
  init_user_tables(username)
  clean_username = username.strip().lower()
  engine = get_sqlalchemy_engine()
  df = pd.read_sql(
      f"SELECT * FROM audit_log_{clean_username} ORDER BY timestamp DESC",
      engine,
  )
  return df


# ==========================================
# 3. SESSION STATE INITIALIZATION
# ==========================================
if "auth_user" not in st.session_state:
  st.session_state.auth_user = None
if "last_receipt" not in st.session_state:
  st.session_state.last_receipt = None


# ==========================================
# 4. AUTHENTICATION & UI FLOW
# ==========================================
if not st.session_state.auth_user:
  col_landing, col_auth = st.columns([1.2, 1])

  with col_landing:
    st.markdown(
        """
        <div class="landing-banner">
            <h1 style="color: #ffffff; margin-bottom: 10px;">🏛️ SusuFlow Enterprise (Cloud PostgreSQL)</h1>
            <p style="font-size: 1.1em; color: #d0d7de;">Cloud-backed micro-finance ledger with secure PostgreSQL storage, quotas, and anti-forgery stamps.</p>
            <hr style="border-color: rgba(255,255,255,0.2);">
            <ul style="list-style-type: none; padding-left: 0; line-height: 2.2em; font-size: 1.05em;">
                <li>☁️ <b>Permanent Cloud Storage:</b> Zero risk of data loss on reboots.</li>
                <li>🛡️ <b>Anti-Forgery Stamps:</b> Cryptographically hashed digital receipt stamps.</li>
                <li>📊 <b>Protected Excel Reports:</b> Secure worksheet exports.</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

  with col_auth:
    st.sidebar.markdown("### 🔐 Cloud Portal Authentication")
    auth_mode = st.sidebar.radio(
        "Select Action", ["Log In", "Sign Up", "Forgot Password / Recovery"]
    )

    if auth_mode == "Log In":
      st.sidebar.subheader("Operator Login")
      login_user = st.sidebar.text_input("Username").strip().lower()
      login_pass = st.sidebar.text_input("Password", type="password")

      if st.sidebar.button("Log In", use_container_width=True):
        if not login_user:
          st.sidebar.error("❌ Please enter a username.")
        else:
          user_data = get_user_credentials(login_user)
          if user_data:
            entered_hash = hashlib.sha256(login_pass.encode()).hexdigest()
            if entered_hash == user_data["password_hash"]:
              st.session_state.auth_user = user_data["username"]
              st.rerun()
            else:
              st.sidebar.error("❌ Incorrect password.")
          else:
            st.sidebar.error("❌ Username not found.")

    elif auth_mode == "Sign Up":
      st.sidebar.subheader("📝 Operator Sign Up")
      reg_user = st.sidebar.text_input("Choose Username").strip().lower()
      reg_pass = st.sidebar.text_input("Choose Password", type="password")
      reg_identifier = st.sidebar.text_input(
          "Phone Number or Gmail"
      ).strip()
      st.sidebar.info("ℹ️ New accounts are automatically registered as collectors.")

      if st.sidebar.button("Register & Login", use_container_width=True):
        if not reg_user or not reg_pass or not reg_identifier:
          st.sidebar.error(
              "❌ Please fill in Username, Password, and Phone/Email."
          )
        else:
          pass_hash = hashlib.sha256(reg_pass.encode()).hexdigest()
          success, msg = register_user(reg_user, pass_hash, reg_identifier)
          if success:
            st.session_state.auth_user = reg_user
            st.rerun()
          else:
            st.sidebar.error(f"❌ {msg}")

    else:
      st.sidebar.subheader("🔄 Account Recovery")
      rec_user = st.sidebar.text_input("Your Username").strip().lower()
      rec_identifier = st.sidebar.text_input(
          "Registered Phone Number or Gmail"
      ).strip()
      new_pass = st.sidebar.text_input("New Password", type="password")
      confirm_pass = st.sidebar.text_input("Confirm New Password", type="password")

      if st.sidebar.button("Reset Password", use_container_width=True):
        if not rec_user or not rec_identifier or not new_pass:
          st.sidebar.error("❌ All recovery fields are required.")
        elif new_pass != confirm_pass:
          st.sidebar.error("❌ Passwords do not match.")
        else:
          new_hash = hashlib.sha256(new_pass.encode()).hexdigest()
          success, msg = reset_user_password(
              rec_user, rec_identifier, new_hash
          )
          if success:
            st.sidebar.success(
                f"✅ {msg} You can now log in with your new password."
            )
          else:
            st.sidebar.error(f"❌ {msg}")

    st.sidebar.markdown(
        """
        <div class="dev-badge">
            👨‍💻 Developer: rog3rs<br>
            📞 0542470810<br>
            📧 koffieroggers@gmail.com
        </div>
        """,
        unsafe_allow_html=True,
    )
  st.stop()


# ==========================================
# 5. DASHBOARD & ROLE-BASED NAVIGATION
# ==========================================
current_user_id = st.session_state.auth_user
user_creds = get_user_credentials(current_user_id)
user_role = user_creds["role"] if user_creds else "collector"
is_master_admin = (current_user_id == "admin" or user_role == "manager")

st.sidebar.markdown(
    f"### 👤 Operator: {current_user_id} ({user_role.upper()})"
)
st.sidebar.info("☁️ **Storage:** Cloud PostgreSQL (Supabase)")

if st.sidebar.button("Log Out", use_container_width=True):
  st.session_state.auth_user = None
  st.rerun()

st.sidebar.markdown(
    """
    <div class="dev-badge">
        👨‍💻 Developer: rog3rs<br>
        📞 0542470810<br>
        📧 koffieroggers@gmail.com
    </div>
    """,
    unsafe_allow_html=True,
)

head_col1, head_col2 = st.columns([3, 1])
with head_col1:
  st.title("💼 SusuFlow Enterprise Cloud Command Centre")
  st.markdown(
      "*Cloud PostgreSQL Storage • Client Directory & Search • Secure Ledger*"
  )
with head_col2:
  st.markdown(
      "<div style='text-align: right; padding-top: 10px; font-size: 0.85em;"
      " color: #333; background: #fff; padding: 8px 12px; border-radius: 6px;"
      " border: 1px solid #ddd;'><b>Developer:</b> rog3rs<br><b>Phone:</b>"
      " 0542470810<br><b>Email:</b> koffieroggers@gmail.com</div>",
      unsafe_allow_html=True,
  )
st.markdown("---")

# Dynamic Tab Configuration: Only show Admin Governance tab if user is master admin ('admin')
if is_master_admin:
  tab1, tab2, tab3, tab4 = st.tabs([
      "👥 Client Registration & Search",
      "📥 Transactions & Records",
      "📊 Dashboard & Protected Export",
      "🛡️ Admin Governance & Audit",
  ])
else:
  tab1, tab2, tab3 = st.tabs([
      "👥 Client Registration & Search",
      "📥 Transactions & Records",
      "📊 Dashboard & Protected Export",
  ])

# --- TAB 1: CLIENT REGISTRATION & SEARCH ---
with tab1:
  st.markdown("### Register Client & Customer Search Directory")
  df_existing_clients = get_client_records(current_user_id)
  current_count = len(df_existing_clients)
  max_limit = user_creds["max_clients"] if user_creds else 50
  st.info(
      f"📊 **Client Quota Status:** {current_count} / {max_limit} clients"
      " registered."
  )

  with st.form("client_reg_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
      acc_id = st.text_input(
          "ACC ID", value=f"ACC-{datetime.now().strftime('%H%M%S')}"
      )
      full_name = st.text_input("Full Name")
      phone_number = st.text_input("Phone Number")
    with col2:
      location = st.text_input("Location")
      occupation = st.text_input("Occupation / Work")

    submit_client = st.form_submit_button(
        "Save Client Record", use_container_width=True
    )
    if submit_client:
      if not full_name or not phone_number or not acc_id:
        st.error(
            "❌ Please provide ACC ID, Full Name, and Phone Number."
        )
      else:
        success, msg = save_client_record(
            current_user_id,
            acc_id,
            full_name,
            phone_number,
            location,
            occupation,
        )
        if success:
          st.success(f"✅ {msg}")
          st.rerun()
        else:
          st.error(msg)

  st.markdown("---")
  st.markdown("#### 🔍 Search & Filter Clients Directory")
  df_clients = get_client_records(current_user_id)
  if df_clients.empty:
    st.info("ℹ️ No clients registered yet.")
  else:
    search_query = st.text_input("Search by Client Name, ACC ID, or Phone Number").strip().lower()
    if search_query:
      filtered_df = df_clients[
          df_clients['acc_id'].str.lower().str.contains(search_query) |
          df_clients['full_name'].str.lower().str.contains(search_query) |
          df_clients['phone_number'].str.lower().str.contains(search_query)
      ]
      st.dataframe(filtered_df, use_container_width=True)
    else:
      st.dataframe(df_clients, use_container_width=True)

        # --- TAB 2: TRANSACTION RECORDING & RECORDS ---
with tab2:
  st.markdown("### Record Transaction & Transaction Records")
  df_clients = get_client_records(current_user_id)

  if df_clients.empty:
    st.warning("⚠️ Please register a client in Tab 1 first.")
  else:
    with st.form("tx_form", clear_on_submit=True):
      col1, col2 = st.columns(2)
      with col1:
        client_options = df_clients["acc_id"].tolist()
        selected_acc_id = st.selectbox(
            "Client ACC ID",
            options=client_options,
            format_func=lambda x: f"{x} - {df_clients.loc[df_clients['acc_id'] == x, 'full_name'].values[0]}",
        )
        tx_type = st.selectbox(
            "Type of Transaction",
            [
                "Daily Contribution",
                "Weekly Deposit",
                "Savings Deposit",
                "Withdrawal",
            ],
        )
        amount = st.number_input("Amount (GHS)", min_value=0.0, format="%.2f")
      with col2:
        c_match = df_clients.loc[df_clients["acc_id"] == selected_acc_id].iloc[
            0
        ]
        tx_loc = st.text_input("Location", value=c_match["location"])
        notes = st.text_input("Remarks / Notes", value="Standard Deposit")

      submit_tx = st.form_submit_button(
          "Record Transaction", use_container_width=True
      )

      if submit_tx:
        if amount <= 0:
          st.error("❌ Amount must be greater than zero.")
        else:
          tx_id = f"TXN-{datetime.now().strftime('%Y%m%d%H%M%S')}"
          tx_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

          save_transaction_record(
              current_user_id,
              tx_id,
              tx_time,
              selected_acc_id,
              c_match["full_name"],
              c_match["phone_number"],
              tx_type,
              tx_loc,
              amount,
              notes,
          )

          stamp_seed = (
              f"{tx_id}-{selected_acc_id}-{amount}-{tx_time}-rog3rs"
          )
          stamp_hash = hashlib.sha256(stamp_seed.encode()).hexdigest()[
              :16
          ].upper()

          st.session_state.last_receipt = {
              "Transaction ID": tx_id,
              "Automated Date": tx_time,
              "ACC ID": selected_acc_id,
              "Client Name": c_match["full_name"],
              "Phone Number": c_match["phone_number"],
              "Location": tx_loc,
              "Transaction Type": tx_type,
              "Amount (GHS)": amount,
              "Notes": notes,
              "Stamp Hash": stamp_hash,
          }
          st.success("✅ Transaction recorded with anti-forgery stamp!")

  if st.session_state.last_receipt:
    r = st.session_state.last_receipt
    st.markdown("---")
    st.markdown("### 🖨️ Stamped & Verified Transaction Receipt")

    receipt_text = (
        f"🏛️ *SUSUFLOW ENTERPRISE CLOUD RECEIPT*\n"
        f"----------------------------------------\n"
        f"Tx ID: {r['Transaction ID']}\n"
        f"Timestamp: {r['Automated Date']}\n"
        f"ACC ID: {r['ACC ID']} | Name: {r['Client Name']}\n"
        f"Type: {r['Transaction Type']}\n"
        f"Amount: GHS {r['Amount (GHS)']:,.2f}\n"
        f"Remarks: {r['Notes']}\n"
        f"----------------------------------------\n"
        f"🛡️ ANTI-FORGERY STAMP HASH: #{r['Stamp Hash']}\n"
        f"Status: OFFICIAL CLOUD VERIFIED TRANSACTION\n"
        f"Developer: rog3rs (0542470810)"
    )

    st.markdown(
        f"""
        <div style="background-color: #ffffff; padding: 25px; border-radius: 12px; border: 2px solid #1e3c72; color: #000; box-shadow: 0 4px 15px rgba(0,0,0,0.05);">
            <h3 style="text-align: center; color: #1e3c72; margin-bottom: 0;">🏛️ SUSUFLOW ENTERPRISE</h3>
            <p style="text-align: center; font-size: 0.9em; color: #555;">Official Cloud Verified Transaction Receipt</p>
            <hr style="border: 0.5px solid #ddd;">
            <p><b>Transaction ID:</b> {r['Transaction ID']}</p>
            <p><b>Automated Date & Time:</b> {r['Automated Date']}</p>
            <p><b>ACC ID:</b> {r['ACC ID']} | <b>Client Name:</b> {r['Client Name']}</p>
            <p><b>Phone Number:</b> {r['Phone Number']} | <b>Location:</b> {r['Location']}</p>
            <p><b>Transaction Type:</b> {r['Transaction Type']}</p>
            <p><b>Amount:</b> <span style="font-size: 1.2em; color: #2e7d32;"><b>GHS {r['Amount (GHS)']:,.2f}</b></span></p>
            <p><b>Remarks:</b> {r['Notes']}</p>
            <div style="border: 3px dashed #b71c1c; color: #b71c1c; padding: 12px; text-align: center; font-weight: bold; font-size: 1em; border-radius: 8px; background-color: rgba(183, 28, 28, 0.03); margin-top: 15px; letter-spacing: 1px;">
                🛡️ CLOUD VERIFIED & AUTHENTICATED STAMP<br>SECURITY HASH: #{r['Stamp Hash']}
            </div>
            <hr style="border: 0.5px solid #ddd; margin-top: 15px;">
            <p style="text-align: center; font-size: 0.8em; color: #777;">Secured by SusuFlow Enterprise Cloud PostgreSQL Engine.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    wa_text = urllib.parse.quote(receipt_text)
    clean_ph = "".join(filter(str.isdigit, str(r["Phone Number"])))
    wa_url = (
        f"https://wa.me/{clean_ph}?text={wa_text}"
        if clean_ph
        else f"https://wa.me/?text={wa_text}"
    )
    st.markdown(
        f'<p style="text-align: center; margin-top: 15px;"><a href="{wa_url}"'
        ' target="_blank" style="display:inline-block; background-color:#25D366;'
        ' color:white; padding:10px 25px; border-radius:6px;'
        ' text-decoration:none; font-weight:bold;">💬 Share Stamped Receipt via'
        " WhatsApp</a></p>",
        unsafe_allow_html=True,
    )

  st.markdown("---")
  st.markdown("#### 🕒 Transaction Records & Search")
  df_tx = get_transaction_records(current_user_id)
  if df_tx.empty:
    st.info("ℹ️ No transactions recorded yet.")
  else:
    tx_search = st.text_input("Filter Transactions by Client Name, ACC ID, or ID").strip().lower()
    if tx_search:
      filtered_tx = df_tx[
          df_tx['acc_id'].str.lower().str.contains(tx_search) |
          df_tx['client_name'].str.lower().str.contains(tx_search) |
          df_tx['transaction_id'].str.lower().str.contains(tx_search)
      ]
      st.dataframe(filtered_tx, use_container_width=True)
    else:
      st.dataframe(df_tx, use_container_width=True)

# --- TAB 3: DASHBOARD & PROTECTED EXCEL EXPORT ---
  with tab3:
    st.markdown("### 📊 Client Deposit Summaries & Protected Excel Export")
    df_clients = get_client_records(current_user_id)
    df_tx = get_transaction_records(current_user_id)

    if not df_clients.empty and not df_tx.empty:
      client_sums = (
          df_tx.groupby(["acc_id", "client_name"])["amount"].sum().reset_index()
      )
      client_sums.rename(
          columns={"amount": "Total Deposits (GHS)"}, inplace=True
      )
      merged_dashboard = pd.merge(
          df_clients, client_sums, on="acc_id", how="left"
      ).fillna({"Total Deposits (GHS)": 0.0})
      
      # Client filter dropdown to sum up specific client total deposits quickly
      st.markdown("#### 🔎 Filter Particular Client Total Deposit")
      selected_client_filter = st.selectbox(
          "Select Client to View Total Summary",
          options=["All Clients"] + merged_dashboard["full_name"].tolist()
      )
      
      if selected_client_filter != "All Clients":
        filtered_row = merged_dashboard[merged_dashboard["full_name"] == selected_client_filter]
        st.success(f"📌 Total Deposit for **{selected_client_filter}**: **GHS {filtered_row['Total Deposits (GHS)'].values[0]:,.2f}**")
        st.dataframe(filtered_row, use_container_width=True)
      else:
        merged_dashboard["Total Deposits (GHS)"] = merged_dashboard[
            "Total Deposits (GHS)"
        ].apply(lambda x: f"GHS {x:,.2f}")
        st.dataframe(merged_dashboard, use_container_width=True)
    else:
      st.info("ℹ️ Insufficient data for dashboard aggregation.")

    st.markdown("---")
    st.markdown("#### 📥 Download Protected Excel Report")
    if st.button("Generate Encrypted Protected Excel File", use_container_width=True):
      try:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
          # Ensure valid dataframes to prevent openpyxl index errors
          export_clients = df_clients if not df_clients.empty else pd.DataFrame({"Status": ["No client records available"]})
          export_tx = df_tx if not df_tx.empty else pd.DataFrame({"Status": ["No transaction records available"]})
          
          export_clients.to_excel(writer, sheet_name="Clients", index=False)
          export_tx.to_excel(writer, sheet_name="Transactions", index=False)

        output.seek(0)
        wb = openpyxl.load_workbook(output)
        for sheet in wb.sheetnames:
          ws = wb[sheet]
          ws.protection.sheet = True
          ws.protection.password = "SusuFlowSecure2026"

        protected_output = io.BytesIO()
        wb.save(protected_output)
        protected_output.seek(0)

        st.download_button(
            label="📥 Download Secure Protected Excel File (.xlsx)",
            data=protected_output,
            file_name=f"SusuFlow_Cloud_Report_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
      except Exception as e:
        st.error(f"❌ Error generating Excel file: {e}")

# --- TAB 4: ADMIN GOVERNANCE & AUDIT LOGS (ADMIN ONLY) ---
if is_master_admin:
  with tab4:
    st.markdown("### 🛡️ Admin Governance & System Controls")
    st.success("👑 Master Administrator Access Verified.")
    df_users = get_all_users()
    st.dataframe(df_users, use_container_width=True)

    st.markdown("---")
    st.markdown("#### ⚙️ Regulate Operator Quotas & Edit Privileges")
    target_user = st.selectbox(
        "Select Operator Username", options=df_users["username"].tolist()
    )
    t_row = df_users[df_users["username"] == target_user].iloc[0]

    with st.form("gov_form"):
      new_max = st.number_input(
          "Maximum Client Registration Limit",
          min_value=1,
          max_value=10000,
          value=int(t_row["max_clients"]),
      )
      new_edit_perm = st.selectbox(
          "Grant Special Edit Privilege",
          options=[0, 1],
          format_func=lambda x: "Yes (Can Edit)"
          if x == 1
          else "No (Standard 24-hr Lock)",
          index=int(t_row["can_edit"]),
      )
      apply_gov = st.form_submit_button(
          "Update Operator Privileges", use_container_width=True
      )
      if apply_gov:
        update_user_governance(target_user, new_max, new_edit_perm)
        st.success(
            f"✅ Successfully updated governance rules for **{target_user}**!"
        )
        st.rerun()

    st.markdown("---")
    st.markdown("#### 🔍 Global Workspace Inspector")
    inspect_user = st.selectbox(
        "Select Collector Partition to Inspect",
        options=df_users["username"].tolist(),
        key="inspect_select",
    )
    col_insp1, col_insp2 = st.columns(2)
    with col_insp1:
      st.markdown(f"##### Clients Registered by `{inspect_user}`")
      st.dataframe(get_client_records(inspect_user), use_container_width=True)
    with col_insp2:
      st.markdown(f"##### Transactions by `{inspect_user}`")
      st.dataframe(
          get_transaction_records(inspect_user), use_container_width=True
      )

st.markdown("---")
st.caption(
    "SusuFlow Enterprise Cloud • Developer: rog3rs • 📞 0542470810 • 📧"
    " koffieroggers@gmail.com • PostgreSQL Cloud Platform"
)
