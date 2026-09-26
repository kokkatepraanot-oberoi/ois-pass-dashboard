# PASS dashboard role configuration

Google Workspace authentication confirms identity. Role permissions are then resolved inside the app.

Praanot's school account is retained as the initial dashboard administrator. Additional access should be added in **Streamlit → Manage app → Settings → Secrets**, never committed to GitHub.

Example:

```toml
[auth]
redirect_uri = "https://ois-pass.streamlit.app/oauth2callback"
cookie_secret = "..."
client_id = "..."
client_secret = "..."
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"

[roles]
admin = ["another.admin@oberoi-is.org"]
slt = ["secondary.leader@oberoi-is.org"]
learning_support = ["learning.support@oberoi-is.org"]
counsellor = ["counsellor@oberoi-is.org"]

[roles.grade_leaders]
"grade6.leader@oberoi-is.org" = ["Year 6"]
"grade7.leader@oberoi-is.org" = ["Year 7"]
"grade8.leader@oberoi-is.org" = ["Year 8"]

[roles.homerooms]
"teacher@oberoi-is.org" = ["6.1"]
```

## HRT convenience mapping

If an HRT email is not explicitly listed under `[roles.homerooms]`, the app attempts a safe exact-name match between the verified Google display name and the 2026–27 HRT mapping built into the app. If there is no match, the user gets no PASS access until configured.

## Access behaviour

- **SLT/admin:** full dashboard access.
- **Grade Level Leader:** only assigned grade(s).
- **Homeroom Teacher:** only assigned homeroom(s).
- **Learning Support:** specialist Learning Support view.
- **Counsellor:** specialist Counsellor view.
- **Authenticated OIS account with no role:** no PASS data is shown.
