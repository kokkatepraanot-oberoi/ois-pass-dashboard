from __future__ import annotations

import re
from typing import Dict, List

import streamlit as st

try:
    import gspread
    from google.oauth2.service_account import Credentials
except ImportError:  # handled cleanly by the caller
    gspread = None
    Credentials = None


DEFAULT_ROLE_SPREADSHEET_ID = "12nxD-6wpi3KjdQSUqCxVW0kX4fM0tU9jgtPGN27U1DY"
DEFAULT_WORKSHEET = "Access"
ROLE_HEADERS = ["Name", "Email", "Role", "Scope", "Active", "Notes"]
ALL_VIEWS = ["SLT", "Grade Level Leader", "Homeroom Teacher", "Learning Support", "Counsellor"]

# Break-glass access only if the role register itself cannot be reached.
# Normal permissions come from the PASS Role Access Google Sheet.
BREAK_GLASS_ADMINS = {
    "praanot.kokkate@oberoi-is.org",
    "roma.bhargava@oberoi-is.org",
}


def _role_config() -> tuple[str, str]:
    config = st.secrets.get("pass_roles", {}) or {}
    spreadsheet_id = str(config.get("spreadsheet_id", DEFAULT_ROLE_SPREADSHEET_ID)).strip()
    worksheet = str(config.get("worksheet", DEFAULT_WORKSHEET)).strip() or DEFAULT_WORKSHEET
    return spreadsheet_id, worksheet


def _is_active(value: object) -> bool:
    return str(value or "").strip().casefold() in {"yes", "y", "true", "1", "active"}


def _normalise_role(value: object) -> str:
    return " ".join(str(value or "").strip().casefold().split())


def _normalise_email(value: object) -> str:
    return str(value or "").strip().casefold()


def _google_client():
    if gspread is None or Credentials is None:
        raise RuntimeError("Google Sheets role-access libraries are not installed.")
    if not st.secrets.get("gcp_service_account"):
        raise RuntimeError("Google service-account credentials are not configured.")

    info = dict(st.secrets["gcp_service_account"])
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/drive.readonly",
    ]
    creds = Credentials.from_service_account_info(info, scopes=scopes)
    return gspread.authorize(creds)


@st.cache_data(ttl=60, show_spinner=False)
def load_role_rows() -> List[Dict[str, str]]:
    """Read the active role register. Cache briefly to avoid an API call on every widget rerun."""
    spreadsheet_id, worksheet_name = _role_config()
    client = _google_client()
    ws = client.open_by_key(spreadsheet_id).worksheet(worksheet_name)
    rows = ws.get_all_records(expected_headers=ROLE_HEADERS)

    cleaned: List[Dict[str, str]] = []
    for row in rows:
        item = {header: str(row.get(header, "") or "").strip() for header in ROLE_HEADERS}
        if not item["Email"] or not _is_active(item["Active"]):
            continue
        item["Email"] = _normalise_email(item["Email"])
        cleaned.append(item)
    return cleaned


def _grade_number(scope: str) -> str:
    match = re.search(r"\b([678])\b", str(scope or ""))
    return match.group(1) if match else ""


def resolve_role_access(email: str) -> Dict[str, object]:
    """Resolve exact email-based permissions from the PASS Role Access Sheet.

    A Grade Level Leader receives both the GL view and the HRT view for every
    active homeroom in their assigned grade. Staff with multiple rows receive
    the union of those roles (for example, Vanita can be HRT + Learning Support).
    """
    email = _normalise_email(email)
    try:
        rows = load_role_rows()
    except Exception:
        if email in BREAK_GLASS_ADMINS:
            return {
                "views": ALL_VIEWS.copy(),
                "grades": None,
                "homerooms": None,
                "is_admin": True,
                "role_source": "break-glass admin",
                "role_register_error": True,
            }
        raise

    mine = [row for row in rows if row["Email"] == email]
    if not mine:
        return {
            "views": [],
            "grades": None,
            "homerooms": None,
            "is_admin": False,
            "role_source": "PASS Role Access",
            "role_register_error": False,
        }

    roles = {_normalise_role(row["Role"]) for row in mine}
    if "admin" in roles or "slt" in roles:
        return {
            "views": ALL_VIEWS.copy(),
            "grades": None,
            "homerooms": None,
            "is_admin": True,
            "role_source": "PASS Role Access",
            "role_register_error": False,
        }

    views: List[str] = []
    grades: List[str] = []
    homerooms: List[str] = []

    if "learning support" in roles:
        views.append("Learning Support")
    if "counsellor" in roles or "counselor" in roles:
        views.append("Counsellor")

    for row in mine:
        role = _normalise_role(row["Role"])
        scope = str(row["Scope"] or "").strip()
        if role in {"grade level leader", "gl"} and scope:
            grades.append(scope)
        elif role in {"homeroom teacher", "hrt"} and scope:
            homerooms.append(scope)

    if grades:
        views.append("Grade Level Leader")
        views.append("Homeroom Teacher")

        # GLs see the HRT view for every active homeroom in their own grade(s).
        grade_numbers = {_grade_number(grade) for grade in grades}
        grade_numbers.discard("")
        for row in rows:
            if _normalise_role(row["Role"]) not in {"homeroom teacher", "hrt"}:
                continue
            scope = str(row["Scope"] or "").strip()
            if any(scope.startswith(f"{grade}.") for grade in grade_numbers):
                homerooms.append(scope)

    if homerooms:
        views.append("Homeroom Teacher")

    views = list(dict.fromkeys(views))
    grades = list(dict.fromkeys(grades))
    homerooms = list(dict.fromkeys(homerooms))

    return {
        "views": views,
        "grades": grades or None,
        "homerooms": homerooms or None,
        "is_admin": False,
        "role_source": "PASS Role Access",
        "role_register_error": False,
    }
