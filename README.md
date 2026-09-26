# OIS Middle School PASS Dashboard

A Streamlit dashboard that turns a Testwise **PASS (Pupil Attitudes to Self and School)** Excel export into five practical views:

- **SLT:** school-level patterns, grade/homeroom variation, completion and intervention load. Student names are not shown.
- **Grade Level Leaders:** grade diagnosis, homeroom comparison, named student priorities and intervention planning.
- **Homeroom Teachers:** homeroom overview, check-in queue and individual student profile.
- **Learning Support:** learning-barrier patterns across F2, F3, F4, F6, F7 and F9, with a review queue and access-to-learning responses.
- **Counsellors:** pastoral/relational patterns across F1, F3, F5, F7 and F8, with contextual review and conversation planning.

## Why this design

PASS is most useful when it moves from data to a clear pastoral response. GL Assessment describes PASS analysis at whole-school/cohort/individual level and uses percentile bands to highlight students and cohorts that may need support.

This app uses the published PASS percentile interpretation:

- 1st–5th percentile: low / immediate concern
- 6th–20th percentile: low-moderate
- 21st–30th percentile: moderate
- 31st–100th percentile: high

For day-to-day workflow, the app derives an **OIS attention status**:

- **Immediate review:** any factor <= 5th percentile
- **Targeted support:** no factor <=5, but any factor <=20
- **Monitor:** no factor <=20, but any factor is 21–30
- **Generally positive:** all nine factors >=31

This is **not an additional PASS score or diagnosis**. Staff should interpret the pattern across factors and triangulate it with attendance, attainment, behaviour, teacher observation and student voice.

## Nine PASS factors

1. Feelings about school
2. Perceived learning capability
3. Self-regard as a learner
4. Preparedness for learning
5. Attitudes to teachers
6. General work ethic
7. Confidence in learning
8. Attitudes to attendance
9. Response to curriculum demands

The intervention suggestions in this repository are **OIS-created practical responses**, not copies of GL Assessment's proprietary PASS Intervention bank.

## Specialist views

The **Learning Support** and **Counsellor** views use focused subsets of PASS factors to make review manageable. Their domain-specific "Immediate / Targeted / Monitor" labels are workflow aids only; they do not create a new PASS scale, identify SEND, diagnose mental-health needs, or constitute an automatic referral decision.

- Learning Support should triangulate PASS with attainment, work samples, teacher observation, language profile, screening and existing support plans.
- Counsellors should triangulate PASS with student voice, pastoral history, attendance, behaviour and safeguarding information.
- If a student conversation raises a safeguarding concern, staff should leave the PASS workflow and follow the school's safeguarding procedure.

**Important access note:** the current role selector changes what the dashboard displays; it is **not role-based authentication**. Anyone with the shared app password can switch between views. Before broad staff rollout, use school-approved authentication/authorisation if different teams should have different data access.

## Data privacy

PASS files contain sensitive pupil wellbeing/pastoral information.

- **Never commit a live PASS export to GitHub.** The `.gitignore` blocks common data file formats as an extra safeguard.
- Prefer a **private repository**.
- Deploy only on a school-approved platform with appropriate access controls and data-processing arrangements.
- The app does not deliberately write uploaded pupil data to disk, but the deployment host still processes the file in memory.
- Set an `APP_PASSWORD` in Streamlit secrets before any deployment. The app now **fails closed** if the secret is missing; there is no unlocked mode.
- Staff sign in with their name plus the shared school password. The staff name is stored only in the current Streamlit session.

In Streamlit Community Cloud open **Manage app → Settings → Secrets** and add:

```toml
APP_PASSWORD = "replace-with-a-strong-school-managed-password"
```

Do **not** commit `.streamlit/secrets.toml` to GitHub.

## 2026–27 Middle School homeroom teachers

The dashboard maps the PASS homeroom code to the HRT named on the `Homeroom` sheet of **Homeroom and Secondary Staff Data (A.Y. 2026- 2027)**. The separate `HRT` summary tab contains conflicting allocations, so the direct `Homeroom` sheet pairing is used for the dashboard.

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

The HRT view displays the teacher beside the homeroom code and automatically preselects the signed-in teacher's homeroom when the entered staff name exactly matches this mapping.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Then upload the Testwise PASS Excel export. The app looks for a sheet named `StudentData`; if it is not present, it uses the first sheet.

## Expected Testwise fields

Core fields:

- `Forename`
- `Surname`
- `Current Year`
- `Group`
- `PASS - Factor 1 - Percentile` through `PASS - Factor 9 - Percentile`

Other fields can be present and are retained. The SLT subgroup view only offers fields that contain meaningful variation.

## Recommended operating rhythm

1. **SLT:** identify 2–3 school/grade priorities, not dozens of actions.
2. **GL:** review Immediate students first, assign Targeted cases, and decide no more than two grade-wide responses.
3. **HRT:** complete student check-ins and use the individual factor profile to frame the conversation.
4. **Learning Support:** review multiple learning-related concerns against attainment and classroom evidence before assigning support.
5. **Counsellors:** use pastoral PASS patterns to prioritise contextual review and check-ins, not automatic counselling referrals.
6. **Review after 3–4 weeks** using real evidence (attendance, work completion, behaviour, student voice), rather than waiting for the next PASS survey.
7. Re-administer PASS later in the year if that fits the school's assessment cycle; GL notes that many secondary schools use a second administration at least 12 weeks after the first.

## Official PASS references

- GL Assessment PASS overview: https://www.gl-assessment.co.uk/products/pass/
- PASS attitudinal factor definitions: https://support.gl-assessment.co.uk/knowledge-base/assessments/pass-support/general-information/attitudinal-factors
- Understanding PASS data and percentile bands: https://support.gl-assessment.co.uk/knowledge-base/assessments/pass-support/after-the-test/understanding-your-data
- PASS quick data guide: https://support.gl-assessment.co.uk/knowledge-base/assessments/pass-support/after-the-test/quick-data-guide
- PASS interventions overview: https://support.gl-assessment.co.uk/knowledge-base/assessments/pass-support/after-the-test/pass-interventions
