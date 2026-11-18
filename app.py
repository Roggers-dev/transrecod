from datetime import datetime
import urllib.parse
import uuid
from fpdf import FPDF
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
    .receipt-container {
        max-width: 380px;
        margin: 20px auto;
        background: #ffffff;
        border: 1px solid #d0d0d0;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        font-family: monospace;
        color: #111111;
        overflow: hidden;
    }
    .receipt-header-bg {
        background-color: #FF4B4B;
        color: white;
        padding: 15px;
        text-align: center;
    }
    .receipt-footer-bg {
        background-color: #2C3E50;
        color: white;
        padding: 12px;
        text-align: center;
        font-size: 10px;
    }
    .receipt-body {
        padding: 15px;
    }
    </style>

    <div class="developer-footer">
        <strong>🚀 AlufaTanaah Record Keeper</strong><br>
        ©️ Rogers Enterprises Limited | Ghana<br>
        📧 koffieroggers@gmail.com | Enchi
    </div>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# WHATSAPP PHONE NUMBER NORMALIZER (GHANA FORMAT)
# ---------------------------------------------------------
def normalize_ghana_phone(phone_str):
  if not phone_str:
    return ""
  digits = "".join(filter(str.isdigit, str(phone_str)))
  if digits.startswith("233") and len(digits) >= 12:
    return "+" + digits
  elif digits.startswith("0") and len(digits) == 10:
    return "+233" + digits[1:]
  elif len(digits) == 9:
    return "+233" + digits
  return "+" + digits if digits else ""


# ---------------------------------------------------------
# PDF RECEIPT GENERATOR
# ---------------------------------------------------------
def create_receipt_pdf(
    receipt_no,
    date_str,
    client_name,
    client_id,
    manager_name,
    company_header,
    trans_type,
    amount,
    notes,
):
  pdf = FPDF(orientation="P", unit="mm", format=(105, 160))
  pdf.set_auto_page_break(auto=False)
  pdf.add_page()

  pdf.set_fill_color(255, 75, 75)
  pdf.rect(0, 0, 105, 24, "F")
  pdf.set_text_color(255, 255, 255)
  pdf.set_font("Helvetica", "B", 12)
  pdf.set_xy(5, 5)
  safe_header = str(company_header).encode("latin-1", "replace").decode("latin-1")
  pdf.cell(95, 6, safe_header[:35], ln=True, align="C")
  pdf.set_font("Helvetica", "", 8)
  pdf.cell(95, 5, "OFFICIAL TRANSACTION RECEIPT", ln=True, align="C")

  pdf.set_fill_color(44, 62, 80)
  pdf.rect(0, 138, 105, 22, "F")
  pdf.set_text_color(255, 255, 255)
  pdf.set_xy(5, 141)
  pdf.set_font("Helvetica", "I", 8)
  pdf.cell(95, 4, "Thank you for working with us.", ln=True, align="C")
  pdf.set_font("Helvetica", "B", 7)
  pdf.cell(
      95,
      4,
      "Empowered by Rogers Enterprises Limited | Ghana".encode(
          "latin-1", "replace"
      ).decode("latin-1"),
      ln=True,
      align="C",
  )

  pdf.set_text_color(20, 20, 20)
  pdf.set_xy(8, 30)
  pdf.set_font("Helvetica", "B", 9)
  pdf.cell(40, 6, "Receipt No:", 0, 0)
  pdf.set_font("Helvetica", "", 9)
  pdf.cell(49, 6, str(receipt_no), 0, 1, "R")

  pdf.set_x(8)
  pdf.set_font("Helvetica", "B", 9)
  pdf.cell(40, 6, "Date & Time:", 0, 0)
  pdf.set_font("Helvetica", "", 9)
  pdf.cell(49, 6, str(date_str), 0, 1, "R")

  pdf.line(8, pdf.get_y() + 2, 97, pdf.get_y() + 2)
  pdf.ln(4)

  details = [
      ("Client Name:", str(client_name)),
      ("Client ID:", str(client_id)),
      ("Collector/Mgr:", str(manager_name)),
      ("Transaction:", str(trans_type).upper()),
  ]
  for label, val in details:
    pdf.set_x(8)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(35, 6, label, 0, 0)
    pdf.set_font("Helvetica", "", 9)
    safe_val = str(val).encode("latin-1", "replace").decode("latin-1")
    pdf.cell(54, 6, safe_val[:28], 0, 1, "R")

  pdf.ln(2)
  pdf.set_fill_color(245, 245, 245)
  pdf.set_x(8)
  pdf.set_font("Helvetica", "B", 11)
  pdf.cell(40, 9, "TOTAL AMOUNT:", 0, 0, "L", True)
  pdf.set_text_color(200, 40, 40)
  pdf.cell(49, 9, f"GHS {amount:,.2f}", 0, 1, "R", True)

  pdf.set_text_color(40, 40, 40)
  pdf.ln(2)
  pdf.set_x(8)
  pdf.set_font("Helvetica", "B", 8)
  pdf.cell(89, 5, "Remarks / Notes:", 0, 1)
  pdf.set_x(8)
  pdf.set_font("Helvetica", "", 8)
  safe_notes = (notes if notes else "None").encode("latin-1", "replace").decode("latin-1")
  pdf.multi_cell(89, 4, safe_notes)

  return bytes(pdf.output())


