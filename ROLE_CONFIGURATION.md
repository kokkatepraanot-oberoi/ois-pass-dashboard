# PASS dashboard role configuration

Google Workspace authentication confirms identity. Role permissions are then resolved by exact OIS email address from the protected **PASS Role Access** Google Sheet.

The role register is stored in the same **PASS Dashboard Source Data** folder as the PASS source dataset and intervention store. It is shared with the PASS dashboard service account so the Streamlit app can read it securely.

## Role register

Google Sheet: **PASS Role Access**  
Spreadsheet ID: `12nxD-6wpi3KjdQSUqCxVW0kX4fM0tU9jgtPGN27U1DY`  
Worksheet: `Access`

Columns:

- `Name`
- `Email`
- `Role`
- `Scope`
- `Active`
- `Notes`

Use `Yes` in **Active** to grant access. Changing a row to `No` (or removing it) removes that assignment after the short access-cache period.

## Access behaviour

- **Admin:** all five dashboard views and the full Middle School dataset.
- **Grade Level Leader:** Grade Level Leader view for the assigned grade **plus the Homeroom Teacher view for every active homeroom in that grade**.
- **Homeroom Teacher:** Homeroom Teacher view for the assigned homeroom(s) only.
- **Learning Support:** Learning Support specialist view.
- **Counsellor:** Counsellor specialist view.
- **Multiple assignments:** permissions are combined. For example, a member of Learning Support who is also an HRT receives both views.
- **Authenticated OIS account with no active role row:** no PASS data is shown.

Role access is now email-based only. The previous Streamlit Secrets role lists and Google display-name HRT fallback are no longer used for normal access decisions.

## Administration

Praanot Kokkate and Roma Bhargava are the current administrators in the role register. They are also retained as break-glass administrators so the dashboard can still be accessed to diagnose a role-register connection failure.

Normal role changes should be made by editing **PASS Role Access**, not by changing application code or Streamlit Secrets.

The service account used by the dashboard must retain access to the role register and the Google Sheets API must remain enabled for the `ois-dashboards` Google Cloud project.
