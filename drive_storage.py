from __future__ import annotations

import hashlib
import io
from typing import Dict, List, Optional

import streamlit as st
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload


# My Drive folder used for the dashboard's protected PASS source exports.
DEFAULT_SOURCE_FOLDER_ID = "1OiLcZNjTEY-NkXhYtjUxolfTu8fJfcpE"
XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
DRIVE_SCOPE = "https://www.googleapis.com/auth/drive"


def source_storage_configured() -> bool:
    return bool(st.secrets.get("gcp_service_account"))


def source_storage_status() -> str:
    if not st.secrets.get("gcp_service_account"):
        return "Google Drive source storage is waiting for the service-account credentials in Streamlit Secrets."
    return "Google Drive credentials are configured."


def source_folder_id() -> str:
    config = st.secrets.get("pass_drive", {})
    return str(config.get("folder_id", DEFAULT_SOURCE_FOLDER_ID)).strip()


@st.cache_resource(show_spinner=False)
def _drive_service():
    if not source_storage_configured():
        raise RuntimeError(source_storage_status())

    info = dict(st.secrets["gcp_service_account"])
    required = {"type", "project_id", "private_key", "client_email", "token_uri"}
    missing = sorted(required - set(info))
    if missing:
        raise RuntimeError(
            "Google service-account configuration is incomplete. Missing: " + ", ".join(missing)
        )

    creds = Credentials.from_service_account_info(info, scopes=[DRIVE_SCOPE])
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def _drive_error(exc: Exception) -> RuntimeError:
    if isinstance(exc, HttpError):
        status = getattr(exc.resp, "status", None)
        if status == 403:
            return RuntimeError(
                "Google Drive rejected the service-account request (403). Confirm that the Google Drive API is enabled in the 'ois-dashboards' Google Cloud project, the current service-account key is in Streamlit Secrets, and the PASS Dashboard Source Data folder is shared with pass-dashboard@ois-dashboards.iam.gserviceaccount.com as Editor."
            )
        if status == 404:
            return RuntimeError(
                "The configured PASS source folder/file could not be found by the service account. Check the folder ID and sharing permissions."
            )
    return RuntimeError(f"Google Drive source storage failed: {exc}")


def verify_source_folder() -> Dict[str, object]:
    """Verify the service account can see the configured source folder."""
    try:
        service = _drive_service()
        return (
            service.files()
            .get(fileId=source_folder_id(), fields="id,name,mimeType,webViewLink")
            .execute()
        )
    except Exception as exc:
        raise _drive_error(exc) from exc


def list_source_files(limit: int = 25) -> List[Dict[str, object]]:
    try:
        service = _drive_service()
        folder_id = source_folder_id()
        result = (
            service.files()
            .list(
                q=f"'{folder_id}' in parents and trashed = false",
                orderBy="modifiedTime desc",
                pageSize=max(1, min(int(limit), 100)),
                fields="files(id,name,size,createdTime,modifiedTime,mimeType,webViewLink,appProperties)",
            )
            .execute()
        )
        return result.get("files", [])
    except Exception as exc:
        raise _drive_error(exc) from exc


def latest_source_file() -> Optional[Dict[str, object]]:
    files = [
        f
        for f in list_source_files()
        if f.get("mimeType") == XLSX_MIME or str(f.get("name", "")).lower().endswith(".xlsx")
    ]
    return files[0] if files else None


def download_source_file(file_id: str) -> bytes:
    try:
        service = _drive_service()
        request = service.files().get_media(fileId=file_id)
        buffer = io.BytesIO()
        downloader = MediaIoBaseDownload(buffer, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        return buffer.getvalue()
    except Exception as exc:
        raise _drive_error(exc) from exc


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

    metadata = {
        "name": file_name,
        "parents": [source_folder_id()],
        "mimeType": XLSX_MIME,
        "appProperties": {
            "sha256": file_hash,
            "uploaded_by": str(uploaded_by)[:124],
            "row_count": str(int(row_count)),
            "waves": " | ".join(str(w) for w in waves)[:124],
            "source": "ois-pass-dashboard",
        },
    }

    try:
        service = _drive_service()
        media = MediaIoBaseUpload(io.BytesIO(file_bytes), mimetype=XLSX_MIME, resumable=False)
        return (
            service.files()
            .create(
                body=metadata,
                media_body=media,
                fields="id,name,size,createdTime,modifiedTime,mimeType,webViewLink,appProperties",
            )
            .execute()
        )
    except Exception as exc:
        raise _drive_error(exc) from exc
