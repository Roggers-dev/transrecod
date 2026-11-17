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
                recovery_pref TEXT DEFAULT 'Email',
                subscription_status TEXT DEFAULT 'Active',
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

    # Automatically insert a default admin account if none exists
    res = conn.execute(
        sqlalchemy.text("SELECT COUNT(*) FROM users WHERE role = 'admin'")
    ).fetchone()
    if res[0] == 0:
      conn.execute(
          sqlalchemy.text("""
                INSERT INTO users (full_name, phone, email, password, role, status, subscription_status)
                VALUES ('System Admin', 'admin', 'admin@susuflow.com', 'admin123', 'admin', 'Active', 'Active')
                ON CONFLICT (phone) DO NOTHING;
            """)
      )
