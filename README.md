# OIS Middle School PASS Dashboard

A Streamlit dashboard that turns a Testwise **PASS (Pupil Attitudes to Self and School)** Excel export into three practical views:

- **SLT:** school-level patterns, grade/homeroom variation, completion and intervention load. Student names are not shown.
- **Grade Level Leaders:** grade diagnosis, homeroom comparison, named student priorities and intervention planning.
- **Homeroom Teachers:** homeroom overview, check-in queue and individual student profile.

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

## Data privacy

PASS files contain sensitive pupil wellbeing/pastoral information.

- **Never commit a live PASS export to GitHub.** The `.gitignore` blocks common data file formats as an extra safeguard.
- Prefer a **private repository**.
- Deploy only on a school-approved platform with appropriate access controls and data-processing arrangements.
- The app does not deliberately write uploaded pupil data to disk, but the deployment host still processes the file in memory.
- Set an `APP_PASSWORD` in Streamlit secrets before any wider deployment.

Example `.streamlit/secrets.toml` (do **not** commit this file):

```toml
APP_PASSWORD = "use-a-strong-school-managed-password"
```

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
4. **Review after 3–4 weeks** using real evidence (attendance, work completion, behaviour, student voice), rather than waiting for the next PASS survey.
5. Re-administer PASS later in the year if that fits the school's assessment cycle; GL notes that many secondary schools use a second administration at least 12 weeks after the first.

## Official PASS references

- GL Assessment PASS overview: https://www.gl-assessment.co.uk/products/pass/
- PASS attitudinal factor definitions: https://support.gl-assessment.co.uk/knowledge-base/assessments/pass-support/general-information/attitudinal-factors
- Understanding PASS data and percentile bands: https://support.gl-assessment.co.uk/knowledge-base/assessments/pass-support/after-the-test/understanding-your-data
- PASS quick data guide: https://support.gl-assessment.co.uk/knowledge-base/assessments/pass-support/after-the-test/quick-data-guide
- PASS interventions overview: https://support.gl-assessment.co.uk/knowledge-base/assessments/pass-support/after-the-test/pass-interventions