# ---------------------------------------------------------
# DATABASE CONNECTION & SCHEMA MIGRATIONS
# ---------------------------------------------------------
@st.cache_resource
def get_sqlalchemy_engine():
  try:
    database_url = st.secrets["postgres"]["url"]
    if "postgresql://" in database_url and "+psycopg2" not in database_url:
      database_url = database_url.replace(
          "postgresql://", "postgresql+psycopg2://", 1
      )
    return sqlalchemy.create_engine(database_url, pool_pre_ping=True)
  except Exception as e:
    st.error(f"Database Connection Error: {e}")
    st.stop()


engine = get_sqlalchemy_engine()


def safe_read_sql(query_str, params=None):
  try:
    return pd.read_sql(sqlalchemy.text(query_str), engine, params=params)
  except Exception:
    return pd.DataFrame()


@st.cache_resource
def init_db():
  with engine.connect() as conn:
    conn = conn.execution_options(isolation_level="AUTOCOMMIT")

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
                suspension_reason TEXT DEFAULT '',
                recovery_pref TEXT DEFAULT 'Email',
                client_quota INT DEFAULT 50,
                edit_override BOOLEAN DEFAULT FALSE,
                note_override BOOLEAN DEFAULT FALSE,
                company_header TEXT DEFAULT 'AlufaTanaah Record Keeper'
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
                client_id TEXT,
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
                admin_reply TEXT DEFAULT '',
                status TEXT DEFAULT 'Pending',
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    )

    schema_migrations = [
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS suspension_reason TEXT DEFAULT '';",
        "ALTER TABLE support_tickets ADD COLUMN IF NOT EXISTS admin_reply TEXT DEFAULT '';",
        "ALTER TABLE clients ALTER COLUMN id DROP DEFAULT;",
        "ALTER TABLE clients ALTER COLUMN id TYPE TEXT USING id::TEXT;",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS client_quota INT DEFAULT 50;",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS edit_override BOOLEAN DEFAULT FALSE;",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS note_override BOOLEAN DEFAULT FALSE;",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'Active';",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS role TEXT DEFAULT 'manager';",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS recovery_pref TEXT DEFAULT 'Email';",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS email TEXT;",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS company_header TEXT DEFAULT 'AlufaTanaah Record Keeper';",
        "ALTER TABLE clients ADD COLUMN IF NOT EXISTS manager_name TEXT;",
        "ALTER TABLE clients ADD COLUMN IF NOT EXISTS client_phone TEXT;",
        "ALTER TABLE clients ADD COLUMN IF NOT EXISTS gender TEXT;",
        "ALTER TABLE clients ADD COLUMN IF NOT EXISTS location TEXT;",
        "ALTER TABLE clients ADD COLUMN IF NOT EXISTS target_limit FLOAT DEFAULT 0.0;",
        "ALTER TABLE clients ADD COLUMN IF NOT EXISTS date_registered TIMESTAMP DEFAULT CURRENT_TIMESTAMP;",
        "ALTER TABLE clients ALTER COLUMN target_limit TYPE DOUBLE PRECISION USING COALESCE(target_limit::DOUBLE PRECISION, 0.0);",
        "ALTER TABLE transactions ADD COLUMN IF NOT EXISTS manager_name TEXT;",
        "ALTER TABLE transactions ADD COLUMN IF NOT EXISTS client_name TEXT;",
        "ALTER TABLE transactions ADD COLUMN IF NOT EXISTS client_id TEXT;",
        "ALTER TABLE transactions ADD COLUMN IF NOT EXISTS amount FLOAT;",
        "ALTER TABLE transactions ADD COLUMN IF NOT EXISTS trans_type TEXT;",
        "ALTER TABLE transactions ADD COLUMN IF NOT EXISTS notes TEXT;",
        "ALTER TABLE transactions ADD COLUMN IF NOT EXISTS date TIMESTAMP DEFAULT CURRENT_TIMESTAMP;",
        "ALTER TABLE transactions ALTER COLUMN amount TYPE DOUBLE PRECISION USING COALESCE(amount::DOUBLE PRECISION, 0.0);",
    ]

    for sql_cmd in schema_migrations:
      try:
        conn.execute(sqlalchemy.text(sql_cmd))
      except Exception:
        pass

    conn.execute(
        sqlalchemy.text("""
            INSERT INTO users (full_name, phone, email, password, role, status, client_quota, company_header)
            VALUES ('System Admin', 'admin', 'admin@alufatanaah.com', 'admin123', 'admin', 'Active', 9999, 'AlufaTanaah Record Keeper')
            ON CONFLICT (phone) DO UPDATE 
            SET password = 'admin123', role = 'admin', status = 'Active';
        """)
    )
  return True


