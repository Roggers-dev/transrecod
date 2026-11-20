from datetime import datetime
import urllib.parse
import uuid
from zoneinfo import ZoneInfo
from fpdf import FPDF
import pandas as pd
import sqlalchemy
import streamlit as st

GHANA_TZ = ZoneInfo("Africa/Accra")


def now_ghana():
  return datetime.now(GHANA_TZ)


def get_time_greeting(dt=None):
  current_dt = dt or now_ghana()
  hour = current_dt.hour
  if 5 <= hour < 12:
    return "Good morning"
  elif 12 <= hour < 17:
    return "Good afternoon"
  return "Good evening"


def play_threshold_alert_sound():
  # Plays a pleasant alert chime via Web Audio API without external audio files
  st.components.v1.html(
      """
      <script>
      (function() {
          try {
              const ctx = new (window.AudioContext || window.webkitAudioContext)();
              const notes = [523.25, 659.25, 783.99, 1046.50];
              notes.forEach((freq, idx) => {
                  const osc = ctx.createOscillator();
                  const gain = ctx.createGain();
                  osc.type = "sine";
                  osc.frequency.value = freq;
                  gain.gain.setValueAtTime(0.18, ctx.currentTime + idx * 0.14);
                  gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + idx * 0.14 + 0.25);
                  osc.connect(gain);
                  gain.connect(ctx.destination);
                  osc.start(ctx.currentTime + idx * 0.14);
                  osc.stop(ctx.currentTime + idx * 0.14 + 0.26);
              });
          } catch (e) {}
      })();
      </script>
      """,
      height=0,
  )


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
# STYLING, DEVELOPER FOOTER & UNIQUE HOVER CSS
# ---------------------------------------------------------
st.markdown(
    """
    <style>
    /* Keep sidebar & navigation tools clearly visible for all users */
    [data-testid="stSidebar"] {
        min-width: 270px;
        visibility: visible !important;
    }
    [data-testid="stSidebarNav"] {
        display: block !important;
    }

    /* Unique hover styles for Auth Tabs: Login, Register Workspace, Recover Password */
    div[data-baseweb="tab-list"] button[data-baseweb="tab"] {
        border-radius: 10px 10px 0 0;
        font-weight: 600;
        transition: all 0.25s ease;
        border: 1px solid rgba(128, 128, 128, 0.2);
    }
    /* Tab 1: Login */
    div[data-baseweb="tab-list"] button[data-baseweb="tab"]:nth-of-type(1):hover {
        background: linear-gradient(135deg, #1d4ed8, #3b82f6) !important;
        color: #ffffff !important;
        transform: translateY(-2px);
        box-shadow: 0 6px 14px rgba(37, 99, 235, 0.35);
    }
    /* Tab 2: Register Workspace */
    div[data-baseweb="tab-list"] button[data-baseweb="tab"]:nth-of-type(2):hover {
        background: linear-gradient(135deg, #059669, #34d399) !important;
        color: #ffffff !important;
        transform: translateY(-2px);
        box-shadow: 0 6px 14px rgba(5, 150, 105, 0.35);
    }
    /* Tab 3: Recover Password */
    div[data-baseweb="tab-list"] button[data-baseweb="tab"]:nth-of-type(3):hover {
        background: linear-gradient(135deg, #d97706, #fbbf24) !important;
        color: #111827 !important;
        transform: translateY(-2px);
        box-shadow: 0 6px 14px rgba(217, 119, 6, 0.35);
    }

    /* Unique hover CSS for each sidebar radio navigation tool */
    [data-testid="stSidebar"] div[role="radiogroup"] > label {
        border-radius: 10px;
        padding: 8px 12px !important;
        margin-bottom: 6px !important;
        border-left: 4px solid transparent;
        transition: all 0.22s ease;
        cursor: pointer;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] > label:nth-of-type(1):hover {
        background: linear-gradient(90deg, rgba(14, 165, 233, 0.22), rgba(14, 165, 233, 0.05)) !important;
        border-left-color: #0ea5e9 !important;
        transform: translateX(4px);
        box-shadow: 0 4px 10px rgba(14, 165, 233, 0.22);
    }
    [data-testid="stSidebar"] div[role="radiogroup"] > label:nth-of-type(2):hover {
        background: linear-gradient(90deg, rgba(16, 185, 129, 0.22), rgba(16, 185, 129, 0.05)) !important;
        border-left-color: #10b981 !important;
        transform: translateX(4px);
        box-shadow: 0 4px 10px rgba(16, 185, 129, 0.22);
    }
    [data-testid="stSidebar"] div[role="radiogroup"] > label:nth-of-type(3):hover {
        background: linear-gradient(90deg, rgba(139, 92, 246, 0.22), rgba(139, 92, 246, 0.05)) !important;
        border-left-color: #8b5cf6 !important;
        transform: translateX(4px);
        box-shadow: 0 4px 10px rgba(139, 92, 246, 0.22);
    }
    [data-testid="stSidebar"] div[role="radiogroup"] > label:nth-of-type(4):hover {
        background: linear-gradient(90deg, rgba(245, 158, 11, 0.22), rgba(245, 158, 11, 0.05)) !important;
        border-left-color: #f59e0b !important;
        transform: translateX(4px);
        box-shadow: 0 4px 10px rgba(245, 158, 11, 0.22);
    }
    [data-testid="stSidebar"] div[role="radiogroup"] > label:nth-of-type(5):hover {
        background: linear-gradient(90deg, rgba(236, 72, 153, 0.22), rgba(236, 72, 153, 0.05)) !important;
        border-left-color: #ec4899 !important;
        transform: translateX(4px);
        box-shadow: 0 4px 10px rgba(236, 72, 153, 0.22);
    }
    [data-testid="stSidebar"] div[role="radiogroup"] > label:nth-of-type(6):hover {
        background: linear-gradient(90deg, rgba(20, 184, 166, 0.22), rgba(20, 184, 166, 0.05)) !important;
        border-left-color: #14b8a6 !important;
        transform: translateX(4px);
        box-shadow: 0 4px 10px rgba(20, 184, 166, 0.22);
    }
    [data-testid="stSidebar"] div[role="radiogroup"] > label:nth-of-type(7):hover {
        background: linear-gradient(90deg, rgba(239, 68, 68, 0.22), rgba(239, 68, 68, 0.05)) !important;
        border-left-color: #ef4444 !important;
        transform: translateX(4px);
        box-shadow: 0 4px 10px rgba(239, 68, 68, 0.22);
    }
    [data-testid="stSidebar"] div[role="radiogroup"] > label:nth-of-type(8):hover {
        background: linear-gradient(90deg, rgba(99, 102, 241, 0.22), rgba(99, 102, 241, 0.05)) !important;
        border-left-color: #6366f1 !important;
        transform: translateX(4px);
        box-shadow: 0 4px 10px rgba(99, 102, 241, 0.22);
    }

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
    payer_name,
    manager_name,
    company_header,
    trans_type,
    amount,
    notes,
):
  pdf = FPDF(orientation="P", unit="mm", format=(105, 165))
  pdf.set_auto_page_break(auto=False)
  pdf.add_page()
  pdf.set_fill_color(255, 75, 75)
  pdf.rect(0, 0, 105, 24, "F")
  pdf.set_text_color(255, 255, 255)
  pdf.set_font("Helvetica", "B", 12)
  pdf.set_xy(5, 5)
  safe_header = (
      str(company_header).encode("latin-1", "replace").decode("latin-1")
  )
  pdf.cell(95, 6, safe_header[:35], ln=True, align="C")
  pdf.set_font("Helvetica", "", 8)
  pdf.cell(95, 5, "OFFICIAL TRANSACTION RECEIPT", ln=True, align="C")
  pdf.set_fill_color(44, 62, 80)
  pdf.rect(0, 142, 105, 23, "F")
  pdf.set_text_color(255, 255, 255)
  pdf.set_xy(5, 145)
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
  pdf.set_xy(8, 28)
  pdf.set_font("Helvetica", "B", 9)
  pdf.cell(40, 5, "Receipt No:", 0, 0)
  pdf.set_font("Helvetica", "", 9)
  pdf.cell(49, 5, str(receipt_no), 0, 1, "R")
  pdf.set_x(8)
  pdf.set_font("Helvetica", "B", 9)
  pdf.cell(40, 5, "Date & Time:", 0, 0)
  pdf.set_font("Helvetica", "", 9)
  pdf.cell(49, 5, str(date_str), 0, 1, "R")
  pdf.line(8, pdf.get_y() + 2, 97, pdf.get_y() + 2)
  pdf.ln(3)
  details = [
      ("Client Name:", str(client_name)),
      ("Client ID:", str(client_id)),
      ("Paid By / Payer:", str(payer_name)),
      ("Collector/Mgr:", str(manager_name)),
      ("Transaction:", str(trans_type).upper()),
  ]
  for label, val in details:
    pdf.set_x(8)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(35, 5, label, 0, 0)
    pdf.set_font("Helvetica", "", 9)
    safe_val = str(val).encode("latin-1", "replace").decode("latin-1")
    pdf.cell(54, 5, safe_val[:28], 0, 1, "R")
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
  pdf.cell(89, 4, "Remarks / Notes:", 0, 1)
  pdf.set_x(8)
  pdf.set_font("Helvetica", "", 8)
  safe_notes = (
      (notes if notes else "None").encode("latin-1", "replace").decode("latin-1")
  )
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


def mark_daily_greeting_if_needed(user_row):
  today_ghana = now_ghana().date()
  last_greet = user_row.get("last_greeting_date")
  if hasattr(last_greet, "date"):
    last_greet = last_greet.date()
  elif isinstance(last_greet, str) and last_greet:
    try:
      last_greet = datetime.fromisoformat(last_greet[:10]).date()
    except ValueError:
      last_greet = None

  if last_greet != today_ghana:
    greeting = get_time_greeting(now_ghana())
    name_part = user_row.get("full_name", "there")
    st.session_state.daily_greeting_banner = (
        f"{greeting}, **{name_part}**! Welcome to AlufaTanaah Record Keeper —"
        " wishing you a productive and smooth day ahead."
    )
    try:
      with engine.begin() as conn:
        conn.execute(
            sqlalchemy.text(
                "UPDATE users SET last_greeting_date = :d WHERE id = :id"
            ),
            {"d": today_ghana, "id": int(user_row["id"])},
        )
    except Exception:
      pass


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
                show_quota_to_manager BOOLEAN DEFAULT FALSE,
                edit_override BOOLEAN DEFAULT FALSE,
                note_override BOOLEAN DEFAULT FALSE,
                company_header TEXT DEFAULT 'AlufaTanaah Record Keeper',
                last_greeting_date DATE
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
                payer_name TEXT DEFAULT '',
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
    conn.execute(
        sqlalchemy.text("""
            CREATE TABLE IF NOT EXISTS workspace_announcements (
                id SERIAL PRIMARY KEY,
                message TEXT NOT NULL,
                updated_by TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    )
    conn.execute(
        sqlalchemy.text("""
            CREATE TABLE IF NOT EXISTS client_loans (
                client_id TEXT PRIMARY KEY,
                client_name TEXT,
                manager_name TEXT,
                initial_loan FLOAT DEFAULT 0.0,
                loan_amount FLOAT DEFAULT 0.0,
                loan_threshold FLOAT DEFAULT 0.0,
                is_active BOOLEAN DEFAULT FALSE,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    )
    schema_migrations = [
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS show_quota_to_manager BOOLEAN DEFAULT FALSE;",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_greeting_date DATE;",
        "ALTER TABLE transactions ADD COLUMN IF NOT EXISTS payer_name TEXT DEFAULT '';",
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
if "daily_greeting_banner" not in st.session_state:
  st.session_state.daily_greeting_banner = None
if "loan_feedback" not in st.session_state:
  st.session_state.loan_feedback = None


def render_auth():
  st.title("💰 AlufaTanaah Transaction Record Keeper")
  tab1, tab2, tab3 = st.tabs(
      ["Login", "Register Workspace", "Recover Password"]
  )
  with tab1:
    st.subheader("Login")
    login_phone = st.text_input("Phone Number or Email", key="login_id").strip()
    login_pass = st.text_input("Password", type="password", key="login_pw")
    if st.button("Log In"):
      df = safe_read_sql(
          "SELECT id, full_name, phone, email, password, role, status,"
          " suspension_reason, client_quota, show_quota_to_manager,"
          " edit_override, note_override, recovery_pref, company_header,"
          " last_greeting_date FROM users WHERE phone = :id OR email = :id",
          params={"id": login_phone},
      )
      if not df.empty:
        user = df.iloc[0]
        if user["password"] == login_pass:
          user_dict = user.to_dict()
          mark_daily_greeting_if_needed(user_dict)
          st.session_state.logged_in = True
          st.session_state.user = user_dict
          st.success("Login successful!")
          st.rerun()
        else:
          st.error("Incorrect password.")
      else:
        st.error("User not found.")
  with tab2:
    st.subheader("Register Workspace")
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
          today_ghana = now_ghana().date()
          greeting = get_time_greeting(now_ghana())
          try:
            with engine.begin() as conn:
              conn.execute(
                  sqlalchemy.text("""
                              INSERT INTO users (full_name, phone, email, password, role, recovery_pref, client_quota, show_quota_to_manager, company_header, last_greeting_date)
                              VALUES (:name, :phone, :email, :passwd, 'manager', :rec, 50, FALSE, :header, :greet_date)
                          """),
                  {
                      "name": reg_name,
                      "phone": reg_phone,
                      "email": reg_email,
                      "passwd": reg_pass,
                      "rec": recovery_choice,
                      "header": header_val,
                      "greet_date": today_ghana,
                  },
              )
            st.success(
                f"{greeting}, **{reg_name}**! Your workspace account has been"
                " created. You can now sign in using the Login tab."
            )
          except Exception:
            st.error(
                f"Error registering user: Phone number '{reg_phone}' may already"
                " be registered."
            )
        else:
          st.warning(
              "Please fill in Full Name, Phone Number, and Password fields."
          )
  with tab3:
    st.subheader("Recover Password")
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

  if st.session_state.daily_greeting_banner:
    st.success(st.session_state.daily_greeting_banner)

  df_ann = safe_read_sql(
      "SELECT message, updated_by, updated_at FROM workspace_announcements"
      " ORDER BY id DESC LIMIT 1"
  )
  if not df_ann.empty and str(df_ann.iloc[0]["message"]).strip():
    st.info(
        f"📢 **Announcement ({df_ann.iloc[0]['updated_by']}):**"
        f" {df_ann.iloc[0]['message']}"
    )

  # CHECK SUSPENSION STATUS FOR MANAGERS
  if not is_admin and user.get("status") == "Frozen":
    st.error("⚠️ ACCOUNT SUSPENDED BY ADMINISTRATION")
    st.warning(
        "**Reason / Message from Admin:**\n\n>"
        f" {user.get('suspension_reason', 'No specific reason provided.')}"
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
      st.session_state.daily_greeting_banner = None
      st.session_state.loan_feedback = None
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
    st.session_state.daily_greeting_banner = None
    st.session_state.loan_feedback = None
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
      if bool(user.get("show_quota_to_manager")):
        st.info(f"Quota Status: **{current_count} / {quota}** clients registered")
      if current_count >= quota:
        st.error("⚠️ Client registration limit reached. Please contact Admin.")
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
                f"Client **{c_name}** registered successfully! Unique ID:"
                f" `{unique_client_id}`"
            )
          except Exception as e:
            st.error(f"Error registering client: {e}")

              # 2. RECORD TRANSACTION & PDF RECEIPT + WHATSAPP NOTIFICATION
  elif nav == "📥 Record Transaction & Receipts":
    st.subheader("📥 Record Daily Transaction & Share PDF Receipt")
    if is_admin:
      df_clients = safe_read_sql(
          "SELECT id, client_name, client_phone FROM clients ORDER BY"
          " client_name ASC"
      )
    else:
      df_clients = safe_read_sql(
          "SELECT id, client_name, client_phone FROM clients WHERE manager_name"
          " = :m ORDER BY client_name ASC",
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

    selected_label = st.selectbox("Select Client", list(client_dict.keys()))
    trans_type = st.selectbox(
        "Transaction Type",
        ["Deposit", "Payment", "Arrears Pay", "Loan Payment"],
    )

    picked_cid = client_dict[selected_label]["id"]
    df_loan = safe_read_sql(
        "SELECT initial_loan, loan_amount, loan_threshold, is_active FROM"
        " client_loans WHERE client_id = :cid",
        params={"cid": str(picked_cid)},
    )
    existing_initial = (
        float(df_loan.iloc[0]["initial_loan"] or 0.0)
        if not df_loan.empty
        else 0.0
    )
    existing_loan_bal = (
        float(df_loan.iloc[0]["loan_amount"] or 0.0)
        if not df_loan.empty
        else 0.0
    )
    existing_threshold = (
        float(df_loan.iloc[0]["loan_threshold"] or 0.0)
        if not df_loan.empty
        else 0.0
    )

    with st.form("trans_form", clear_on_submit=True):
      if trans_type == "Loan Payment":
        st.markdown("#### 💳 Loan Balance & Threshold Setup")
        if existing_loan_bal > 0:
          st.info(
              f"Active Loan Balance: **GHS {existing_loan_bal:,.2f}** | Current"
              f" Threshold: **GHS {existing_threshold:,.2f}**"
          )
        loan_amount_input = st.number_input(
            "Loan Amount (GHS)",
            min_value=0.0,
            value=float(existing_loan_bal),
            step=10.0,
        )
        loan_threshold_input = st.number_input(
            "Loan Threshold Amount (GHS)",
            min_value=0.0,
            value=float(existing_threshold),
            step=5.0,
        )
      else:
        loan_amount_input = existing_loan_bal
        loan_threshold_input = existing_threshold

      amount = st.number_input("Payment / Transaction Amount (GHS)", min_value=0.0, step=1.0)
      payer_name = st.text_input(
          "Who is making this payment / deposit? (Leave blank if made by client"
          " directly)"
      ).strip()
      notes = st.text_area("Notes / Remarks (Locked after 24 hrs)")

      collector_role_label = (
          "Collector / Admin" if is_admin else "Collector / Manager"
      )
      money_confirmed = st.checkbox(
          f"✅ I ({collector_role_label}: {user['full_name']}) confirm that I"
          " have received and verified the money for this transaction."
      )

      submitted = st.form_submit_button(
          "Save Transaction & Generate PDF Receipt"
      )
      if submitted:
        if not money_confirmed:
          st.warning(
              "⚠️ Please confirm receipt of the money before saving the"
              " transaction."
          )
        elif amount <= 0:
          st.warning("Please enter an amount greater than 0.")
        elif (
            trans_type == "Loan Payment"
            and loan_threshold_input > loan_amount_input
        ):
          st.warning(
              "⚠️ Threshold amount cannot be greater than the loan amount."
          )
        else:
          c_data = client_dict[selected_label]
          c_id, c_name, c_phone = (
              c_data["id"],
              c_data["name"],
              c_data["phone"],
          )
          final_payer = payer_name if payer_name else c_name
          now_str = now_ghana().strftime("%Y-%m-%d %H:%M")
          current_header = user.get(
              "company_header", "AlufaTanaah Record Keeper"
          )

          threshold_met_now = False
          updated_loan_bal = existing_loan_bal
          cycle_start_loan = (
              existing_initial
              if existing_initial > 0
              else float(loan_amount_input)
          )

          if trans_type == "Loan Payment":
            starting_loan = float(loan_amount_input)
            thresh_val = float(loan_threshold_input)
            if starting_loan <= 0:
              st.warning(
                  "⚠️ Please enter a Loan Amount greater than 0 for a Loan"
                  " Payment."
              )
              st.stop()
            if existing_loan_bal <= 0 or abs(
                starting_loan - existing_loan_bal
            ) > 1e-6:
              cycle_start_loan = starting_loan
            remaining_after_payment = max(0.0, starting_loan - float(amount))

            if remaining_after_payment <= thresh_val:
              threshold_met_now = True
              updated_loan_bal = 0.0
              st.session_state.loan_feedback = {
                  "met": True,
                  "client_name": c_name,
                  "threshold": thresh_val,
                  "payment": float(amount),
                  "cycle_total": max(cycle_start_loan, float(amount)),
              }
            else:
              updated_loan_bal = remaining_after_payment
              st.session_state.loan_feedback = {
                  "met": False,
                  "client_name": c_name,
                  "threshold": thresh_val,
                  "remaining": updated_loan_bal,
                  "cycle_total": max(cycle_start_loan, updated_loan_bal),
              }

          try:
            with engine.begin() as conn:
              res = conn.execute(
                  sqlalchemy.text("""
                              INSERT INTO transactions (manager_name, client_name, client_id, payer_name, amount, trans_type, notes)
                              VALUES (:col, :client, :cid, :payer, :amt, :type, :notes)
                              RETURNING id
                          """),
                  {
                      "col": user["full_name"],
                      "client": c_name,
                      "cid": str(c_id),
                      "payer": final_payer,
                      "amt": float(amount),
                      "type": trans_type,
                      "notes": notes,
                  },
              )
              trans_id = res.scalar()

              if trans_type == "Loan Payment":
                conn.execute(
                    sqlalchemy.text("""
                                INSERT INTO client_loans (client_id, client_name, manager_name, initial_loan, loan_amount, loan_threshold, is_active, updated_at)
                                VALUES (:cid, :cname, :mname, :init_l, :l_amt, :l_thresh, :active, CURRENT_TIMESTAMP)
                                ON CONFLICT (client_id) DO UPDATE
                                SET client_name = EXCLUDED.client_name,
                                    manager_name = EXCLUDED.manager_name,
                                    initial_loan = EXCLUDED.initial_loan,
                                    loan_amount = EXCLUDED.loan_amount,
                                    loan_threshold = EXCLUDED.loan_threshold,
                                    is_active = EXCLUDED.is_active,
                                    updated_at = CURRENT_TIMESTAMP
                            """),
                    {
                        "cid": str(c_id),
                        "cname": c_name,
                        "mname": user["full_name"],
                        "init_l": float(cycle_start_loan),
                        "l_amt": float(updated_loan_bal),
                        "l_thresh": float(loan_threshold_input),
                        "active": not threshold_met_now,
                    },
                )

            receipt_no = f"REC-{str(trans_id).zfill(5)}"
            pdf_bytes = create_receipt_pdf(
                receipt_no=receipt_no,
                date_str=now_str,
                client_name=c_name,
                client_id=c_id,
                payer_name=final_payer,
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
                "payer_name": final_payer,
                "manager_name": user["full_name"],
                "company_header": current_header,
                "trans_type": trans_type,
                "amount": float(amount),
                "notes": notes,
                "pdf_bytes": pdf_bytes,
                "file_name": f"{receipt_no}_{c_name.replace(' ', '_')}.pdf",
            }
            st.success("Transaction recorded and PDF receipt ready!")
            st.rerun()
          except Exception as e:
            st.error(f"Error saving transaction: {e}")

    # Active Loan Progress Display & Threshold Alert
    df_loan_current = safe_read_sql(
        "SELECT initial_loan, loan_amount, loan_threshold, is_active FROM"
        " client_loans WHERE client_id = :cid",
        params={"cid": str(picked_cid)},
    )
    if st.session_state.loan_feedback:
      fb = st.session_state.loan_feedback
      if fb.get("met"):
        play_threshold_alert_sound()
        st.balloons()
        st.success(
            f"🔔 **Loan Threshold Met for {fb['client_name']}!** Threshold"
            f" (GHS {fb['threshold']:,.2f}) reached — Loan Amount has been"
            " reset to **GHS 0.00**."
        )
        st.progress(1.0)
        st.caption("Loan Repayment Progress: 100.0% — Loan Reset to GHS 0.00")
      else:
        total_ref = max(float(fb.get("cycle_total") or 1.0), 0.01)
        rem_val = float(fb.get("remaining") or 0.0)
        paid_ratio = min(1.0, max(0.0, (total_ref - rem_val) / total_ref))
        st.progress(paid_ratio)
        st.caption(
            f"Loan Remaining: **GHS {rem_val:,.2f}** | Threshold:"
            f" **GHS {float(fb.get('threshold') or 0.0):,.2f}** | Progress:"
            f" **{paid_ratio * 100:.1f}%**"
        )
    elif not df_loan_current.empty:
      lr = df_loan_current.iloc[0]
      init_l = float(lr["initial_loan"] or 0.0)
      rem_l = float(lr["loan_amount"] or 0.0)
      th_l = float(lr["loan_threshold"] or 0.0)
      if init_l > 0:
        pct_done = (
            1.0
            if rem_l == 0.0 and not bool(lr["is_active"])
            else min(1.0, max(0.0, (init_l - rem_l) / init_l))
        )
        st.progress(pct_done)
        st.caption(
            f"Client Loan Balance: **GHS {rem_l:,.2f}** / Initial:"
            f" **GHS {init_l:,.2f}** | Threshold: **GHS {th_l:,.2f}**"
            f" ({pct_done * 100:.1f}%)"
        )

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
                    <p><b>Paid By:</b> {rec['payer_name']}</p>
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
          action_phrase = (
              "payment received"
              if rec["trans_type"] in ["Payment", "Arrears Pay", "Loan Payment"]
              else "deposit made"
          )
          payer_text = (
              f" by {rec['payer_name']}"
              if rec["payer_name"] != rec["client_name"]
              else ""
          )
          wa_msg = (
              f"Hello {rec['client_name']}, {action_phrase} of"
              f" GHS {rec['amount']:,.2f} ({rec['trans_type']}){payer_text} has"
              f" been successfully recorded on your account ({rec['client_id']})"
              f" on {rec['date_str']}. Receipt No: {rec['receipt_no']}. Thank"
              f" you for working with us. - {rec['company_header']}"
          )
          encoded_msg = urllib.parse.quote(wa_msg)
          wa_url = f"https://wa.me/{clean_ph}?text={encoded_msg}"
          st.markdown(
              f'<a href="{wa_url}" target="_blank" style="display:block;'
              " text-align:center; background-color:#25D366; color:white;"
              " padding:10px 15px; border-radius:5px; text-decoration:none;"
              ' font-weight:bold; font-size:14px; margin-top:0px;">💬 Send'
              " WhatsApp Notification</a>",
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

  # 4. MY CLIENTS & RECORDS + SHARED CLIENT LEDGER LOOKUP
  elif nav == "📊 My Clients & Records":
    st.subheader("📊 Workspace Clients, Transaction Sums & Search Filtering")
    if is_admin:
      df_clients_all = safe_read_sql(
          "SELECT id, manager_name, client_name, client_phone, gender,"
          " location, target_limit, date_registered FROM clients"
      )
      df_trans = safe_read_sql(
          "SELECT id, manager_name, client_name, client_id, payer_name,"
          " amount, trans_type, notes, date FROM transactions ORDER BY date"
          " DESC"
      )
    else:
      df_clients_all = safe_read_sql(
          "SELECT id, manager_name, client_name, client_phone, gender,"
          " location, target_limit, date_registered FROM clients WHERE"
          " manager_name = :m",
          params={"m": user["full_name"]},
      )
      df_trans = safe_read_sql(
          "SELECT id, manager_name, client_name, client_id, payer_name,"
          " amount, trans_type, notes, date FROM transactions WHERE"
          " manager_name = :m ORDER BY date DESC",
          params={"m": user["full_name"]},
      )
    if not df_clients_all.empty:
      df_clients_summary = df_clients_all.copy()
      if not df_trans.empty and "client_name" in df_trans.columns:
        deposits = (
            df_trans[
                df_trans["trans_type"].isin(
                    ["Deposit", "Payment", "Arrears Pay", "Loan Payment"]
                )
            ]
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
        df_clients_summary = pd.merge(
            df_clients_summary, deposits, on="client_name", how="left"
        )
        df_clients_summary = pd.merge(
            df_clients_summary, withdrawals, on="client_name", how="left"
        )
      else:
        df_clients_summary["Total Deposits (GHS)"] = 0.0
        df_clients_summary["Total Withdrawals (GHS)"] = 0.0

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

      # Shared Feature: Instant Client Ledger & Balance Statement
      st.markdown("---")
      st.subheader("🧾 Client Balance & Statement Lookup")
      client_labels = [
          f"{r['client_name']} ({r['id']})"
          for _, r in df_clients_summary.iterrows()
      ]
      picked_client_label = st.selectbox(
          "Select a client to view balance & recent transactions", client_labels
      )
      picked_row = df_clients_summary[
          df_clients_summary["id"]
          == picked_client_label.split("(")[-1].rstrip(")")
      ].iloc[0]
      c1, c2, c3 = st.columns(3)
      c1.metric(
          "Total Inflows (GHS)",
          f"{float(picked_row['Total Deposits (GHS)']):,.2f}",
      )
      c2.metric(
          "Total Withdrawals (GHS)",
          f"{float(picked_row['Total Withdrawals (GHS)']):,.2f}",
      )
      c3.metric(
          "Net Balance (GHS)", f"{float(picked_row['Net Balance (GHS)']):,.2f}"
      )
      target_val = float(picked_row.get("target_limit") or 0.0)
      if target_val > 0:
        pct = min(
            100.0,
            max(0.0, (float(picked_row["Net Balance (GHS)"]) / target_val) * 100),
        )
        st.progress(pct / 100.0)
        st.caption(
            f"Target Progress: GHS {float(picked_row['Net Balance (GHS)']):,.2f}"
            f" / GHS {target_val:,.2f} ({pct:.1f}%)"
        )
      if not df_trans.empty:
        c_tx = df_trans[
            (df_trans["client_id"] == picked_row["id"])
            | (df_trans["client_name"] == picked_row["client_name"])
        ]
        if not c_tx.empty:
          st.dataframe(c_tx, use_container_width=True)
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

  # 8. ADMIN GOVERNANCE, MANAGER COUNT, QUOTAS, PERMISSIONS & BROADCAST
  elif nav == "🛡️ [Admin] Manager Governance & Quotas":
    if not is_admin:
      st.error("Unauthorized access.")
      return
    st.subheader("🛡️ Manager Governance, Quotas & Account Controls")

    df_managers = safe_read_sql(
        "SELECT id, full_name, phone, email, client_quota,"
        " show_quota_to_manager, status, suspension_reason, edit_override,"
        " note_override FROM users WHERE role != 'admin' ORDER BY id ASC"
    )
    df_clients_counts = safe_read_sql(
        "SELECT manager_name, COUNT(*) AS client_count FROM clients GROUP BY"
        " manager_name"
    )
    count_map = (
        dict(
            zip(
                df_clients_counts["manager_name"],
                df_clients_counts["client_count"],
            )
        )
        if not df_clients_counts.empty
        else {}
    )

    total_managers = len(df_managers)
    active_managers = (
        int((df_managers["status"] == "Active").sum())
        if not df_managers.empty
        else 0
    )
    frozen_managers = (
        int((df_managers["status"] == "Frozen").sum())
        if not df_managers.empty
        else 0
    )
    total_allocated_quota = (
        int(df_managers["client_quota"].fillna(0).sum())
        if not df_managers.empty
        else 0
    )

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Signed-Up Managers", total_managers)
    m2.metric("Active Managers", active_managers)
    m3.metric("Frozen Managers", frozen_managers)
    m4.metric("Total Client Quota", total_allocated_quota)

    st.markdown("---")
    st.subheader("📢 Workspace Broadcast Notice")
    current_notice = ""
    if not df_ann.empty:
      current_notice = str(df_ann.iloc[0]["message"] or "")
    with st.form("announcement_form"):
      notice_text = st.text_area(
          "Message shown to all signed-in users (leave blank to clear)",
          value=current_notice,
      )
      if st.form_submit_button("Save Announcement"):
        with engine.begin() as conn:
          conn.execute(
              sqlalchemy.text("""
                          INSERT INTO workspace_announcements (message, updated_by)
                          VALUES (:msg, :by)
                      """),
              {"msg": notice_text.strip(), "by": user["full_name"]},
          )
        st.success("Workspace announcement updated!")
        st.rerun()

    st.markdown("---")
    if not df_managers.empty:
      for _, row in df_managers.iterrows():
        mgr_clients = int(count_map.get(row["full_name"], 0))
        mgr_quota = int(row["client_quota"] or 0)
        vis_label = (
            "Visible to Mgr"
            if bool(row.get("show_quota_to_manager"))
            else "Hidden from Mgr"
        )
        st.markdown(
            f"**{row['full_name']}** ({row['phone']}) | Status:"
            f" `{row['status']}` | Clients: `{mgr_clients}` | Quota:"
            f" `{mgr_quota}` (`{vis_label}`)"
        )
        if row["status"] == "Frozen" and row["suspension_reason"]:
          st.markdown(
              f"> *Suspension Reason:* `{row['suspension_reason']}`"
          )

        with st.form(f"quota_perm_form_{row['id']}"):
          q_col, qv_col, p1_col, p2_col, btn_col = st.columns([2, 2, 2, 2, 2])
          new_quota = q_col.number_input(
              "Client Quota",
              min_value=0,
              max_value=100000,
              value=mgr_quota,
              step=5,
              key=f"quota_val_{row['id']}",
          )
          new_show_quota = qv_col.checkbox(
              "Show Quota to Mgr",
              value=bool(row.get("show_quota_to_manager")),
              key=f"show_quota_{row['id']}",
          )
          new_edit_ov = p1_col.checkbox(
              "Edit Override",
              value=bool(row.get("edit_override")),
              key=f"edit_ov_{row['id']}",
          )
          new_note_ov = p2_col.checkbox(
              "Note Override",
              value=bool(row.get("note_override")),
              key=f"note_ov_{row['id']}",
          )
          if btn_col.form_submit_button("Save Quota & Perms"):
            with engine.begin() as conn:
              conn.execute(
                  sqlalchemy.text("""
                              UPDATE users
                              SET client_quota = :q,
                                  show_quota_to_manager = :sq,
                                  edit_override = :eo,
                                  note_override = :no
                              WHERE id = :id
                          """),
                  {
                      "q": int(new_quota),
                      "sq": bool(new_show_quota),
                      "eo": bool(new_edit_ov),
                      "no": bool(new_note_ov),
                      "id": int(row["id"]),
                  },
              )
            st.success(f"Updated quota & permissions for {row['full_name']}.")
            st.rerun()

        col1, col2 = st.columns(2)
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
          resolved = c_r1.checkbox(
              "Mark as Resolved", value=t["status"] == "Resolved"
          )
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
