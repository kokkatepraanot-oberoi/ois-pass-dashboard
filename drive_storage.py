from __future__ import annotations

import hashlib
import io
import time
from typing import Dict, List, Optional

import streamlit as st
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload

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


def _drive_service():
    """Build a fresh Drive client per operation so stale sockets are never reused."""
    if not source_storage_configured():
        raise RuntimeError(source_storage_status())
    info = dict(st.secrets["gcp_service_account"])
    required = {"type", "project_id", "private_key", "client_email", "token_uri"}
    missing = sorted(required - set(info))
    if missing:
        raise RuntimeError("Google service-account configuration is incomplete. Missing: " + ", ".join(missing))
    creds = Credentials.from_service_account_info(info, scopes=[DRIVE_SCOPE])
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def _is_transient_transport_error(exc: Exception) -> bool:
    if isinstance(exc, (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, TimeoutError)):
        return True
    if isinstance(exc, OSError) and getattr(exc, "errno", None) in {32, 54, 104}:
        return True
    text = str(exc).lower()
    return any(marker in text for marker in (
        "broken pipe", "connection reset", "connection aborted",
        "remote end closed connection", "temporarily unavailable",
    ))


def _execute_with_retry(request_builder):
    last_exc = None
    for attempt in range(2):
        try:
            return request_builder(_drive_service()).execute()
        except Exception as exc:
            last_exc = exc
            if attempt == 0 and _is_transient_transport_error(exc):
                time.sleep(0.2)
                continue
            raise
    raise last_exc


def _drive_error(exc: Exception) -> RuntimeError:
    if isinstance(exc, HttpError):
        status = getattr(exc.resp, "status", None)
        if status == 403:
            return RuntimeError("Google Drive rejected the service-account request (403). Check Drive API enablement, the current service-account key, and folder sharing.")
        if status == 404:
            return RuntimeError("The configured PASS source folder/file could not be found by the service account. Check the folder ID and sharing permissions.")
    if _is_transient_transport_error(exc):
        return RuntimeError("Google Drive had a temporary connection interruption. Refresh the dashboard; the saved PASS data has not been lost.")
    return RuntimeError(f"Google Drive source storage failed: {exc}")


def verify_source_folder() -> Dict[str, object]:
    try:
        return _execute_with_retry(lambda service: service.files().get(fileId=source_folder_id(), fields="id,name,mimeType,webViewLink"))
    except Exception as exc:
        raise _drive_error(exc) from exc


def list_source_files(limit: int = 25) -> List[Dict[str, object]]:
    try:
        folder_id = source_folder_id()
        result = _execute_with_retry(lambda service: service.files().list(
            q=f"'{folder_id}' in parents and trashed = false",
            orderBy="modifiedTime desc",
            pageSize=max(1, min(int(limit), 100)),
            fields="files(id,name,size,createdTime,modifiedTime,mimeType,webViewLink,appProperties)",
        ))
        return result.get("files", [])
    except Exception as exc:
        raise _drive_error(exc) from exc


def latest_source_file() -> Optional[Dict[str, object]]:
    files = [f for f in list_source_files() if f.get("mimeType") == XLSX_MIME or str(f.get("name", "")).lower().endswith(".xlsx")]
    return files[0] if files else None


def download_source_file(file_id: str) -> bytes:
    last_exc = None
    for attempt in range(2):
        try:
            request = _drive_service().files().get_media(fileId=file_id)
            buffer = io.BytesIO()
            downloader = MediaIoBaseDownload(buffer, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
            return buffer.getvalue()
        except Exception as exc:
            last_exc = exc
            if attempt == 0 and _is_transient_transport_error(exc):
                time.sleep(0.2)
                continue
            raise _drive_error(exc) from exc
    raise _drive_error(last_exc)


def _existing_by_hash(file_hash: str) -> Optional[Dict[str, object]]:
    for item in list_source_files(limit=100):
        if str((item.get("appProperties") or {}).get("sha256", "")) == file_hash:
            return item
    return None


def save_source_file(file_bytes: bytes, file_name: str, *, uploaded_by: str, row_count: int, waves: List[str]) -> Dict[str, object]:
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
    last_exc = None
    for attempt in range(2):
        try:
            service = _drive_service()
            media = MediaIoBaseUpload(io.BytesIO(file_bytes), mimetype=XLSX_MIME, resumable=False)
            return service.files().create(
                body=metadata,
                media_body=media,
                fields="id,name,size,createdTime,modifiedTime,mimeType,webViewLink,appProperties",
            ).execute()
        except Exception as exc:
            last_exc = exc
            if attempt == 0 and _is_transient_transport_error(exc):
                time.sleep(0.2)
                continue
            raise _drive_error(exc) from exc
    raise _drive_error(last_exc)