init_db()


# ---------------------------------------------------------
# SESSION STATE
# ---------------------------------------------------------
if "logged_in" not in st.session_state:
  st.session_state.logged_in = False
  st.session_state.user = None
if "last_receipt" not in st.session_state:
  st.session_state.last_receipt = None


def render_auth():
  st.title("💰 AlufaTanaah Transaction Record Keeper")
  tab1, tab2, tab3 = st.tabs(
      ["Login", "Register Workspace", "Password Reset (No Data Loss)"]
  )

  with tab1:
    st.subheader("Sign In")
    login_phone = st.text_input("Phone Number or Email", key="login_id").strip()
    login_pass = st.text_input("Password", type="password", key="login_pw")

    if st.button("Log In"):
      df = safe_read_sql(
          "SELECT id, full_name, phone, email, password, role, status,"
          " suspension_reason, client_quota, edit_override, note_override,"
          " recovery_pref, company_header FROM users WHERE phone = :id OR email"
          " = :id",
          params={"id": login_phone},
      )

      if not df.empty:
        user = df.iloc[0]
        if user["password"] == login_pass:
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
    with st.form("workspace_reg_form", clear_on_submit=True):
      reg_name = st.text_input("Full Name").strip()
      reg_phone = st.text_input("Phone Number").strip()
      reg_email = st.text_input("Email Address (Optional)").strip()
      reg_pass = st.text_input("Create Password", type="password")
      reg_header = st.text_input(
          "Preferred Company Name on Receipts (Optional)",
          value="AlufaTanaah Record Keeper",
      ).strip()
      recovery_choice = st.radio(
          "Preferred Password Recovery Channel:", ["Email", "Phone"]
      )

      submitted_reg = st.form_submit_button("Register Account")
      if submitted_reg:
        if reg_name and reg_phone and reg_pass:
          header_val = (
              reg_header if reg_header else "AlufaTanaah Record Keeper"
          )
          try:
            with engine.begin() as conn:
              conn.execute(
                  sqlalchemy.text("""
                              INSERT INTO users (full_name, phone, email, password, role, recovery_pref, client_quota, company_header)
                              VALUES (:name, :phone, :email, :passwd, 'manager', :rec, 50, :header)
                          """),
                  {
                      "name": reg_name,
                      "phone": reg_phone,
                      "email": reg_email,
                      "passwd": reg_pass,
                      "rec": recovery_choice,
                      "header": header_val,
                  },
              )
            st.success(
                "Registration successful! You can now sign in using the Login"
                " tab."
            )
          except Exception as e:
            st.error(
                f"Error registering user: Phone number '{reg_phone}' may already"
                f" be registered."
            )
        else:
          st.warning(
              "Please fill in Full Name, Phone Number, and Password fields."
          )

  with tab3:
    st.subheader("Secure Password Reset")
    reset_id = st.text_input(
        "Phone Number or Email", key="reset_id_input"
    ).strip()
    new_pass = st.text_input(
        "New Password", type="password", key="reset_new_pass"
    )
    confirm_pass = st.text_input(
        "Confirm Password", type="password", key="reset_confirm_pass"
    )

    if st.button("Reset Password Securely"):
      if reset_id and new_pass and confirm_pass:
        if new_pass == confirm_pass:
          df_check = safe_read_sql(
              "SELECT id FROM users WHERE phone = :id OR email = :id",
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

  # CHECK SUSPENSION STATUS FOR MANAGERS
  if not is_admin and user.get("status") == "Frozen":
    st.error("⚠️ ACCOUNT SUSPENDED BY ADMINISTRATION")
    st.warning(
        f"**Reason / Message from Admin:**\n\n> {user.get('suspension_reason', 'No specific reason provided.')}"
    )
    st.info(
        "Your account is currently in read-only suspension. You cannot record"
        " new transactions or edit records until the admin reactivates your"
        " account. You may review your past records below or file a support"
        " ticket."
    )

    if st.button("Log Out"):
      st.session_state.logged_in = False
      st.session_state.user = None
      st.session_state.last_receipt = None
      st.rerun()

    st.markdown("---")
    st.subheader("📊 Read-Only Workspace Review")
    df_read = safe_read_sql(
        "SELECT * FROM transactions WHERE manager_name = :m ORDER BY date DESC",
        params={"m": user["full_name"]},
    )
    if not df_read.empty:
      st.dataframe(df_read, use_container_width=True)
    else:
      st.info("No transaction records found in your workspace.")
    return

  if is_admin:
    st.sidebar.title(f"🛡️ Admin: {user['full_name']}")
    nav_options = [
        "👥 Register Client",
        "📥 Record Transaction & Receipts",
        "⚙️ Workspace & Receipt Settings",
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
        "⚙️ Workspace & Receipt Settings",
        "📊 My Clients & Records",
        "🎯 Client Target Limits",
        "📥 Export Encrypted Data (Excel/CSV)",
        "🛠️ Report App Issue / Problem",
    ]

  nav = st.sidebar.radio("Navigation", nav_options)

  if st.sidebar.button("Log Out"):
    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.last_receipt = None
    st.rerun()

      # 1. REGISTER CLIENT
  if nav == "👥 Register Client":
    st.subheader("👥 Register New Client")
    if not is_admin:
      df_count = safe_read_sql(
          "SELECT COUNT(*) as cnt FROM clients WHERE manager_name = :m",
          params={"m": user["full_name"]},
      )
      current_count = int(df_count.iloc[0]["cnt"]) if not df_count.empty else 0
      quota = int(user["client_quota"])
      st.info(f"Quota Status: **{current_count} / {quota}** clients registered")
      if current_count >= quota:
        st.error("⚠️ Quota limit reached. Contact Admin.")
        return

    with st.form("client_reg_form", clear_on_submit=True):
      c_name = st.text_input("Client Full Name").strip()
      c_phone = st.text_input("Client Phone Number (e.g. 0241234567)").strip()
      c_gender = st.selectbox("Gender", ["Male", "Female", "Other"])
      c_location = st.text_input("Location / Address").strip()

      submitted = st.form_submit_button("Register Client")
      if submitted:
        if not c_name:
          st.warning("Please enter the client's full name.")
        else:
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
                f"Client **{c_name}** registered successfully! Unique ID: `{unique_client_id}`"
            )
          except Exception as e:
            st.error(f"Error registering client: {e}")

  # 2. RECORD TRANSACTION & PDF RECEIPT + WHATSAPP NOTIFICATION
  elif nav == "📥 Record Transaction & Receipts":
    st.subheader("📥 Record Daily Transaction & Share PDF Receipt")
    if is_admin:
      df_clients = safe_read_sql(
          "SELECT id, client_name, client_phone FROM clients ORDER BY client_name ASC"
      )
    else:
      df_clients = safe_read_sql(
          "SELECT id, client_name, client_phone FROM clients WHERE manager_name = :m ORDER BY client_name ASC",
          params={"m": user["full_name"]},
      )

    if df_clients.empty:
      st.warning("⚠️ Please register at least one client first.")
      return

    client_dict = {
        f"{row['client_name']} ({row['id']})": {
            "id": row["id"],
            "name": row["client_name"],
            "phone": row["client_phone"],
        }
        for _, row in df_clients.iterrows()
    }

    with st.form("trans_form", clear_on_submit=True):
      selected_label = st.selectbox("Select Client", list(client_dict.keys()))
      amount = st.number_input("Amount (GHS)", min_value=0.0, step=1.0)
      trans_type = st.selectbox("Transaction Type", ["Deposit", "Withdrawal"])
      notes = st.text_area("Notes / Remarks (Locked after 24 hrs)")

      submitted = st.form_submit_button("Save Transaction & Generate PDF Receipt")
      if submitted:
        if amount <= 0:
          st.warning("Please enter an amount greater than 0.")
        else:
          c_data = client_dict[selected_label]
          c_id, c_name, c_phone = (
              c_data["id"],
              c_data["name"],
              c_data["phone"],
          )
          now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
          current_header = user.get(
              "company_header", "AlufaTanaah Record Keeper"
          )
          try:
            with engine.begin() as conn:
              res = conn.execute(
                  sqlalchemy.text("""
                              INSERT INTO transactions (manager_name, client_name, client_id, amount, trans_type, notes)
                              VALUES (:col, :client, :cid, :amt, :type, :notes)
                              RETURNING id
                          """),
                  {
                      "col": user["full_name"],
                      "client": c_name,
                      "cid": str(c_id),
                      "amt": float(amount),
                      "type": trans_type,
                      "notes": notes,
                  },
              )
              trans_id = res.scalar()

            receipt_no = f"REC-{str(trans_id).zfill(5)}"
            pdf_bytes = create_receipt_pdf(
                receipt_no=receipt_no,
                date_str=now_str,
                client_name=c_name,
                client_id=c_id,
                manager_name=user["full_name"],
                company_header=current_header,
                trans_type=trans_type,
                amount=float(amount),
                notes=notes,
            )

            st.session_state.last_receipt = {
                "receipt_no": receipt_no,
                "date_str": now_str,
                "client_name": c_name,
                "client_id": c_id,
                "client_phone": c_phone,
                "manager_name": user["full_name"],
                "company_header": current_header,
                "trans_type": trans_type,
                "amount": float(amount),
                "notes": notes,
                "pdf_bytes": pdf_bytes,
                "file_name": f"{receipt_no}_{c_name.replace(' ', '_')}.pdf",
            }
            st.success("Transaction recorded and PDF receipt ready!")
          except Exception as e:
            st.error(f"Error saving transaction: {e}")

    if st.session_state.last_receipt:
      rec = st.session_state.last_receipt
      receipt_html = f"""
            <div class="receipt-container">
                <div class="receipt-header-bg">
                    <p style="margin:0; font-weight:bold; font-size:15px;">{rec['company_header']}</p>
                    <p style="margin:2px 0 0 0; font-size:10px; opacity:0.9;">OFFICIAL TRANSACTION RECEIPT</p>
                </div>
                <div class="receipt-body">
                    <p><b>Receipt No:</b> {rec['receipt_no']}</p>
                    <p><b>Date & Time:</b> {rec['date_str']}</p>
                    <hr style="border: 0.5px dashed #ccc;">
                    <p><b>Client Name:</b> {rec['client_name']}</p>
                    <p><b>Client ID:</b> {rec['client_id']}</p>
                    <p><b>Collector/Mgr:</b> {rec['manager_name']}</p>
                    <p><b>Transaction:</b> {rec['trans_type'].upper()}</p>
                    <p style="background:#f9f9f9; padding:8px; border-radius:4px; margin-top:8px;"><b>TOTAL AMOUNT:</b> GHS {rec['amount']:,.2f}</p>
                    <p><b>Remarks:</b> {rec['notes'] if rec['notes'] else 'None'}</p>
                </div>
                <div class="receipt-footer-bg">
                    <p style="margin:0; font-style:italic; font-size:10px;">Thank you for working with us.</p>
                    <p style="margin:2px 0 0 0; font-size:9px; font-weight:bold;">Empowered by Rogers Enterprises Limited | Ghana</p>
                </div>
            </div>
            """
      st.markdown(receipt_html, unsafe_allow_html=True)

      col_dl1, col_dl2 = st.columns(2)
      with col_dl1:
        st.download_button(
            label="📥 Download PDF Receipt",
            data=rec["pdf_bytes"],
            file_name=rec["file_name"],
            mime="application/pdf",
            use_container_width=True,
        )

      with col_dl2:
        if rec["client_phone"]:
          clean_ph = normalize_ghana_phone(rec["client_phone"])
          wa_msg = (
              f"Hello {rec['client_name']}, your {rec['trans_type'].lower()} of"
              f" GHS {rec['amount']:,.2f} has been successfully recorded on your"
              f" account ({rec['client_id']}) on {rec['date_str']}. Receipt No:"
              f" {rec['receipt_no']}. Thank you for working with us. - "
              f"{rec['company_header']}"
          )
          encoded_msg = urllib.parse.quote(wa_msg)
          wa_url = f"https://wa.me/{clean_ph}?text={encoded_msg}"
          st.markdown(
              f'<a href="{wa_url}" target="_blank" style="display:block; text-align:center; background-color:#25D366; color:white; padding:10px 15px; border-radius:5px; text-decoration:none; font-weight:bold; font-size:14px; margin-top:0px;">💬 Send WhatsApp Notification</a>',
              unsafe_allow_html=True,
          )
        else:
          st.info(
              "⚠️ Client has no phone number recorded for WhatsApp alerts."
          )


            # 3. WORKSPACE & RECEIPT SETTINGS
  elif nav == "⚙️ Workspace & Receipt Settings":
    st.subheader("⚙️ Customize Your Receipt Header / Company Name")
    current_h = user.get("company_header", "AlufaTanaah Record Keeper")
    with st.form("header_form"):
      new_header_input = st.text_input(
          "Company / Business Name on Receipts", value=current_h
      ).strip()
      if st.form_submit_button("Save Receipt Header"):
        if new_header_input:
          with engine.begin() as conn:
            conn.execute(
                sqlalchemy.text(
                    "UPDATE users SET company_header = :h WHERE phone = :p"
                ),
                {"h": new_header_input, "p": user["phone"]},
            )
          st.session_state.user["company_header"] = new_header_input
          st.success("Receipt header updated successfully!")
          st.rerun()
        else:
          st.warning("Receipt header cannot be empty.")

  # 4. MY CLIENTS & RECORDS
  elif nav == "📊 My Clients & Records":
    st.subheader("📊 Workspace Clients, Transaction Sums & Search Filtering")

    if is_admin:
      df_clients_all = safe_read_sql(
          "SELECT id, manager_name, client_name, client_phone, gender,"
          " location, target_limit, date_registered FROM clients"
      )
      df_trans = safe_read_sql(
          "SELECT id, manager_name, client_name, amount, trans_type, notes,"
          " date FROM transactions ORDER BY date DESC"
      )
    else:
      df_clients_all = safe_read_sql(
          "SELECT id, manager_name, client_name, client_phone, gender,"
          " location, target_limit, date_registered FROM clients WHERE"
          " manager_name = :m",
          params={"m": user["full_name"]},
      )
      df_trans = safe_read_sql(
          "SELECT id, manager_name, client_name, amount, trans_type, notes,"
          " date FROM transactions WHERE manager_name = :m ORDER BY date"
          " DESC",
          params={"m": user["full_name"]},
      )

    if not df_clients_all.empty:
      df_clients_summary = df_clients_all.copy()
      df_clients_summary["Total Deposits (GHS)"] = 0.0
      df_clients_summary["Total Withdrawals (GHS)"] = 0.0
      df_clients_summary["Net Balance (GHS)"] = 0.0

      if not df_trans.empty and "client_name" in df_trans.columns:
        deposits = (
            df_trans[df_trans["trans_type"] == "Deposit"]
            .groupby("client_name")["amount"]
            .sum()
            .reset_index(name="Total Deposits (GHS)")
        )
        withdrawals = (
            df_trans[df_trans["trans_type"] == "Withdrawal"]
            .groupby("client_name")["amount"]
            .sum()
            .reset_index(name="Total Withdrawals (GHS)")
        )
        df_clients_summary = df_clients_summary.drop(
            columns=[
                "Total Deposits (GHS)",
                "Total Withdrawals (GHS)",
                "Net Balance (GHS)",
            ],
            errors="ignore",
        )
        df_clients_summary = pd.merge(
            df_clients_all, deposits, on="client_name", how="left"
        )
        df_clients_summary = pd.merge(
            df_clients_summary, withdrawals, on="client_name", how="left"
        )
        df_clients_summary["Total Deposits (GHS)"] = df_clients_summary[
            "Total Deposits (GHS)"
        ].fillna(0.0)
        df_clients_summary["Total Withdrawals (GHS)"] = df_clients_summary[
            "Total Withdrawals (GHS)"
        ].fillna(0.0)
        df_clients_summary["Net Balance (GHS)"] = (
            df_clients_summary["Total Deposits (GHS)"]
            - df_clients_summary["Total Withdrawals (GHS)"]
        )

      search_query = st.text_input(
          "🔎 Search by client name, phone, location, or Unique ID:"
      )
      if search_query:
        mask = (
            df_clients_summary["client_name"]
            .astype(str)
            .str.contains(search_query, case=False, na=False)
            | df_clients_summary["client_phone"]
            .astype(str)
            .str.contains(search_query, case=False, na=False)
            | df_clients_summary["location"]
            .astype(str)
            .str.contains(search_query, case=False, na=False)
            | df_clients_summary["id"]
            .astype(str)
            .str.contains(search_query, case=False, na=False)
        )
        df_clients_filtered = df_clients_summary[mask]
      else:
        df_clients_filtered = df_clients_summary

      st.dataframe(df_clients_filtered, use_container_width=True)
    else:
      st.info("No registered clients found in this workspace.")

    st.markdown("---")
    st.subheader("📊 Transaction History & Edit Controls")
    if not df_trans.empty:
      st.dataframe(df_trans, use_container_width=True)
    else:
      st.info("No transaction records found.")

  # 5. TARGET LIMITS
  elif nav == "🎯 Client Target Limits":
    st.subheader("🎯 Client Target Limits")
    if is_admin:
      df_clients = safe_read_sql(
          "SELECT id, manager_name, client_name, target_limit FROM clients"
      )
    else:
      df_clients = safe_read_sql(
          "SELECT id, manager_name, client_name, target_limit FROM clients"
          " WHERE manager_name = :m",
          params={"m": user["full_name"]},
      )

    if not df_clients.empty:
      st.dataframe(df_clients, use_container_width=True)
      c_id_input = st.text_input(
          "Enter Client Unique ID to Update Target Limit"
      ).strip()
      if c_id_input:
        target_row = df_clients[df_clients["id"].astype(str) == c_id_input]
        if not target_row.empty:
          tr = target_row.iloc[0]
          with st.form("target_form"):
            new_target = st.number_input(
                f"New Target for {tr['client_name']} (GHS)",
                value=float(tr["target_limit"] or 0.0),
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

  # 6. EXPORT
  elif nav == "📥 Export Encrypted Data (Excel/CSV)":
    st.subheader("📥 Export Transaction Records")
    if is_admin:
      df_export = safe_read_sql("SELECT * FROM transactions")
    else:
      df_export = safe_read_sql(
          "SELECT * FROM transactions WHERE manager_name = :m",
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

  # 7. REPORT ISSUE (MANAGER)
  elif nav == "🛠️ Report App Issue / Problem":
    st.subheader("🛠️ Report App Issue to Developer / Admin")
    with st.form("issue_form", clear_on_submit=True):
      issue_msg = st.text_area("Describe the issue or request support:")
      if st.form_submit_button("Submit Issue"):
        if issue_msg:
          with engine.begin() as conn:
            conn.execute(
                sqlalchemy.text("""
                            INSERT INTO support_tickets (manager_name, issue_message, status)
                            VALUES (:m, :msg, 'Pending')
                        """),
                {"m": user["full_name"], "msg": issue_msg},
            )
          st.success("Issue submitted successfully! Admin will review soon.")
        else:
          st.warning("Please describe the issue.")

    st.markdown("---")
    st.subheader("📬 Your Submitted Tickets & Admin Replies")
    df_my_tickets = safe_read_sql(
        "SELECT id, issue_message, admin_reply, status, date FROM"
        " support_tickets WHERE manager_name = :m ORDER BY date DESC",
        params={"m": user["full_name"]},
    )
    if not df_my_tickets.empty:
      for _, t in df_my_tickets.iterrows():
        st.markdown(
            f"**Ticket #{t['id']}** ({t['date']}) - Status: `{t['status']}`"
        )
        st.markdown(f"*Your Issue:* {t['issue_message']}")
        if t["admin_reply"]:
          st.success(f"**Admin Reply:** {t['admin_reply']}")
        else:
          st.info("Waiting for admin reply...")
        st.markdown("---")
    else:
      st.info("No support tickets submitted yet.")

  # 8. ADMIN GOVERNANCE & ACCOUNT SUSPENSION / REMOVAL
  elif nav == "🛡️ [Admin] Manager Governance & Quotas":
    if not is_admin:
      st.error("Unauthorized access.")
      return
    st.subheader("🛡️ Manager Governance, Suspensions & Account Removal")

    df_managers = safe_read_sql(
        "SELECT id, full_name, phone, client_quota, status,"
        " suspension_reason FROM users WHERE role != 'admin'"
    )
    if not df_managers.empty:
      for _, row in df_managers.iterrows():
        st.markdown(
            f"**{row['full_name']}** ({row['phone']}) | Status:"
            f" `{row['status']}` | Quota: `{row['client_quota']}`"
        )
        if row["status"] == "Frozen" and row["suspension_reason"]:
          st.markdown(
              f"> *Suspension Reason:* `{row['suspension_reason']}`"
          )

        col1, col2, col3 = st.columns(3)

        if row["status"] == "Active":
          with col1.form(f"freeze_form_{row['id']}"):
            reason = st.text_input(
                "Suspension Reason / Message",
                placeholder="Violation of policy...",
            )
            if st.form_submit_button("Suspend / Freeze Account"):
              with engine.begin() as conn:
                conn.execute(
                    sqlalchemy.text(
                        "UPDATE users SET status = 'Frozen',"
                        " suspension_reason = :r WHERE id = :id"
                    ),
                    {"r": reason, "id": row["id"]},
                )
              st.success("Account suspended with message.")
              st.rerun()
        else:
          if col1.button("Unfreeze Account", key=f"unfreeze_{row['id']}"):
            with engine.begin() as conn:
              conn.execute(
                  sqlalchemy.text(
                      "UPDATE users SET status = 'Active', suspension_reason ="
                      " '' WHERE id = :id"
                  ),
                  {"id": row["id"]},
              )
            st.success("Account reactivated.")
            st.rerun()

        if col2.button(
            "🗑️ Remove Account & Data", key=f"del_mgr_{row['id']}"
        ):
          with engine.begin() as conn:
            conn.execute(
                sqlalchemy.text("DELETE FROM users WHERE id = :id"),
                {"id": row["id"]},
            )
          st.warning("Manager account removed.")
          st.rerun()

        st.markdown("---")
    else:
      st.info("No workspace managers registered.")

  # 9. ADMIN SUPPORT TICKETS & MESSAGING
  elif nav == "🛠️ App Issues & Support Tickets":
    if not is_admin:
      st.error("Unauthorized access.")
      return
    st.subheader("🛠️ Manager Support Tickets & Messaging Reply Center")

    df_tickets = safe_read_sql(
        "SELECT id, manager_name, issue_message, admin_reply, status, date"
        " FROM support_tickets ORDER BY date DESC"
    )
    if not df_tickets.empty:
      for _, t in df_tickets.iterrows():
        st.markdown(
            f"**Ticket #{t['id']}** | Manager: **{t['manager_name']}** |"
            f" Status: `{t['status']}`"
        )
        st.markdown(f"**Issue:** {t['issue_message']}")

        with st.form(f"reply_form_{t['id']}"):
          reply_text = st.text_area(
              "Reply to Manager",
              value=str(t["admin_reply"] if t["admin_reply"] else ""),
          )
          c_r1, c_r2 = st.columns(2)
          resolved = c_r1.checkbox("Mark as Resolved", value=t["status"] == "Resolved")
          if c_r2.form_submit_button("Send Admin Reply"):
            new_status = "Resolved" if resolved else "Pending"
            with engine.begin() as conn:
              conn.execute(
                  sqlalchemy.text(
                      "UPDATE support_tickets SET admin_reply = :r, status ="
                      " :s WHERE id = :id"
                  ),
                  {"r": reply_text, "s": new_status, "id": t["id"]},
              )
            st.success("Reply sent to manager!")
            st.rerun()
        st.markdown("---")
    else:
      st.info("No support tickets or messages from managers.")


# ---------------------------------------------------------
# ROUTER
# ---------------------------------------------------------
if not st.session_state.logged_in:
  render_auth()
else:
  render_dashboard()
