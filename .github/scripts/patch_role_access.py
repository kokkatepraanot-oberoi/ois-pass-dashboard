from pathlib import Path

path = Path("app.py")
text = path.read_text(encoding="utf-8")

# Add the Google Sheet role registry import.
import_anchor = '''from drive_storage import (
    download_source_file,
    latest_source_file,
    save_source_file,
    source_storage_configured,
    source_storage_status,
)
'''
import_replacement = import_anchor + 'from role_access import resolve_role_access\n'
if 'from role_access import resolve_role_access' not in text:
    if import_anchor not in text:
        raise SystemExit("Could not find drive_storage import block")
    text = text.replace(import_anchor, import_replacement, 1)

# Replace the old Streamlit-Secrets/name-matching access resolver.
start_marker = '# Project owner / SLT administrator. Additional roles should be configured in\n'
end_marker = '\n\ndef apply_theme() -> None:\n'
start = text.find(start_marker)
end = text.find(end_marker, start)
if start == -1 or end == -1:
    raise SystemExit("Could not locate legacy role-access block")

new_block = '''# Role permissions are maintained in the protected PASS Role Access Google Sheet.\n\n\ndef logout_and_clear() -> None:\n    """Clear app identity state before ending the Streamlit OIDC session."""\n    for key in ("staff_name", "staff_email"):\n        st.session_state.pop(key, None)\n    st.logout()\n\n\ndef resolve_access() -> dict:\n    """Resolve exact email-based permissions from the PASS Role Access register."""\n    email = str(st.session_state.get("staff_email", "")).strip().casefold()\n    return resolve_role_access(email)\n'''
text = text[:start] + new_block + text[end:]

# Fail closed with a useful message if the protected role register cannot be read.
old_main = '''    apply_theme()\n    google_auth_gate()\n    access = resolve_access()\n    if not access["views"]:\n'''
new_main = '''    apply_theme()\n    google_auth_gate()\n    try:\n        access = resolve_access()\n    except Exception:\n        with st.sidebar:\n            st.error("The PASS role-access register is temporarily unavailable, so access has been stopped safely.")\n            st.caption("Please contact the dashboard administrator. No PASS data has been shown.")\n            st.button("Sign out / switch Google account", on_click=logout_and_clear, type="primary", use_container_width=True, key="role_register_logout")\n        st.stop()\n    if not access["views"]:\n'''
if old_main not in text:
    raise SystemExit("Could not find main access-resolution block")
text = text.replace(old_main, new_main, 1)

text = text.replace(
    'Views are now permission-controlled from the signed-in Google identity. HRT access is restricted to assigned homerooms; GL access can be restricted to assigned grades.',
    'Views are permission-controlled from the protected PASS Role Access register using the signed-in OIS email. HRTs see their assigned homeroom; GLs see their grade plus the HRT view for all homerooms in that grade.',
)

# Correct the directory spelling now that access is email-based.
text = text.replace('"6.1": "Shruti Uniyal"', '"6.1": "Shruti Unial"')

path.write_text(text, encoding="utf-8")
print("Google Sheet role access applied.")
