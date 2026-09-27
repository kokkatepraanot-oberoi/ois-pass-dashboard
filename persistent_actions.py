from __future__ import annotations

from typing import List

import pandas as pd
import streamlit as st

from specialist_guidance import factor_label
from storage import filtered_records, save_new_record, storage_configured, storage_status, update_record


ADMIN_EMAIL = "praanot.kokkate@oberoi-is.org"


def _show_storage_connection_error() -> None:
    staff_email = str(st.session_state.get("staff_email", "")).strip().lower()
    if staff_email == ADMIN_EMAIL:
        st.error(
            "The PASS intervention store cannot be reached. The service account is configured, but Google Sheets denied access. "
            "Check that the Google Sheets API is enabled for the 'ois-dashboards' Google Cloud project and that "
            "pass-dashboard@ois-dashboards.iam.gserviceaccount.com has Editor access to the OIS PASS Intervention & Review Store."
        )
    else:
        st.info(
            "Saved intervention / review records are temporarily unavailable. Your PASS dashboard data is unaffected. "
            "The dashboard administrator has been asked to restore the storage connection."
        )


def render_action_manager(
    seed_df: pd.DataFrame,
    role_name: str,
    scope_label: str,
    key_prefix: str,
    schema,
    factors: List[int] | None = None,
    latest_wave: str = "",
) -> None:
    st.markdown("### Saved intervention / review records")
    if not storage_configured():
        st.warning(
            "Persistent storage is not connected yet. An administrator must add the Google service-account credentials "
            "to Streamlit Secrets. " + storage_status()
        )
        return

    try:
        saved = filtered_records(role=role_name, scope=scope_label)
    except Exception:
        _show_storage_connection_error()
        return

    if not saved.empty:
        cols = ["Updated at", "Student", "Record type", "PASS factor", "Action agreed", "Owner name", "Review date", "Status", "Escalate to"]
        st.dataframe(saved[[c for c in cols if c in saved.columns]], hide_index=True, use_container_width=True)
    else:
        st.caption("No saved records yet for this role/scope.")

    working = seed_df.copy() if seed_df is not None else pd.DataFrame()
    student_options = ["Cohort / no individual student"]
    if not working.empty and "Student" in working.columns:
        student_options += working["Student"].dropna().astype(str).drop_duplicates().sort_values().tolist()
    selected_student = st.selectbox("Student / cohort", student_options, key=f"persist_student_{key_prefix}")

    selected_row = None
    if selected_student != "Cohort / no individual student" and not working.empty:
        matches = working[working["Student"].astype(str) == selected_student]
        if not matches.empty:
            selected_row = matches.iloc[0]

    factor_numbers = factors or list(schema.factor_cols.keys())
    factor_choice = st.selectbox(
        "PASS factor / focus",
        [0, *factor_numbers],
        format_func=lambda n: "General / cohort action" if n == 0 else factor_label(n),
        key=f"persist_factor_{key_prefix}",
    )

    default_why = ""
    if selected_row is not None:
        if "Why this is a concern" in selected_row.index:
            default_why = str(selected_row.get("Why this is a concern", ""))
        elif "Attention" in selected_row.index:
            default_why = f"Current PASS status: {selected_row.get('Attention', '')}."

    with st.form(f"persist_form_{key_prefix}"):
        record_type = st.selectbox("Record type", ["Intervention", "Check-in", "Review", "Cohort action"])
        why = st.text_area(
            "Why this is a concern / focus",
            value=default_why,
            help="Keep this factual and brief. Do not enter detailed counselling or safeguarding notes here.",
        )
        action = st.text_area("Action agreed", help="State exactly what will happen, who will do it and what evidence you expect to see.")
        owner = st.text_input("Owner", value="", placeholder="Enter the person responsible")
        review_date = st.date_input("Review date", value=None)
        status = st.selectbox("Status", ["Not started", "In progress", "Review due", "Complete"])
        escalate = st.selectbox("Escalate / involve", ["", "HRT", "GL", "Learning Support", "Counsellor", "Subject teacher", "SLT", "Safeguarding"])
        evidence = st.text_area(
            "Brief evidence / outcome",
            help="Short operational evidence only. Detailed case notes remain in the school's approved pastoral/counselling system.",
        )
        if st.form_submit_button("Save to OIS PASS store", type="primary"):
            student_id = ""
            grade = ""
            homeroom = ""
            longitudinal = ""
            concern_waves = ""
            if selected_row is not None:
                student_id = str(selected_row.get("Student ID", ""))
                grade = str(selected_row.get("Grade", ""))
                homeroom = str(selected_row.get("Homeroom", ""))
                longitudinal = str(selected_row.get("Longitudinal status", ""))
                concern_waves = str(selected_row.get("Repeated concern across survey waves", ""))

            try:
                save_new_record({
                    "Student ID": student_id,
                    "Student": "" if selected_student == "Cohort / no individual student" else selected_student,
                    "Grade": grade,
                    "Homeroom": homeroom,
                    "Role": role_name,
                    "Record type": record_type,
                    "PASS factor": "General / cohort action" if factor_choice == 0 else factor_label(factor_choice),
                    "Why this is a concern": why,
                    "Longitudinal status": longitudinal,
                    "Concern waves": concern_waves,
                    "Action agreed": action,
                    "Owner name": owner,
                    "Owner email": st.session_state.get("staff_email", ""),
                    "Review date": "" if review_date is None else str(review_date),
                    "Status": status,
                    "Escalate to": escalate,
                    "Brief evidence / outcome": evidence,
                    "Scope": scope_label,
                    "Latest PASS wave": latest_wave,
                    "Last editor email": st.session_state.get("staff_email", ""),
                })
            except Exception:
                _show_storage_connection_error()
            else:
                st.success("Saved to the OIS PASS intervention store.")
                st.rerun()

    if not saved.empty:
        with st.expander("Update an existing saved record"):
            record_map = {}
            labels = []
            for _, rec in saved.iterrows():
                label = f"{rec.get('Student') or 'Cohort'} | {rec.get('Record type')} | {rec.get('Updated at')} | {str(rec.get('Record ID'))[:8]}"
                labels.append(label)
                record_map[label] = rec
            chosen = st.selectbox("Saved record", labels, key=f"persist_edit_{key_prefix}")
            rec = record_map[chosen]
            status_options = ["Not started", "In progress", "Review due", "Complete"]
            escalation_options = ["", "HRT", "GL", "Learning Support", "Counsellor", "Subject teacher", "SLT", "Safeguarding"]
            with st.form(f"persist_update_form_{key_prefix}"):
                update_action = st.text_area("Action agreed", value=str(rec.get("Action agreed", "")))
                current_status = str(rec.get("Status", "Not started"))
                update_status = st.selectbox("Status", status_options, index=status_options.index(current_status) if current_status in status_options else 0)
                current_escalation = str(rec.get("Escalate to", ""))
                update_escalate = st.selectbox("Escalate / involve", escalation_options, index=escalation_options.index(current_escalation) if current_escalation in escalation_options else 0)
                update_evidence = st.text_area("Brief evidence / outcome", value=str(rec.get("Brief evidence / outcome", "")))
                if st.form_submit_button("Update saved record"):
                    try:
                        update_record(str(rec["Record ID"]), {
                            "Action agreed": update_action,
                            "Status": update_status,
                            "Escalate to": update_escalate,
                            "Brief evidence / outcome": update_evidence,
                            "Last editor email": st.session_state.get("staff_email", ""),
                        })
                    except Exception:
                        _show_storage_connection_error()
                    else:
                        st.success("Saved record updated.")
                        st.rerun()
