# OIS Middle School PASS Dashboard

A Streamlit dashboard for turning Testwise **PASS (Pupil Attitudes to Self and School)** exports into practical leadership, pastoral and intervention workflows.

The app has five permission-controlled views:

- **SLT:** school climate, longitudinal patterns, grade/homeroom variation and intervention priorities.
- **Grade Level Leaders:** grade diagnosis, student journeys, homeroom comparison, named review queues and intervention planning.
- **Homeroom Teachers:** own-homeroom picture, check-in queue, student journey and first-step interventions.
- **Learning Support:** learning-barrier patterns across F2, F3, F4, F6, F7 and F9.
- **Counsellors:** pastoral/relational patterns across F1, F3, F5, F7 and F8.

## PASS interpretation used

Published PASS percentile bands are used as the base:

- **1st–5th percentile:** low / immediate concern
- **6th–20th percentile:** low-moderate
- **21st–30th percentile:** moderate
- **31st–100th percentile:** high

The dashboard derives an OIS workflow status:

- **Immediate review:** any factor <=5
- **Targeted support:** no factor <=5, but any factor <=20
- **Monitor:** no factor <=20, but any factor is 21–30
- **Generally positive:** all nine factors >=31

This is **not an additional PASS score or diagnosis**. Results must be triangulated with attendance, attainment, behaviour, teacher observation and student voice.

## Phase 1 — longitudinal analysis

A multi-wave Testwise export unlocks analysis over time. Late completions close to the main administration are grouped into the same survey wave so they do not create artificial extra waves.

The dashboard can now show:

- school, grade and specialist factor trends across survey waves
- latest-wave vs previous-wave movement
- current student profiles alongside historical journeys
- **New concern**
- **Persistent concern**
- **Chronic concern**
- **Recovered**
- **Watch deterioration**
- **Stable positive**

Historical grade and homeroom labels in Testwise exports may reflect the student's **current** placement. For that reason, older results are presented as a **current cohort/student journey**, not as proof of the historical composition of a particular grade or homeroom.

## Phase 2 — action workflow

The app also includes:

- Google Workspace login restricted to `@oberoi-is.org`
- role-based permissions
- HRT restriction to assigned homeroom(s)
- GL restriction to assigned grade(s)
- Learning Support and Counsellor specialist permissions
- intervention trackers
- HRT/GL action and review logs
- CSV downloads
- multi-sheet Excel analysis exports
- safeguarding and interpretation guardrails

The trackers/logs are currently **session-based**. Staff should download the CSV before leaving the session and use the school's approved systems for any detailed pastoral, counselling or safeguarding record.

## Authentication and roles

Google OIDC authentication uses Streamlit's `st.login()`, `st.user` and `st.logout()` workflow.

The project owner account is retained as the initial dashboard administrator. All other roles should be configured in **Streamlit → Manage app → Settings → Secrets**. See `ROLE_CONFIGURATION.md` for the exact format.

An authenticated OIS account with **no assigned role receives no PASS data**.

For HRTs, if no explicit email mapping exists, the app can use a safe exact match between the Google display name and the 2026–27 HRT list built into the app.

## Google OIDC secrets

Keep these only in Streamlit Secrets, never in GitHub:

```toml
[auth]
redirect_uri = "https://ois-pass.streamlit.app/oauth2callback"
cookie_secret = "YOUR_RANDOM_SECRET"
client_id = "YOUR_GOOGLE_CLIENT_ID"
client_secret = "YOUR_GOOGLE_CLIENT_SECRET"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
```

`Authlib` and `httpx` are included in `requirements.txt` because Streamlit's Google authentication flow requires them in the deployed environment.

## Data privacy

PASS files contain sensitive pupil pastoral/wellbeing information.

- **Never commit a live PASS export to GitHub.**
- The repository should be **Private** before wider school rollout.
- Deploy only on a school-approved platform with appropriate access controls and data-processing arrangements.
- Uploaded pupil data is processed in the current Streamlit session; it is not deliberately written to the repository.
- Detailed counselling and safeguarding notes must remain in the school's approved record systems.

## 2026–27 Middle School homeroom teachers

The dashboard uses the direct homeroom allocation from the `Homeroom` sheet in **Homeroom and Secondary Staff Data (A.Y. 2026- 2027)**.

| Homeroom | HRT |
|---|---|
| 6.1 | Shruti Uniyal |
| 6.2 | Jigna Doshi |
| 6.3 | Neha Kapadia |
| 6.4 | Sneha Sundrani |
| 6.5 | Debduti Ray |
| 6.6 | Ursula Sanghvi |
| 6.7 | Prathamesh Cheulkar |
| 6.8 | Ramprasad Iyengar |
| 7.1 | Pradeep Singh |
| 7.2 | Aashana Musle |
| 7.3 | Manasi Bhingarde |
| 7.4 | Pallavi Rajguru |
| 7.5 | Vaishnavi Bapardekar |
| 7.6 | Roshan Chavan |
| 7.7 | Antara Roy |
| 7.8 | Rohit Kumar |
| 8.1 | Vanita Amin |
| 8.2 | Swapnil Shetty |
| 8.3 | Lata Dalvi |
| 8.4 | Mamta Pasi |
| 8.5 | Ashwin Subramanian |
| 8.6 | Dhanisha Benoy |
| 8.7 | Neha Basak |

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

The app looks for a sheet named `StudentData`; if it is not present, it uses the first sheet.

Core Testwise fields are:

- `Forename`
- `Surname`
- `Current Year`
- `Group`
- `PASS - Date of Survey` for longitudinal analysis
- `TW Unique ID` for reliable student matching over time
- `PASS - Factor 1 - Percentile` through `PASS - Factor 9 - Percentile`

## Recommended operating rhythm

1. **SLT:** select 2–3 systemic priorities, not a long list of actions.
2. **GL:** review new/persistent/chronic concerns, assign ownership and choose no more than two grade-wide responses.
3. **HRT:** complete targeted student check-ins using the factor profile and journey as context.
4. **Learning Support/Counsellors:** use specialist queues for contextual review, not automatic referral.
5. **Review after 3–4 weeks** using attendance, work completion, behaviour, attainment and student voice.
6. Use the next PASS administration to review whether concerns have improved, persisted or newly emerged.

## Official PASS references

- GL Assessment PASS overview: https://www.gl-assessment.co.uk/products/pass/
- PASS factor definitions: https://support.gl-assessment.co.uk/knowledge-base/assessments/pass-support/general-information/attitudinal-factors
- Understanding PASS data: https://support.gl-assessment.co.uk/knowledge-base/assessments/pass-support/after-the-test/understanding-your-data
- PASS quick data guide: https://support.gl-assessment.co.uk/knowledge-base/assessments/pass-support/after-the-test/quick-data-guide
- PASS interventions: https://support.gl-assessment.co.uk/knowledge-base/assessments/pass-support/after-the-test/pass-interventions
