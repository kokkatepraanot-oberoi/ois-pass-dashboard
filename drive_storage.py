from __future__ import annotations

import hashlib
import json
from typing import Dict, List, Optional
from uuid import uuid4

import streamlit as st
from google.auth.transport.requests import AuthorizedSession
from google.oauth2.service_account import Credentials


# Shared Drive folder created for the dashboard's source PASS exports.
DEFAULT_SOURCE_FOLDER_ID = "1clhramwdpF-GAIdunuJwNJRv8Vg6JuAG"
XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def source_storage_configured() -> bool:
    return bool(st.secrets.get("gcp_service_account"))


def source_storage_status() -> str:
    if not st.secrets.get("gcp_service_account"):
        return "Google Drive source storage is waiting for the service-account credentials in Streamlit Secrets."
    return "Connected"


def source_folder_id() -> str:
    config = st.secrets.get("pass_drive", {})
    return str(config.get("folder_id", DEFAULT_SOURCE_FOLDER_ID))


def _session() -> AuthorizedSession:
    if not source_storage_configured():
        raise RuntimeError(source_storage_status())
    info = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(
        info,
        scopes=["https://www.googleapis.com/auth/drive"],
    )
    return AuthorizedSession(creds)


def list_source_files(limit: int = 25) -> List[Dict[str, object]]:
    session = _session()
    folder_id = source_folder_id()
    params = {
        "q": f"'{folder_id}' in parents and trashed = false",
        "orderBy": "modifiedTime desc",
        "pageSize": max(1, min(int(limit), 100)),
        "supportsAllDrives": "true",
        "includeItemsFromAllDrives": "true",
        "fields": "files(id,name,size,createdTime,modifiedTime,mimeType,webViewLink,appProperties)",
    }
    response = session.get("https://www.googleapis.com/drive/v3/files", params=params, timeout=30)
    response.raise_for_status()
    return response.json().get("files", [])


def latest_source_file() -> Optional[Dict[str, object]]:
    files = [f for f in list_source_files() if f.get("mimeType") == XLSX_MIME or str(f.get("name", "")).lower().endswith(".xlsx")]
    return files[0] if files else None


def download_source_file(file_id: str) -> bytes:
    session = _session()
    response = session.get(
        f"https://www.googleapis.com/drive/v3/files/{file_id}",
        params={"alt": "media", "supportsAllDrives": "true"},
        timeout=60,
    )
    response.raise_for_status()
    return response.content


def _existing_by_hash(file_hash: str) -> Optional[Dict[str, object]]:
    for item in list_source_files(limit=100):
        if str((item.get("appProperties") or {}).get("sha256", "")) == file_hash:
            return item
    return None


def save_source_file(
    file_bytes: bytes,
    file_name: str,
    *,
    uploaded_by: str,
    row_count: int,
    waves: List[str],
) -> Dict[str, object]:
    file_hash = hashlib.sha256(file_bytes).hexdigest()
    existing = _existing_by_hash(file_hash)
    if existing:
        return existing

    session = _session()
    folder_id = source_folder_id()
    boundary = f"pass-{uuid4().hex}"
    metadata = {
        "name": file_name,
        "parents": [folder_id],
        "mimeType": XLSX_MIME,
        "appProperties": {
            "sha256": file_hash,
            "uploaded_by": str(uploaded_by)[:124],
            "row_count": str(int(row_count)),
            "waves": " | ".join(str(w) for w in waves)[:124],
            "source": "ois-pass-dashboard",
        },
    }
    prefix = (
        f"--{boundary}\r\n"
        "Content-Type: application/json; charset=UTF-8\r\n\r\n"
        f"{json.dumps(metadata)}\r\n"
        f"--{boundary}\r\n"
        f"Content-Type: {XLSX_MIME}\r\n\r\n"
    ).encode("utf-8")
    suffix = f"\r\n--{boundary}--\r\n".encode("utf-8")
    body = prefix + file_bytes + suffix
    response = session.post(
        "https://www.googleapis.com/upload/drive/v3/files",
        params={
            "uploadType": "multipart",
            "supportsAllDrives": "true",
            "fields": "id,name,size,createdTime,modifiedTime,mimeType,webViewLink,appProperties",
        },
        data=body,
        headers={"Content-Type": f"multipart/related; boundary={boundary}"},
        timeout=90,
    )
    response.raise_for_status()
    return response.json()
