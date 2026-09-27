from pathlib import Path

path = Path("app.py")
text = path.read_text(encoding="utf-8")

anchor = 'ALL_VIEWS = ["SLT", "Grade Level Leader", "Homeroom Teacher", "Learning Support", "Counsellor"]\n\n\n'
helper = '''ALL_VIEWS = ["SLT", "Grade Level Leader", "Homeroom Teacher", "Learning Support", "Counsellor"]\n\n\ndef logout_and_clear() -> None:\n    """Clear app identity state before ending the Streamlit OIDC session."""\n    for key in ("staff_name", "staff_email"):\n        st.session_state.pop(key, None)\n    st.logout()\n\n\n'''
if 'def logout_and_clear()' not in text:
    if anchor not in text:
        raise SystemExit("Could not find ALL_VIEWS anchor")
    text = text.replace(anchor, helper, 1)

replacements = [
    (
        'st.button("Sign out", on_click=st.logout)',
        'st.button("Sign out", on_click=logout_and_clear)',
    ),
    (
        'st.button("Sign out and use school account", on_click=st.logout, type="primary")',
        'st.button("Sign out and use school account", on_click=logout_and_clear, type="primary")',
    ),
    (
        'st.button("Log out", on_click=st.logout, use_container_width=True)',
        'st.button("Log out / switch account", on_click=logout_and_clear, use_container_width=True)',
    ),
]
for old, new in replacements:
    text = text.replace(old, new)

old_denied = '''    if not access["views"]:\n        with st.sidebar:\n            st.error("Your Google account is authenticated, but no PASS dashboard role has been assigned to it.")\n            st.caption("Ask the dashboard administrator to add your school email to the role configuration.")\n        st.stop()\n'''
new_denied = '''    if not access["views"]:\n        with st.sidebar:\n            st.error("Your Google account is authenticated, but no PASS dashboard role has been assigned to it.")\n            current_email = str(st.session_state.get("staff_email", "")).strip()\n            if current_email:\n                st.caption(f"Signed in as **{current_email}**")\n            st.button(\n                "Sign out / switch Google account",\n                on_click=logout_and_clear,\n                type="primary",\n                use_container_width=True,\n                key="no_role_logout",\n            )\n            st.caption("Ask the dashboard administrator to add your school email to the role configuration if you should have access.")\n        st.stop()\n'''
if old_denied in text:
    text = text.replace(old_denied, new_denied, 1)
elif 'key="no_role_logout"' not in text:
    raise SystemExit("Could not find no-role access block")

if 'on_click=st.logout' in text:
    raise SystemExit("A direct st.logout callback remains in app.py")
if 'key="no_role_logout"' not in text:
    raise SystemExit("No-role switch-account button was not added")

path.write_text(text, encoding="utf-8")
print("Logout/account-switch flow updated.")
