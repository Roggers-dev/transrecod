from datetime import datetime
import urllib.parse
import uuid
import os
import sqlite3
import hashlib
import secrets
import hmac
import time
from pathlib import Path
from zoneinfo import ZoneInfo

from fpdf import FPDF
import pandas as pd
import sqlalchemy
from sqlalchemy import inspect
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
# LOCAL-FIRST DATABASE + OPTIONAL AUTOMATIC CLOUD SNAPSHOT SYNC
# ---------------------------------------------------------
# The SQLite database is the working database. It keeps the app usable
# when the internet is unavailable, provided Streamlit itself is running
# on a computer/server that remains accessible. A hosted Streamlit website
# cannot be used offline when its hosting server cannot be reached.
#
# When a PostgreSQL URL is configured, the local database is synchronised
# with a cloud snapshot on app reruns. This is intended for ONE primary
# installation/database at a time. It is not multi-device concurrent
# conflict-free replication.
LOCAL_DB_PATH = Path(os.getenv("ALUFATANAAH_DB", "alufatanaah_local.db")).resolve()


@st.cache_resource
def get_sqlalchemy_engine():
    return sqlalchemy.create_engine(
        f"sqlite:///{LOCAL_DB_PATH.as_posix()}",
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,
    )


engine = get_sqlalchemy_engine()


def get_remote_engine():
    try:
        url = st.secrets.get("postgres", {}).get("url") or os.getenv("DATABASE_URL")
        if not url:
            return None
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+psycopg2://", 1)
        elif url.startswith("postgresql://") and "+psycopg" not in url:
            url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
        remote = sqlalchemy.create_engine(url, pool_pre_ping=True, connect_args={"connect_timeout": 4})
        with remote.connect() as c:
            c.execute(sqlalchemy.text("SELECT 1"))
        return remote
    except Exception:
        return None


def safe_read_sql(query_str, params=None):
    try:
        with engine.connect() as conn:
            return pd.read_sql(sqlalchemy.text(query_str), conn, params=params or {})
    except Exception as exc:
        st.warning(f"Database read problem: {exc}")
        return pd.DataFrame()


def _sqlite_columns(conn, table):
    return {r[1] for r in conn.exec_driver_sql(f"PRAGMA table_info({table})").fetchall()}


