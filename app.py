import os
import random
import pandas as pd
import sqlalchemy
import streamlit as st

# ---------------------------------------------------------
# PAGE CONFIGURATION & MOBILE OPTIMIZATION
# ---------------------------------------------------------
st.set_page_config(
    page_title="SusuFlow Enterprise",
    page_icon="💰",
    layout="centered",
    initial_sidebar_state="expanded",
)

# Custom CSS for Mobile Performance and Print-Isolated Receipts
st.markdown(
    """
    <style>
    /* Hide Streamlit header, footer, and sidebar when printing or saving as PDF */
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

    /* Android Mobile Screen Sized Receipt */
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
        font-size: 18px;
        margin-bottom: 0;
    }
    .receipt-subtitle {
        text-align: center;
        font-size: 12px;
        color: #666;
        margin-bottom: 15px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# DATABASE CONNECTION & INITIALIZATION
# ---------------------------------------------------------
def get_sqlalchemy_engine():
  try:
    database_url = st.secrets["postgres"]["url"]
    # Ensure SQLAlchemy uses psycopg2 driver
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
  with engine.begin() as conn:
    conn.execute(
        sqlalchemy.text("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                full_name TEXT NOT NULL,
                phone TEXT UNIQUE NOT NULL,
                email TEXT,
                password TEXT NOT NULL,
                role TEXT DEFAULT 'collector',
                status TEXT DEFAULT 'Active',
                recovery_pref TEXT DEFAULT 'Email',
                subscription_status TEXT DEFAULT 'Inactive',
                momo_ref TEXT
            )
        """)
    )
    conn.execute(
        sqlalchemy.text("""
            CREATE TABLE IF NOT EXISTS transactions (
                id SERIAL PRIMARY KEY,
                collector_name TEXT,
                client_name TEXT,
                amount FLOAT,
                trans_type TEXT,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    )


init_db()


# ---------------------------------------------------------
# AUTHENTICATION & SESSION MANAGEMENT
# ---------------------------------------------------------
if "logged_in" not in st.session_state:
  st.session_state.logged_in = False
  st.session_state.user = None


def render_auth():
  st.title("💰 SusuFlow Enterprise")
  tab1, tab2, tab3 = st.tabs(
      ["Login", "Register (Full Name)", "Password Recovery"]
  )

  with tab1:
    st.subheader("Sign In")
    login_phone = st.text_input("Phone Number or Email", key="login_id")
    login_pass = st.text_input("Password", type="password", key="login_pw")

    if st.button("Log In"):
      query = sqlalchemy.text(
          "SELECT * FROM users WHERE phone = :id OR email = :id"
      )
      df = pd.read_sql(query, engine, params={"id": login_phone})
      if not df.empty:
        user = df.iloc[0]
        if user["password"] == login_pass:
          if user["status"] == "Frozen":
            st.error(
                "⚠️ Your account has been frozen by the admin. Contact"
                " management."
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
    st.subheader("Create New Account")
    reg_name = st.text_input("Full Name (e.g., Kofi Mensah)")
    reg_phone = st.text_input("Phone Number")
    reg_email = st.text_input("Email Address (Optional)")
    reg_pass = st.text_input("Create Password", type="password")
    reg_role = st.selectbox("Account Role", ["collector", "admin"])
    recovery_choice = st.radio(
        "Preferred Password Recovery Channel:",
        ["Email", "Phone (SMS/WhatsApp)"],
    )

    if st.button("Register Account"):
      if reg_name and reg_phone and reg_pass:
        try:
          with engine.begin() as conn:
            conn.execute(
                sqlalchemy.text("""
                            INSERT INTO users (full_name, phone, email, password, role, recovery_pref)
                            VALUES (:name, :phone, :email, :passwd, :role, :rec)
                        """),
                {
                    "name": reg_name,
                    "phone": reg_phone,
                    "email": reg_email,
                    "passwd": reg_pass,
                    "role": reg_role,
                    "rec": recovery_choice,
                },
            )
          st.success(
              "Registration successful! You can now log in using the Login tab."
          )
        except Exception as e:
          st.error(
              f"Error registering user (Phone might already exist): {e}"
          )
      else:
        st.warning("Please fill in Full Name, Phone Number, and Password.")

  with tab3:
    st.subheader("Password Recovery")
    rec_id = st.text_input("Enter your registered Phone or Email")
    if st.button("Send Recovery Code"):
      df = pd.read_sql(
          sqlalchemy.text(
              "SELECT * FROM users WHERE phone = :id OR email = :id"
          ),
          engine,
          params={"id": rec_id},
      )
      if not df.empty:
        pref = df.iloc[0]["recovery_pref"]
        code = random.randint(100000, 999999)
        st.success(
            f"Recovery code `{code}` generated and sent via your preferred"
            f" channel: **{pref}**."
        )
      else:
        st.error("No account matches that identifier.")


# ---------------------------------------------------------
# SUBSCRIPTION GATE FOR FULL ACCESS
# ---------------------------------------------------------
def check_subscription():
  user = st.session_state.user
  if user["role"] == "admin":
    return  # Admins bypass subscription check

  if user["subscription_status"] != "Active":
    st.warning("⚠️ Full Platform Access Requires Active Subscription")
    st.info(
        "Please send your subscription fee to the Admin/Developer MoMo Number:"
        " **0542470810** (Name: **Koffi Rogers**)."
    )

    with st.form("sub_form"):
      momo_ref = st.text_input("Enter Mobile Money Transaction Reference ID")
      if st.form_submit_button("Submit Payment Reference"):
        if momo_ref:
          with engine.begin() as conn:
            conn.execute(
                sqlalchemy.text(
                    "UPDATE users SET momo_ref = :ref WHERE id = :uid"
                ),
                {"ref": momo_ref, "uid": user["id"]},
            )
          st.success(
              "Reference submitted successfully! Waiting for admin activation."
          )
        else:
          st.warning("Please provide the transaction reference.")
    st.stop()


# ---------------------------------------------------------
# COLLECTOR DASHBOARD
# ---------------------------------------------------------
def render_collector_dashboard():
  user = st.session_state.user
  st.sidebar.title(f"👤 {user['full_name']}")
  st.sidebar.markdown("Storage: **Cloud PostgreSQL (Neon)**")

  nav = st.sidebar.radio(
      "Navigation",
      [
          "📥 Take Transaction Input",
          "📊 Clients Progress Score",
          "🎯 Target Limits",
      ],
  )

  if st.sidebar.button("Log Out"):
    st.session_state.logged_in = False
    st.session_state.user = None
    st.rerun()

  if nav == "📥 Take Transaction Input":
    st.subheader("📥 Record Daily Susu Deposit / Withdrawal")

    with st.form("trans_form"):
      client_name = st.text_input("Client Full Name")
      amount = st.number_input("Amount (GHS)", min_value=0.0, step=1.0)
      trans_type = st.selectbox("Transaction Type", ["Deposit", "Withdrawal"])

      submitted = st.form_submit_button("Save & Generate Receipt")
      if submitted and client_name and amount > 0:
        with engine.begin() as conn:
          conn.execute(
              sqlalchemy.text("""
                        INSERT INTO transactions (collector_name, client_name, amount, trans_type)
                        VALUES (:col, :client, :amt, :type)
                    """),
              {
                  "col": user["full_name"],
                  "client": client_name,
                  "amt": amount,
                  "type": trans_type,
              },
          )
        st.success("Transaction recorded successfully!")

        # Display Mobile-Sized Receipt with Print Isolation
        st.markdown("### Official Transaction Receipt")
        receipt_html = f"""
                <div class="receipt-container">
                    <p class="receipt-title">SusuFlow Enterprise</p>
                    <p class="receipt-subtitle">Mobile Receipt & Record</p>
                    <hr style="border: 0.5px dashed #ccc;">
                    <p><b>Date:</b> {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}</p>
                    <p><b>Client:</b> {client_name}</p>
                    <p><b>Collector:</b> {user['full_name']}</p>
                    <p><b>Type:</b> {trans_type}</p>
                    <p><b>Amount:</b> GHS {amount:.2f}</p>
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

  elif nav == "📊 Clients Progress Score":
    st.subheader("📊 Clients Progress Score Comparison")
    df_trans = pd.read_sql(
        sqlalchemy.text(
            "SELECT client_name, SUM(amount) as total_saved FROM transactions"
            " WHERE trans_type='Deposit' GROUP BY client_name"
        ),
        engine,
    )
    if not df_trans.empty:
      st.dataframe(df_trans, use_container_width=True)
      st.bar_chart(df_trans.set_index("client_name")["total_saved"])
    else:
      st.info("No transaction data available yet.")

  elif nav == "🎯 Target Limits":
    st.subheader("🎯 Target Limits & Collection Goals")
    st.metric(label="Monthly Collection Target", value="GHS 10,000.00")
    df_tot = pd.read_sql(
        sqlalchemy.text(
            "SELECT COALESCE(SUM(amount), 0) as collected FROM transactions"
            " WHERE trans_type='Deposit'"
        ),
        engine,
    )
    collected = df_tot.iloc[0]["collected"]
    st.progress(
        min(collected / 10000.0, 1.0),
        text=f"Progress: GHS {collected:.2f} / GHS 10,000.00",
    )


# ---------------------------------------------------------
# ADMIN DASHBOARD
# ---------------------------------------------------------
def render_admin_dashboard():
  user = st.session_state.user
  st.sidebar.title(f"🛡️ Admin: {user['full_name']}")

  admin_nav = st.sidebar.radio(
      "Admin Panel",
      [
          "👥 Manage Collectors & Freeze",
          "💳 Subscriptions & MoMo Verification",
      ],
  )

  if st.sidebar.button("Log Out"):
    st.session_state.logged_in = False
    st.session_state.user = None
    st.rerun()

  if admin_nav == "👥 Manage Collectors & Freeze":
    st.subheader("Collector Account Governance")
    df_users = pd.read_sql(
        sqlalchemy.text(
            "SELECT id, full_name, phone, role, status FROM users"
        ),
        engine,
    )

    for idx, row in df_users.iterrows():
      cols = st.columns([3, 2, 2])
      cols[0].write(f"**{row['full_name']}** ({row['phone']})")
      cols[1].write(f"Status: `{row['status']}`")

      if row["status"] == "Active":
        if cols[2].button("Freeze", key=f"freeze_{row['id']}"):
          with engine.begin() as conn:
            conn.execute(
                sqlalchemy.text(
                    "UPDATE users SET status = 'Frozen' WHERE id = :id"
                ),
                {"id": row["id"]},
            )
          st.warning(f"Account {row['full_name']} frozen.")
          st.rerun()
      else:
        if cols[2].button("Unfreeze", key=f"unfreeze_{row['id']}"):
          with engine.begin() as conn:
            conn.execute(
                sqlalchemy.text(
                    "UPDATE users SET status = 'Active' WHERE id = :id"
                ),
                {"id": row["id"]},
            )
          st.success(f"Account {row['full_name']} restored.")
          st.rerun()

  elif admin_nav == "💳 Subscriptions & MoMo Verification":
    st.subheader("MoMo Payment Verifications")
    df_subs = pd.read_sql(
        sqlalchemy.text(
            "SELECT id, full_name, phone, subscription_status, momo_ref FROM"
            " users WHERE momo_ref IS NOT NULL"
        ),
        engine,
    )
    if not df_subs.empty:
      for idx, row in df_subs.iterrows():
        st.write(
            f"**{row['full_name']}** | MoMo Ref: `{row['momo_ref']}` | Status:"
            f" `{row['subscription_status']}`"
        )
        if row["subscription_status"] != "Active":
          if st.button(
              f"Approve Subscription for {row['full_name']}",
              key=f"sub_{row['id']}",
          ):
            with engine.begin() as conn:
              conn.execute(
                  sqlalchemy.text(
                      "UPDATE users SET subscription_status = 'Active' WHERE id"
                      " = :id"
                  ),
                  {"id": row["id"]},
              )
            st.success(
                f"Subscription activated for {row['full_name']} successfully!"
            )
            st.rerun()
        else:
          st.success("Subscription Active")
    else:
      st.info("No pending subscription verification requests.")


        # ---------------------------------------------------------
# MAIN APP ROUTER
# ---------------------------------------------------------
if not st.session_state.logged_in:
  render_auth()
else:
  check_subscription()
  current_user = st.session_state.user
  if current_user["role"] == "admin":
    render_admin_dashboard()
  else:
    render_collector_dashboard()
