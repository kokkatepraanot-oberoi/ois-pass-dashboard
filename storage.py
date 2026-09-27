from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Optional
from uuid import uuid4

import pandas as pd
import streamlit as st

try:
    import gspread
    from google.oauth2.service_account import Credentials
except ImportError:  # handled cleanly in the UI
    gspread = None
    Credentials = None


# Default OIS PASS persistent intervention/review store.
# This Sheet is shared directly with the PASS dashboard service account.
DEFAULT_SPREADSHEET_ID = "1kP4Ehre5uuFbvriJhjqvuYyuHqN5xOOzxiqo8Ax__r0"
DEFAULT_WORKSHEET = "Records"

RECORD_HEADERS = [
    "Record ID",
    "Created at",
    "Updated at",
    "Student ID",
    "Student",
    "Grade",
    "Homeroom",
    "Role",
    "Record type",
    "PASS factor",
    "Factor percentile",
    "Why this is a concern",
    "Longitudinal status",
    "Concern waves",
    "Action agreed",
    "Owner name",
    "Owner email",
    "Review date",
    "Status",
    "Escalate to",
    "Brief evidence / outcome",
    "Scope",
    "Latest PASS wave",
    "Last editor email",
]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _storage_config() -> tuple[str, str]:
    config = st.secrets.get("pass_storage", {}) or {}
    spreadsheet_id = str(config.get("spreadsheet_id", DEFAULT_SPREADSHEET_ID)).strip()
    worksheet_name = str(config.get("worksheet", DEFAULT_WORKSHEET)).strip() or DEFAULT_WORKSHEET
    return spreadsheet_id, worksheet_name


def storage_configured() -> bool:
    spreadsheet_id, _ = _storage_config()
    return bool(spreadsheet_id) and bool(st.secrets.get("gcp_service_account"))


def storage_status() -> str:
    if gspread is None or Credentials is None:
        return "Google Sheets storage libraries are not installed."
    if not st.secrets.get("gcp_service_account"):
        return "Google service-account credentials are not configured in Streamlit secrets."
    spreadsheet_id, _ = _storage_config()
    if not spreadsheet_id:
        return "PASS intervention storage is not configured."
    return "Connected"


@st.cache_resource(show_spinner=False)
def _worksheet():
    if not storage_configured():
        raise RuntimeError(storage_status())
    if gspread is None or Credentials is None:
        raise RuntimeError(storage_status())

    service_info = dict(st.secrets["gcp_service_account"])
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_info(service_info, scopes=scopes)
    client = gspread.authorize(creds)
    spreadsheet_id, worksheet_name = _storage_config()
    spreadsheet = client.open_by_key(spreadsheet_id)
    return spreadsheet.worksheet(worksheet_name)


def load_records() -> pd.DataFrame:
    if not storage_configured():
        return pd.DataFrame(columns=RECORD_HEADERS)
    ws = _worksheet()
    values = ws.get_all_records(expected_headers=RECORD_HEADERS)
    return pd.DataFrame(values, columns=RECORD_HEADERS)


def save_new_record(record: Dict[str, object]) -> str:
    ws = _worksheet()
    record_id = str(record.get("Record ID") or uuid4())
    now = _now_iso()
    payload = {header: "" for header in RECORD_HEADERS}
    payload.update({k: "" if v is None else v for k, v in record.items() if k in payload})
    payload["Record ID"] = record_id
    payload["Created at"] = str(payload.get("Created at") or now)
    payload["Updated at"] = now
    row = [payload[h] for h in RECORD_HEADERS]
    ws.append_row(row, value_input_option="USER_ENTERED")
    return record_id


def update_record(record_id: str, updates: Dict[str, object]) -> None:
    ws = _worksheet()
    cell = ws.find(record_id, in_column=1)
    if cell is None:
        raise ValueError("Saved PASS action could not be found.")

    row_values = ws.row_values(cell.row)
    row_values += [""] * (len(RECORD_HEADERS) - len(row_values))
    current = dict(zip(RECORD_HEADERS, row_values[: len(RECORD_HEADERS)]))
    for key, value in updates.items():
        if key in current:
            current[key] = "" if value is None else value
    current["Updated at"] = _now_iso()
    ws.update(f"A{cell.row}:X{cell.row}", [[current[h] for h in RECORD_HEADERS]], value_input_option="USER_ENTERED")


def filtered_records(
    *,
    role: Optional[str] = None,
    scope: Optional[str] = None,
    student_id: Optional[str] = None,
) -> pd.DataFrame:
    df = load_records()
    if df.empty:
        return df
    if role:
        df = df[df["Role"].astype(str) == str(role)]
    if scope:
        df = df[df["Scope"].astype(str) == str(scope)]
    if student_id:
        df = df[df["Student ID"].astype(str) == str(student_id)]
    return df.sort_values("Updated at", ascending=False, na_position="last")