def _ensure_column(conn, table, column, definition):
    if column not in _sqlite_columns(conn, table):
        conn.exec_driver_sql(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


@st.cache_resource
def init_db():
    with engine.begin() as conn:
        conn.exec_driver_sql("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                phone TEXT UNIQUE NOT NULL,
                email TEXT,
                password TEXT NOT NULL,
                role TEXT DEFAULT 'manager',
                status TEXT DEFAULT 'Active',
                suspension_reason TEXT DEFAULT '',
                recovery_pref TEXT DEFAULT 'Email',
                client_quota INTEGER DEFAULT 50,
                show_quota_to_manager BOOLEAN DEFAULT 0,
                edit_override BOOLEAN DEFAULT 0,
                note_override BOOLEAN DEFAULT 0,
                company_header TEXT DEFAULT 'AlufaTanaah Record Keeper',
                last_greeting_date DATE
            )
        """)
        conn.exec_driver_sql("""
            CREATE TABLE IF NOT EXISTS clients (
                id TEXT PRIMARY KEY, manager_name TEXT, client_name TEXT NOT NULL,
                client_phone TEXT, gender TEXT, location TEXT,
                target_limit REAL DEFAULT 0.0,
                date_registered TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.exec_driver_sql("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                manager_name TEXT, client_name TEXT, client_id TEXT,
                payer_name TEXT DEFAULT '', amount REAL, trans_type TEXT,
                notes TEXT, date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.exec_driver_sql("""
            CREATE TABLE IF NOT EXISTS support_tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                manager_name TEXT, issue_message TEXT, admin_reply TEXT DEFAULT '',
                status TEXT DEFAULT 'Pending', date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.exec_driver_sql("""
            CREATE TABLE IF NOT EXISTS workspace_announcements (
                id INTEGER PRIMARY KEY AUTOINCREMENT, message TEXT NOT NULL,
                updated_by TEXT, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.exec_driver_sql("""
            CREATE TABLE IF NOT EXISTS client_loans (
                client_id TEXT PRIMARY KEY, client_name TEXT, manager_name TEXT,
                initial_loan REAL DEFAULT 0.0, loan_amount REAL DEFAULT 0.0,
                loan_threshold REAL DEFAULT 0.0, is_active BOOLEAN DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # New manager-private debt records
        conn.exec_driver_sql("""
            CREATE TABLE IF NOT EXISTS debts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                manager_name TEXT NOT NULL, client_id TEXT DEFAULT '',
                client_name TEXT NOT NULL, description TEXT DEFAULT '',
                total_amount REAL NOT NULL, paid_amount REAL DEFAULT 0,
                due_date TEXT DEFAULT '', status TEXT DEFAULT 'Open',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.exec_driver_sql("""
            CREATE TABLE IF NOT EXISTS debt_payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT, debt_id INTEGER NOT NULL,
                manager_name TEXT NOT NULL, amount REAL NOT NULL,
                notes TEXT DEFAULT '', paid_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # New manager-private inventory and sales records
        conn.exec_driver_sql("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT, manager_name TEXT NOT NULL,
                product_name TEXT NOT NULL, sku TEXT DEFAULT '',
                quantity INTEGER DEFAULT 0, unit_price REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.exec_driver_sql("""
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT, manager_name TEXT NOT NULL,
                product_id INTEGER, product_name TEXT NOT NULL,
                quantity INTEGER NOT NULL, unit_price REAL NOT NULL,
                total_amount REAL NOT NULL, buyer_name TEXT DEFAULT '',
                sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.exec_driver_sql("""
            CREATE TABLE IF NOT EXISTS sync_meta (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                local_modified TEXT DEFAULT '',
                last_remote_modified TEXT DEFAULT ''
            )
        """)
        conn.exec_driver_sql("INSERT OR IGNORE INTO sync_meta (id, local_modified, last_remote_modified) VALUES (1, '', '')")

        # Migrate older local SQLite databases safely.
        migrations = {
            "users": {
                "email": "TEXT", "role": "TEXT DEFAULT 'manager'",
                "status": "TEXT DEFAULT 'Active'", "suspension_reason": "TEXT DEFAULT ''",
                "recovery_pref": "TEXT DEFAULT 'Email'", "client_quota": "INTEGER DEFAULT 50",
                "show_quota_to_manager": "BOOLEAN DEFAULT 0", "edit_override": "BOOLEAN DEFAULT 0",
                "note_override": "BOOLEAN DEFAULT 0", "company_header": "TEXT DEFAULT 'AlufaTanaah Record Keeper'",
                "last_greeting_date": "DATE"
            },
            "clients": {
                "manager_name": "TEXT", "client_phone": "TEXT", "gender": "TEXT",
                "location": "TEXT", "target_limit": "REAL DEFAULT 0",
                "date_registered": "TIMESTAMP"
            },
            "transactions": {
                "manager_name": "TEXT", "client_name": "TEXT", "client_id": "TEXT",
                "payer_name": "TEXT DEFAULT ''", "amount": "REAL", "trans_type": "TEXT",
                "notes": "TEXT", "date": "TIMESTAMP"
            },
            "support_tickets": {"admin_reply": "TEXT DEFAULT ''", "status": "TEXT DEFAULT 'Pending'"},
        }
        for table, cols in migrations.items():
            for col, definition in cols.items():
                _ensure_column(conn, table, col, definition)

        # Every business-data change marks the local snapshot as needing sync.
        tables = ["users", "clients", "transactions", "support_tickets",
                  "workspace_announcements", "client_loans", "debts",
                  "debt_payments", "products", "sales"]
        for table in tables:
            for action in ("INSERT", "UPDATE", "DELETE"):
                trigger = f"sync_{table}_{action.lower()}"
                conn.exec_driver_sql(f"""
                    CREATE TRIGGER IF NOT EXISTS {trigger}
                    AFTER {action} ON {table}
                    BEGIN
                      UPDATE sync_meta
                      SET local_modified = strftime('%Y-%m-%dT%H:%M:%fZ','now')
                      WHERE id = 1;
                    END
                """)

    # Create the first administrator only when credentials are configured.
    # Existing administrator accounts are never overwritten.
    admin_password = os.getenv("ALUFATANAAH_ADMIN_PASSWORD")
    try:
        admin_password = admin_password or st.secrets.get("admin", {}).get("password")
    except Exception:
        pass
    with engine.begin() as conn:
        existing = conn.execute(sqlalchemy.text(
            "SELECT id FROM users WHERE role = 'admin' LIMIT 1"
        )).first()
        if not existing and admin_password:
            conn.execute(sqlalchemy.text("""
                INSERT INTO users (full_name, phone, email, password, role, status,
                                   client_quota, company_header)
                VALUES ('System Admin', 'admin', 'admin@alufatanaah.com', :pw,
                        'admin', 'Active', 9999, 'AlufaTanaah Record Keeper')
            """), {"pw": hash_password(admin_password)})
    return True


def _sqlite_dump():
    raw = sqlite3.connect(str(LOCAL_DB_PATH))
    try:
        return "\n".join(raw.iterdump())
    finally:
        raw.close()


def _replace_local_database(sql_dump, remote_timestamp):
    temp_path = LOCAL_DB_PATH.with_suffix(".restore.tmp")
    if temp_path.exists():
        temp_path.unlink()
    raw = sqlite3.connect(str(temp_path))
    try:
        raw.executescript(sql_dump)
        raw.commit()
    finally:
        raw.close()
    engine.dispose()
    os.replace(temp_path, LOCAL_DB_PATH)
    # Re-create cache entry is not needed: engine reopens the replaced file.
    with engine.begin() as conn:
        conn.exec_driver_sql("""
            CREATE TABLE IF NOT EXISTS sync_meta (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                local_modified TEXT DEFAULT '',
                last_remote_modified TEXT DEFAULT ''
            )
        """)
        conn.execute(sqlalchemy.text("""
            UPDATE sync_meta SET local_modified=:ts, last_remote_modified=:ts WHERE id=1
        """), {"ts": remote_timestamp})


def _local_has_records_missing_from_snapshot(sql_dump):
    """Return True if restoring this cloud snapshot would remove local accounts or records.

    Admin rows are excluded because the configured admin is safely re-created
    after restore. Manager rows and every manager/business table are protected.
    Matching ignores SQLite autoincrement IDs but compares the remaining fields.
    """
    temp_path = LOCAL_DB_PATH.with_suffix(".safety-check.tmp")
    if temp_path.exists():
        temp_path.unlink()
    cloud_db = sqlite3.connect(str(temp_path))
    local_db = sqlite3.connect(str(LOCAL_DB_PATH))
    try:
        cloud_db.executescript(sql_dump)
        cloud_tables = {
            row[0] for row in cloud_db.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        local_tables = {
            row[0] for row in local_db.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        protected_tables = (local_tables - {"sync_meta", "sqlite_sequence"})
        for table in protected_tables:
            local_info = local_db.execute(f'PRAGMA table_info("{table}")').fetchall()
            local_columns = [r[1] for r in local_info if r[1] != "id"]
            if not local_columns:
                continue
            if table not in cloud_tables:
                local_count = local_db.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
                if local_count:
                    return True
                continue
            cloud_column_names = {
                r[1] for r in cloud_db.execute(f'PRAGMA table_info("{table}")').fetchall()
            }
            common = [c for c in local_columns if c in cloud_column_names]
            if not common:
                continue
            quoted = ", ".join('"' + c.replace('"', '""') + '"' for c in common)
            local_rows = local_db.execute(f'SELECT {quoted} FROM "{table}"').fetchall()
            cloud_rows = cloud_db.execute(f'SELECT {quoted} FROM "{table}"').fetchall()
            if table == "users" and "role" in common:
                role_index = common.index("role")
                local_rows = [r for r in local_rows if str(r[role_index] or "manager") != "admin"]
                cloud_rows = [r for r in cloud_rows if str(r[role_index] or "manager") != "admin"]
            from collections import Counter
            cloud_counts = Counter(cloud_rows)
            local_counts = Counter(local_rows)
            if any(count > cloud_counts[row] for row, count in local_counts.items()):
                return True
        return False
    finally:
        local_db.close()
        cloud_db.close()
        if temp_path.exists():
            temp_path.unlink()


def sync_local_and_cloud():
    """Best-effort single-installation snapshot sync. Runs on each app rerun."""
    remote = get_remote_engine()
    if remote is None:
        return "Offline mode — saved on this device; cloud sync will retry when online."
    try:
        with remote.begin() as conn:
            conn.execute(sqlalchemy.text("""
                CREATE TABLE IF NOT EXISTS alufatanaah_sync_snapshot (
                    id INTEGER PRIMARY KEY,
                    snapshot_text TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """))
            cloud_row = conn.execute(sqlalchemy.text(
                "SELECT snapshot_text, updated_at FROM alufatanaah_sync_snapshot WHERE id=1"
            )).first()

        with engine.connect() as conn:
            meta = conn.execute(sqlalchemy.text(
                "SELECT local_modified, last_remote_modified FROM sync_meta WHERE id=1"
            )).first()
            local_user_count = int(conn.execute(sqlalchemy.text(
                "SELECT COUNT(*) FROM users"
            )).scalar() or 0)
            local_business_count = 0
            for table in ("clients", "transactions", "support_tickets",
                          "workspace_announcements", "client_loans", "debts",
                          "products", "sales"):
                local_business_count += int(conn.execute(
                    sqlalchemy.text(f"SELECT COUNT(*) FROM {table}")
                ).scalar() or 0)
        local_modified = str(meta[0] or "")
        last_remote = str(meta[1] or "")

        # Import the old PostgreSQL database once, including when a newly
        # configured local admin account already exists.
        should_import_legacy = (
            cloud_row is None and
            (local_user_count == 0 or (local_user_count <= 1 and local_business_count == 0))
        )
        if should_import_legacy:
            try:
                remote_tables = set(inspect(remote).get_table_names())
                legacy_tables = ["users", "clients", "transactions", "support_tickets",
                                 "workspace_announcements", "client_loans"]
                with engine.begin() as local_conn:
                    for table in legacy_tables:
                        if table not in remote_tables:
                            continue
                        old_df = pd.read_sql(sqlalchemy.text(f"SELECT * FROM {table}"), remote)
                        if old_df.empty:
                            continue
                        if table == "users" and local_user_count == 1 and "phone" in old_df.columns:
                            old_df = old_df[old_df["phone"].astype(str) != "admin"]
                        if old_df.empty:
                            continue
                        local_cols = _sqlite_columns(local_conn, table)
                        common = [c for c in old_df.columns if c in local_cols]
                        if not common:
                            continue
                        old_df[common].to_sql(table, local_conn, if_exists="append",
                                              index=False, method=None)
                local_modified = "legacy-import"
            except Exception:
                pass
            cloud_row = None

        if cloud_row is not None:
            cloud_dump, cloud_updated = str(cloud_row[0]), str(cloud_row[1])
            if local_modified and local_modified != last_remote and local_modified != "legacy-import":
                # Local edits win when both copies changed. Use one primary local installation.
                if cloud_updated != last_remote:
                    pass
                else:
                    cloud_dump = None
            elif cloud_updated != last_remote:
                # Never replace local data with an older/incomplete cloud snapshot.
                # If any locally registered manager or business record is absent
                # from the snapshot, keep the local copy and publish it instead.
                if _local_has_records_missing_from_snapshot(cloud_dump):
                    with engine.begin() as conn:
                        conn.execute(sqlalchemy.text("""
                            UPDATE sync_meta
                            SET local_modified=:ts
                            WHERE id=1
                        """), {"ts": datetime.utcnow().isoformat(timespec="microseconds") + "Z"})
                    cloud_dump = None
                else:
                    _replace_local_database(cloud_dump, cloud_updated)
                    return "Online — cloud changes downloaded to this device."

        # Push local snapshot if it is new or changed.
        with engine.connect() as conn:
            meta2 = conn.execute(sqlalchemy.text(
                "SELECT local_modified, last_remote_modified FROM sync_meta WHERE id=1"
            )).first()
        dirty = str(meta2[0] or "") != str(meta2[1] or "")
        if cloud_row is None or dirty:
            dump_text = _sqlite_dump()
            stamp = datetime.utcnow().isoformat(timespec="microseconds") + "Z"
            with remote.begin() as conn:
                conn.execute(sqlalchemy.text("""
                    INSERT INTO alufatanaah_sync_snapshot (id, snapshot_text, updated_at)
                    VALUES (1, :snapshot, :stamp)
                    ON CONFLICT (id) DO UPDATE
                    SET snapshot_text = EXCLUDED.snapshot_text, updated_at = EXCLUDED.updated_at
                """), {"snapshot": dump_text, "stamp": stamp})
            with engine.begin() as conn:
                conn.execute(sqlalchemy.text("""
                    UPDATE sync_meta SET local_modified=:stamp, last_remote_modified=:stamp WHERE id=1
                """), {"stamp": stamp})
        return "Online — local data synchronised with cloud."
    except Exception as exc:
        return f"Local mode active — cloud sync will retry. ({str(exc)[:140]})"


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
                conn.execute(sqlalchemy.text(
                    "UPDATE users SET last_greeting_date = :d WHERE id = :id"
                ), {"d": today_ghana, "id": int(user_row["id"])})
        except Exception:
            pass


def hash_password(password):
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 310000)
    return "pbkdf2_sha256$310000${}${}".format(
        salt.hex(), digest.hex()
    )


def verify_password(stored, supplied):
    stored = str(stored or "")
    if stored.startswith("pbkdf2_sha256$"):
        try:
            _, rounds, salt_hex, digest_hex = stored.split("$", 3)
            actual = hashlib.pbkdf2_hmac(
                "sha256", supplied.encode("utf-8"), bytes.fromhex(salt_hex), int(rounds)
            ).hex()
            return hmac.compare_digest(actual, digest_hex), False
        except Exception:
            return False, False
    # Legacy plain-text password: allow one successful login, then upgrade it.
    if not supplied:
        return False, False
    return hmac.compare_digest(stored, supplied), True


init_db()
SYNC_STATUS = sync_local_and_cloud()

# Ensure a configured administrator still exists AFTER cloud snapshot restore.
# A restored snapshot may not contain the locally seeded first admin account.
def ensure_configured_admin():
    configured_admin_password = os.getenv("ALUFATANAAH_ADMIN_PASSWORD")
    try:
        configured_admin_password = (
            configured_admin_password or st.secrets.get("admin", {}).get("password")
        )
    except Exception:
        pass
    if not configured_admin_password:
        return
    with engine.begin() as conn:
        existing_admin = conn.execute(sqlalchemy.text(
            "SELECT id FROM users WHERE role = 'admin' LIMIT 1"
        )).first()
        if not existing_admin:
            conn.execute(sqlalchemy.text("""
                INSERT INTO users (full_name, phone, email, password, role, status,
                                   client_quota, company_header)
                VALUES ('System Admin', 'admin', 'admin@alufatanaah.com', :pw,
                        'admin', 'Active', 9999, 'AlufaTanaah Record Keeper')
            """), {"pw": hash_password(configured_admin_password)})

ensure_configured_admin()

try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=60000, key="alufatanaah_cloud_sync_refresh")
except Exception:
    pass


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
        valid, was_legacy = verify_password(user["password"], login_pass)
        if valid:
          if was_legacy:
            with engine.begin() as conn:
              conn.execute(
                  sqlalchemy.text("UPDATE users SET password=:p WHERE id=:id"),
                  {"p": hash_password(login_pass), "id": int(user["id"])},
              )
            user["password"] = hash_password(login_pass)
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
        if reg_name and reg_phone and len(reg_pass) >= 10:
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
                      "passwd": hash_password(reg_pass),
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
              "Enter your name and phone number, and use a password of at least 10 characters."
          )
  with tab3:
    st.subheader("Recover Password")
    st.warning(
        "For your account's protection, password reset cannot be completed "
        "using only a phone number or email address. Contact your system "
        "administrator and ask them to reset your account password."
    )
    st.info(
        "Your administrator can issue a temporary password. After receiving it, "
        "sign in and ask for a password change before sharing access to your account."
    )


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
        "📊 Admin Overview",
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
        "💳 Debt Management",
        "📦 Inventory & Sales",
        "🛠️ Report App Issue / Problem",
    ]

  st.sidebar.caption(f"🔄 {SYNC_STATUS}")
  nav = st.sidebar.radio("Navigation", nav_options)
  if st.sidebar.button("Log Out"):
    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.last_receipt = None
    st.session_state.daily_greeting_banner = None
    st.session_state.loan_feedback = None
    st.rerun()

  # ADMIN OVERVIEW: totals only; no client names, ledgers, or transaction rows.
  if nav == "📊 Admin Overview":
    if not is_admin:
      st.error("Unauthorized access.")
      return
    st.title("🛡️ Administration Overview")
    total_clients = int(safe_read_sql("SELECT COUNT(*) AS n FROM clients").iloc[0]["n"])
    total_managers = int(safe_read_sql(
        "SELECT COUNT(*) AS n FROM users WHERE role != 'admin'"
    ).iloc[0]["n"])
    a1, a2 = st.columns(2)
    a1.metric("Total Registered Clients", total_clients)
    a2.metric("Total Signed-Up Managers", total_managers)
    st.info(
        "Privacy protection is enabled: this administrator account cannot "
        "open individual client records, transaction histories, debt records, "
        "or inventory and sales records."
    )
    st.markdown("---")
    st.subheader("🔐 Change Administrator Password")
    with st.form("admin_change_password_form", clear_on_submit=True):
      admin_current_pw = st.text_input("Current Administrator Password", type="password")
      admin_new_pw = st.text_input("New Password (at least 10 characters)", type="password")
      admin_confirm_pw = st.text_input("Confirm New Password", type="password")
      admin_change_pw = st.form_submit_button("Update Administrator Password")
      if admin_change_pw:
        valid_admin_pw, _ = verify_password(user.get("password", ""), admin_current_pw)
        if not valid_admin_pw:
          st.error("Current administrator password is incorrect.")
        elif len(admin_new_pw) < 10:
          st.error("Use at least 10 characters for the new password.")
        elif admin_new_pw != admin_confirm_pw:
          st.error("The new passwords do not match.")
        else:
          new_hash = hash_password(admin_new_pw)
          with engine.begin() as conn:
            conn.execute(
                sqlalchemy.text("UPDATE users SET password=:p WHERE id=:id"),
                {"p": new_hash, "id": int(user["id"])},
            )
          st.session_state.user["password"] = new_hash
          st.success("Administrator password updated.")
          st.rerun()

  # 1. REGISTER CLIENT
  elif nav == "👥 Register Client":
    if is_admin:
      st.error("Administrators cannot access individual client records.")
      return
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
    if is_admin:
      st.error("Administrators cannot access individual client transactions.")
      return
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
    if is_admin:
      st.error("This setting belongs to the manager's private workspace.")
      return
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

    st.markdown("---")
    st.subheader("🔐 Change Your Password")
    with st.form("manager_change_password_form", clear_on_submit=True):
      current_password = st.text_input("Current Password", type="password")
      new_password = st.text_input("New Password (at least 10 characters)", type="password")
      confirm_new_password = st.text_input("Confirm New Password", type="password")
      change_password = st.form_submit_button("Update Password")
      if change_password:
        valid_current, _ = verify_password(user.get("password", ""), current_password)
        if not valid_current:
          st.error("Your current password is incorrect.")
        elif len(new_password) < 10:
          st.error("The new password must contain at least 10 characters.")
        elif new_password != confirm_new_password:
          st.error("The new passwords do not match.")
        else:
          with engine.begin() as conn:
            conn.execute(
                sqlalchemy.text("UPDATE users SET password=:p WHERE id=:id"),
                {"p": hash_password(new_password), "id": int(user["id"])},
            )
          st.session_state.user["password"] = hash_password(new_password)
          st.success("Your password has been changed successfully.")
          st.rerun()

  # 4. MY CLIENTS & RECORDS + SHARED CLIENT LEDGER LOOKUP
  elif nav == "📊 My Clients & Records":
    if is_admin:
      st.error("Administrators cannot view individual client records or transactions.")
      return
    st.subheader("📊 Workspace Clients, Transaction Sums & Search Filtering")
    if False:
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
    if is_admin:
      st.error("Administrators cannot access individual client target records.")
      return
    st.subheader("🎯 Client Target Limits")
    if False:
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
    if is_admin:
      st.error("Administrators cannot export individual client transaction records.")
      return
    st.subheader("📥 Export Transaction Records")
    if False:
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


  # 7. DEBT MANAGEMENT — PRIVATE TO THE SIGNED-IN MANAGER
  elif nav == "💳 Debt Management":
    if is_admin:
      st.error("Debt records are private to each manager.")
      return
    st.subheader("💳 Debt Management")
    st.caption("Only you can view and manage debts recorded in your workspace.")
    with st.form("add_debt_form", clear_on_submit=True):
      debt_client_name = st.text_input("Client / Debtor Name")
      debt_desc = st.text_input("Debt Description / Reason")
      debt_total = st.number_input("Total Debt (GHS)", min_value=0.01, step=10.0)
      debt_due = st.date_input("Due Date")
      add_debt = st.form_submit_button("Save Debt")
      if add_debt:
        if not debt_client_name.strip():
          st.warning("Enter the debtor's name.")
        else:
          with engine.begin() as conn:
            conn.execute(sqlalchemy.text("""
                INSERT INTO debts
                (manager_name, client_name, description, total_amount, paid_amount, due_date, status)
                VALUES (:m, :n, :d, :total, 0, :due, 'Open')
            """), {
                "m": user["full_name"], "n": debt_client_name.strip(),
                "d": debt_desc.strip(), "total": float(debt_total),
                "due": str(debt_due)
            })
          st.success("Debt saved.")
          st.rerun()

    df_debts = safe_read_sql(
        "SELECT id, client_name, description, total_amount, paid_amount, "
        "(total_amount-paid_amount) AS balance_due, due_date, status, created_at "
        "FROM debts WHERE manager_name=:m ORDER BY id DESC",
        {"m": user["full_name"]}
    )
    if not df_debts.empty:
      st.dataframe(df_debts, use_container_width=True, hide_index=True)
      open_debts = df_debts[df_debts["balance_due"].astype(float) > 0.00001]
      if not open_debts.empty:
        debt_options = {
            f"#{int(r['id'])} — {r['client_name']} — GHS {float(r['balance_due']):,.2f}":
            int(r["id"]) for _, r in open_debts.iterrows()
        }
        selected_debt_label = st.selectbox("Select debt to receive payment", list(debt_options))
        selected_debt_id = debt_options[selected_debt_label]
        with st.form("debt_payment_form", clear_on_submit=True):
          debt_payment = st.number_input("Amount Received (GHS)", min_value=0.01, step=5.0)
          debt_payment_note = st.text_input("Payment Note (Optional)")
          submit_debt_payment = st.form_submit_button("Record Debt Payment")
          if submit_debt_payment:
            row = open_debts[open_debts["id"] == selected_debt_id].iloc[0]
            outstanding = float(row["balance_due"])
            if debt_payment > outstanding:
              st.error(f"Payment cannot exceed the outstanding balance of GHS {outstanding:,.2f}.")
            else:
              new_paid = float(row["paid_amount"]) + float(debt_payment)
              new_status = "Paid" if new_paid >= float(row["total_amount"]) - 0.00001 else "Part-paid"
              with engine.begin() as conn:
                conn.execute(sqlalchemy.text("""
                    INSERT INTO debt_payments (debt_id, manager_name, amount, notes)
                    VALUES (:id, :m, :amount, :notes)
                """), {"id": selected_debt_id, "m": user["full_name"],
                       "amount": float(debt_payment), "notes": debt_payment_note.strip()})
                conn.execute(sqlalchemy.text("""
                    UPDATE debts SET paid_amount=:paid, status=:status
                    WHERE id=:id AND manager_name=:m
                """), {"paid": new_paid, "status": new_status,
                       "id": selected_debt_id, "m": user["full_name"]})
              st.success("Debt payment recorded.")
              st.rerun()
      st.markdown("---")
      st.subheader("Debt Payment History")
      df_debt_payments = safe_read_sql(
          "SELECT p.id, p.debt_id, d.client_name, p.amount, p.notes, p.paid_at "
          "FROM debt_payments p JOIN debts d ON d.id=p.debt_id "
          "WHERE p.manager_name=:m ORDER BY p.paid_at DESC",
          {"m": user["full_name"]}
      )
      if not df_debt_payments.empty:
        st.dataframe(df_debt_payments, use_container_width=True, hide_index=True)
    else:
      st.info("You have not recorded any debts yet.")

  # 8. INVENTORY & SALES — PRIVATE TO THE SIGNED-IN MANAGER
  elif nav == "📦 Inventory & Sales":
    if is_admin:
      st.error("Inventory and sales records are private to each manager.")
      return
    st.subheader("📦 Inventory & Sales Management")
    st.caption("Your products, stock quantities, and sales are not visible to other managers or the administrator.")
    with st.expander("➕ Add a Product", expanded=False):
      with st.form("add_product_form", clear_on_submit=True):
        product_name = st.text_input("Product Name")
        product_sku = st.text_input("Product Code / SKU (Optional)")
        product_qty = st.number_input("Opening Stock Quantity", min_value=0, step=1)
        product_price = st.number_input("Selling Price per Unit (GHS)", min_value=0.0, step=1.0)
        add_product = st.form_submit_button("Save Product")
        if add_product:
          if not product_name.strip():
            st.warning("Enter a product name.")
          else:
            with engine.begin() as conn:
              conn.execute(sqlalchemy.text("""
                  INSERT INTO products (manager_name, product_name, sku, quantity, unit_price)
                  VALUES (:m, :name, :sku, :qty, :price)
              """), {"m": user["full_name"], "name": product_name.strip(),
                     "sku": product_sku.strip(), "qty": int(product_qty),
                     "price": float(product_price)})
            st.success("Product added to inventory.")
            st.rerun()

    df_products = safe_read_sql(
        "SELECT id, product_name, sku, quantity, unit_price, "
        "(quantity*unit_price) AS stock_value FROM products "
        "WHERE manager_name=:m ORDER BY product_name",
        {"m": user["full_name"]}
    )
    st.subheader("Current Stock")
    if not df_products.empty:
      st.dataframe(df_products, use_container_width=True, hide_index=True)
      available = df_products[df_products["quantity"].astype(int) > 0]
      if not available.empty:
        product_options = {
            f"{r['product_name']} (Stock: {int(r['quantity'])}) — GHS {float(r['unit_price']):,.2f}":
            int(r["id"]) for _, r in available.iterrows()
        }
        with st.form("record_sale_form", clear_on_submit=True):
          chosen_product_label = st.selectbox("Product Sold", list(product_options))
          sale_qty = st.number_input("Quantity Sold", min_value=1, step=1)
          buyer_name = st.text_input("Customer / Buyer (Optional)")
          record_sale = st.form_submit_button("Record Sale")
          if record_sale:
            product_id = product_options[chosen_product_label]
            product_row = available[available["id"] == product_id].iloc[0]
            stock_now = int(product_row["quantity"])
            if int(sale_qty) > stock_now:
              st.error(f"Insufficient stock. Available quantity: {stock_now}.")
            else:
              unit_price = float(product_row["unit_price"])
              total = unit_price * int(sale_qty)
              with engine.begin() as conn:
                conn.execute(sqlalchemy.text("""
                    UPDATE products SET quantity=quantity-:qty
                    WHERE id=:id AND manager_name=:m AND quantity>=:qty
                """), {"qty": int(sale_qty), "id": product_id, "m": user["full_name"]})
                conn.execute(sqlalchemy.text("""
                    INSERT INTO sales
                    (manager_name, product_id, product_name, quantity, unit_price, total_amount, buyer_name)
                    VALUES (:m, :pid, :name, :qty, :price, :total, :buyer)
                """), {"m": user["full_name"], "pid": product_id,
                       "name": product_row["product_name"], "qty": int(sale_qty),
                       "price": unit_price, "total": total, "buyer": buyer_name.strip()})
              st.success(f"Sale recorded. Total: GHS {total:,.2f}")
              st.rerun()
      else:
        st.info("No stock is currently available for sale.")
    else:
      st.info("Add your first product to begin inventory management.")

    st.markdown("---")
    st.subheader("Sales History")
    df_sales = safe_read_sql(
        "SELECT id, product_name, quantity, unit_price, total_amount, buyer_name, sale_date "
        "FROM sales WHERE manager_name=:m ORDER BY sale_date DESC",
        {"m": user["full_name"]}
    )
    if not df_sales.empty:
      st.dataframe(df_sales, use_container_width=True, hide_index=True)
      st.metric("Total Sales Value (GHS)", f"{float(df_sales['total_amount'].sum()):,.2f}")
    else:
      st.info("No sales recorded yet.")

  # 9. REPORT ISSUE (MANAGER)
  elif nav == "🛠️ Report App Issue / Problem":
    if is_admin:
      st.error("Use the administrator support centre.")
      return
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

    total_registered_clients = int(
        safe_read_sql("SELECT COUNT(*) AS n FROM clients").iloc[0]["n"]
    )
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Total Signed-Up Managers", total_managers)
    m2.metric("Active Managers", active_managers)
    m3.metric("Frozen Managers", frozen_managers)
    m4.metric("Total Registered Clients", total_registered_clients)
    m5.metric("Total Client Quota", total_allocated_quota)

    # Aggregate client registrations by manager. This deliberately exposes
    # counts only; it does not show client names, contacts, or transactions.
    st.markdown("---")
    st.subheader("👥 Registered Clients Under Each Manager")
    if not df_managers.empty:
      manager_client_summary = df_managers[[
          "full_name", "phone", "status", "client_quota"
      ]].copy()
      manager_client_summary["Total Registered Clients"] = (
          manager_client_summary["full_name"].map(count_map).fillna(0).astype(int)
      )
      manager_client_summary = manager_client_summary.rename(columns={
          "full_name": "Manager",
          "phone": "Phone",
          "status": "Account Status",
          "client_quota": "Client Quota",
      })
      manager_client_summary = manager_client_summary[[
          "Manager", "Phone", "Account Status",
          "Total Registered Clients", "Client Quota"
      ]].sort_values(
          by=["Total Registered Clients", "Manager"],
          ascending=[False, True],
      )
      st.dataframe(
          manager_client_summary,
          use_container_width=True,
          hide_index=True,
      )
      st.caption(
          "Counts are grouped by manager. This summary does not expose "
          "individual client records or transaction details."
      )
    else:
      st.info("No managers have signed up yet.")

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

        with st.form(f"admin_password_reset_{row['id']}"):
          temp_password = st.text_input(
              "Set a temporary password for this manager",
              type="password",
              key=f"temp_pw_{row['id']}",
          )
          if st.form_submit_button("Set Temporary Password"):
            if len(temp_password) < 10:
              st.error("Use at least 10 characters for the temporary password.")
            else:
              with engine.begin() as conn:
                conn.execute(
                    sqlalchemy.text("UPDATE users SET password=:p WHERE id=:id"),
                    {"p": hash_password(temp_password), "id": int(row["id"])},
                )
              st.success("Temporary password updated. Share it securely with the manager.")
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
