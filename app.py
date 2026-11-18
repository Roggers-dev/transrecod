# --- SECTION 5: EXPORT ENCRYPTED DATA (EXCEL/CSV) ---
  elif nav == "📥 Export Encrypted Data (Excel/CSV)":
    st.subheader("📥 Export Active Transaction Records")
    st.info(
        "Download your active workspace transaction records in encrypted or"
        " standard CSV/Excel format."
    )

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
          label="📥 Download Encrypted/Standard CSV File",
          data=csv_data,
          file_name="alufatanaah_transactions_export.csv",
          mime="text/csv",
      )
    else:
      st.info("No data available for export.")

  # --- SECTION 6: REPORT APP ISSUE / SUPPORT TICKETS ---
  elif nav == "🛠️ Report App Issue / Problem":
    st.subheader("🛠️ Report App Issues or Problems to Developer")
    st.info(
        "Use this channel to report any problems or challenges you are facing"
        " with the application."
    )

    with st.form("issue_form"):
      issue_msg = st.text_area(
          "Describe the issue or problem you are encountering:"
      )
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
          st.success(
              "Issue submitted successfully! Developer/Admin will review it."
          )
        else:
          st.warning("Please describe the issue.")

  # --- SECTION 7: ADMIN - MANAGER GOVERNANCE & QUOTAS ---
  elif nav == "🛡️ [Admin] Manager Governance & Quotas":
    if not is_admin:
      st.error("Unauthorized access.")
      return
    st.subheader("🛡️ Workspace Manager Governance & Audit Control")

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
            f" | Quota: `{row['client_quota']}` | Edit Override: "
            f"`{row['edit_override']}` | Note Override: `{row['note_override']}`"
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
            st.warning(f"Account {row['full_name']} frozen for audit.")
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
            st.success(f"Account {row['full_name']} restored.")
            st.rerun()

        if col2.button("Grant Edit Auth", key=f"edit_{row['id']}"):
          with engine.begin() as conn:
            conn.execute(
                sqlalchemy.text(
                    "UPDATE users SET edit_override = TRUE WHERE id = :id"
                ),
                {"id": row["id"]},
            )
          st.success(f"Edit authorization granted to {row['full_name']}.")
          st.rerun()

        if col3.button("Grant Note Auth", key=f"note_{row['id']}"):
          with engine.begin() as conn:
            conn.execute(
                sqlalchemy.text(
                    "UPDATE users SET note_override = TRUE WHERE id = :id"
                ),
                {"id": row["id"]},
            )
          st.success(f"Note editing authorization granted to {row['full_name']}.")
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
          st.success(f"Quota updated to {new_q} for {row['full_name']}.")
          st.rerun()
        st.markdown("---")
    else:
      st.info("No workspace managers registered.")

    st.subheader("📋 All Registered Clients Across All Workspaces")
    df_all_clients = pd.read_sql(
        sqlalchemy.text(
            "SELECT client_name, client_phone, manager_name, target_limit,"
            " date_registered FROM clients"
        ),
        engine,
    )
    if not df_all_clients.empty:
      st.dataframe(df_all_clients, use_container_width=True)
    else:
      st.info("No clients registered in the system yet.")

  # --- SECTION 8: ADMIN - SUPPORT TICKETS / ISSUES ---
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
    if not df_tickets.empty:
      st.dataframe(df_tickets, use_container_width=True)
    else:
      st.info("No issues reported by managers.")


# ---------------------------------------------------------
# MAIN APP ROUTER
# ---------------------------------------------------------
if not st.session_state.logged_in:
  render_auth()
else:
  render_dashboard()
