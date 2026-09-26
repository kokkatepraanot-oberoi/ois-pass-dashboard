from __future__ import annotations

import io

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from pass_logic import (
    ATTENTION_ORDER,
    FACTOR_DESCRIPTIONS,
    FACTOR_NAMES,
    INTERVENTIONS,
    factor_actions_for_context,
    factor_summary,
    homeroom_summary,
    load_pass_excel,
    student_factor_profile,
    student_priority_table,
    attention_summary,
)


st.set_page_config(
    page_title="OIS Middle School PASS Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


ATTENTION_COLOURS = {
    "Immediate review": "#b42318",
    "Targeted support": "#e07800",
    "Monitor": "#b38b00",
    "Generally positive": "#178344",
    "Not completed": "#687076",
}

BAND_COLOURS = {
    "Low": "#b42318",
    "Low-moderate": "#e07800",
    "Moderate": "#b38b00",
    "High": "#178344",
}

# Specialist views deliberately focus on the PASS factors most relevant to each team's remit.
# These are screening lenses, not diagnostic scales or automatic referral rules.
LEARNING_SUPPORT_FACTORS = [2, 3, 4, 6, 7, 9]
COUNSELLOR_FACTORS = [1, 3, 5, 7, 8]

# 2026-27 Middle School homeroom teachers from the Homeroom sheet in
# “Homeroom and Secondary Staff Data (A.Y. 2026- 2027)”.
HOMEROOM_TEACHERS = {
    "6.1": "Shruti Uniyal",
    "6.2": "Jigna Doshi",
    "6.3": "Neha Kapadia",
    "6.4": "Sneha Sundrani",
    "6.5": "Debduti Ray",
    "6.6": "Ursula Sanghvi",
    "6.7": "Prathamesh Cheulkar",
    "6.8": "Ramprasad Iyengar",
    "7.1": "Pradeep Singh",
    "7.2": "Aashana Musle",
    "7.3": "Manasi Bhingarde",
    "7.4": "Pallavi Rajguru",
    "7.5": "Vaishnavi Bapardekar",
    "7.6": "Roshan Chavan",
    "7.7": "Antara Roy",
    "7.8": "Rohit Kumar",
    "8.1": "Vanita Amin",
    "8.2": "Swapnil Shetty",
    "8.3": "Lata Dalvi",
    "8.4": "Mamta Pasi",
    "8.5": "Ashwin Subramanian",
    "8.6": "Dhanisha Benoy",
    "8.7": "Neha Basak",
}


st.markdown(
    """
    <style>
      .block-container {padding-top: 1.5rem; padding-bottom: 3rem;}
      div[data-testid="stMetric"] {border: 1px solid #e7e7e7; border-radius: 10px; padding: 10px 14px;}
      .small-note {font-size: 0.9rem; color: #5f6368;}
      .ois-callout {padding: 12px 14px; border-left: 4px solid #2f6f6d; background: #f6f9f9; border-radius: 4px; margin: 8px 0 16px 0;}
    </style>
    """,
    unsafe_allow_html=True,
)


ALLOWED_GOOGLE_DOMAIN = "oberoi-is.org"


def google_auth_gate() -> None:
    auth_config = st.secrets.get("auth", {})
    if not auth_config:
        st.title("OIS Middle School PASS Dashboard")
        st.error("School Google sign-in is not configured yet. An administrator must add the Google OIDC settings to the Streamlit app secrets.")
        st.caption("The dashboard fails closed until Google authentication is configured.")
        st.stop()

    if not st.user.is_logged_in:
        st.title("OIS Middle School PASS Dashboard")
        st.caption("Authorised OIS staff only")
        st.write("Sign in with your **@oberoi-is.org** Google Workspace account.")
        st.button("Sign in with school Google", on_click=st.login, type="primary")
        st.stop()

    identity = st.user.to_dict()
    email = str(identity.get("email", "")).strip().lower()
    name = str(identity.get("name", "")).strip() or email.split("@")[0]

    if identity.get("email_verified") is False:
        st.title("OIS Middle School PASS Dashboard")
        st.error("Google did not return a verified email address for this account.")
        st.button("Sign out", on_click=st.logout)
        st.stop()

    if not email.endswith(f"@{ALLOWED_GOOGLE_DOMAIN}"):
        st.title("OIS Middle School PASS Dashboard")
        st.error("Access is restricted to OIS school Google accounts (@oberoi-is.org).")
        if email:
            st.caption(f"Signed in as {email}")
        st.button("Sign out and use school account", on_click=st.logout, type="primary")
        st.stop()

    st.session_state["staff_name"] = name
    st.session_state["staff_email"] = email


def interpretation_note() -> None:
    with st.expander("How the PASS bands are being used"):
        st.markdown(
            """
**Official PASS percentile interpretation used by this dashboard**

- **1st–5th percentile:** low satisfaction / immediate concern in the PASS guidance
- **6th–20th percentile:** low-moderate
- **21st–30th percentile:** moderate
- **31st–100th percentile:** high

The dashboard then creates an **OIS workflow status** to make follow-up manageable:

- **Immediate review:** at least one factor is at/under the 5th percentile
- **Targeted support:** no factor at/under 5, but at least one factor is at/under the 20th percentile
- **Monitor:** no factor at/under 20, but at least one factor is in the 21st–30th percentile
- **Generally positive:** all nine factors are at/above the 31st percentile

This workflow status is **not an additional PASS score and is not a diagnosis**. Staff should read the pattern across factors alongside attendance, attainment, behaviour, teacher observation and student voice.
            """
        )


def data_quality_strip(df: pd.DataFrame) -> None:
    total = len(df)
    completed = int(df["Completed PASS"].sum())
    missing = total - completed
    immediate = int((df["Attention"].astype(str) == "Immediate review").sum())
    targeted = int((df["Attention"].astype(str) == "Targeted support").sum())
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Students", total)
    c2.metric("PASS completed", f"{completed} ({100*completed/total:.1f}%)" if total else "0")
    c3.metric("Immediate review", immediate)
    c4.metric("Targeted support", targeted)
    if missing:
        st.warning(f"{missing} student(s) do not have a complete set of nine factor scores. They are kept visible as ‘Not completed’. ")


def factor_chart(fs: pd.DataFrame, title: str) -> None:
    if fs.empty:
        st.info("No completed PASS records in this selection.")
        return
    plot = fs.copy()
    plot["Label"] = plot.apply(lambda r: f"F{int(r['Factor'])} {r['Factor name']}", axis=1)
    fig = go.Figure()
    fig.add_bar(
        name="Lowest 5%",
        x=plot["Label"],
        y=plot["% ≤5"],
        marker_color="#b42318",
        hovertemplate="%{x}<br>Lowest 5%: %{y:.1f}%<extra></extra>",
    )
    fig.add_bar(
        name="6–20th percentile",
        x=plot["Label"],
        y=(plot["% ≤20"] - plot["% ≤5"]),
        marker_color="#e07800",
        hovertemplate="%{x}<br>6–20th percentile: %{y:.1f}%<extra></extra>",
    )
    fig.update_layout(
        barmode="stack",
        title=title,
        yaxis_title="% of completed students",
        xaxis_title="",
        legend_title="PASS band",
        height=460,
        margin=dict(l=30, r=20, t=70, b=120),
    )
    fig.update_xaxes(tickangle=-35)
    st.plotly_chart(fig, use_container_width=True)


def attention_chart(summary: pd.DataFrame, group_col: str, title: str) -> None:
    if summary.empty:
        st.info("No PASS records are available for this comparison.")
        return

    attention_cols = ["Immediate review", "Targeted support", "Monitor", "Generally positive"]
    required = [group_col, "Completed", *attention_cols]
    missing = [col for col in required if col not in summary.columns]
    if missing:
        st.warning("This comparison could not be displayed because required summary fields are missing.")
        return

    count_col = "Attention students"
    long = summary.melt(
        id_vars=[group_col, "Completed"],
        value_vars=attention_cols,
        var_name="Attention",
        value_name=count_col,
    )
    completed = pd.to_numeric(long["Completed"], errors="coerce").fillna(0)
    counts = pd.to_numeric(long[count_col], errors="coerce").fillna(0)
    long["Percent"] = (100 * counts.div(completed.where(completed.ne(0)))).fillna(0)

    fig = px.bar(
        long,
        x=group_col,
        y="Percent",
        color="Attention",
        category_orders={"Attention": ATTENTION_ORDER[:-1]},
        color_discrete_map=ATTENTION_COLOURS,
        title=title,
        text_auto=".0f",
    )
    fig.update_layout(barmode="stack", yaxis_title="% of completed students", xaxis_title="", height=430)
    st.plotly_chart(fig, use_container_width=True)


def factor_table(fs: pd.DataFrame) -> None:
    if fs.empty:
        return
    display = fs[["Factor", "Factor name", "Median percentile", "% ≤5", "% ≤20", "% 21–30", "% ≥31", "Completed"]].copy()
    display = display.sort_values(["% ≤20", "% ≤5"], ascending=False)
    st.dataframe(display, hide_index=True, use_container_width=True)


def show_action_cards(context_df: pd.DataFrame, schema, heading: str) -> None:
    st.subheader(heading)
    actions = factor_actions_for_context(context_df, schema, top_n=3)
    if not actions:
        st.info("No completed PASS records in this selection.")
        return
    for item in actions:
        with st.expander(
            f"F{item['factor']} – {item['name']} | {item['pct_concern']:.1f}% at/under 20th percentile",
            expanded=item["factor"] == actions[0]["factor"],
        ):
            st.write(item["description"])
            left, right = st.columns(2)
            with left:
                st.markdown("**Whole-grade / homeroom response**")
                for action in item["universal"]:
                    st.markdown(f"- {action}")
            with right:
                st.markdown("**Targeted response**")
                for action in item["targeted"]:
                    st.markdown(f"- {action}")
            st.markdown("**Useful student questions**")
            for q in item["questions"]:
                st.markdown(f"- {q}")


def show_student_profile(sub: pd.DataFrame, schema, key_prefix: str) -> None:
    completed_sub = sub[sub["Completed PASS"]].copy()
    if completed_sub.empty:
        st.info("No completed student profiles in this selection.")
        return
    options = completed_sub["Student"].sort_values().tolist()
    selected = st.selectbox("Select student", options, key=f"{key_prefix}_student")
    row = completed_sub[completed_sub["Student"] == selected].iloc[0]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Homeroom", row["Homeroom"])
    c2.metric("Attention", str(row["Attention"]))
    c3.metric("Factors ≤20", int(row["Concern count"]))
    c4.metric("Lowest percentile", f"{row['Lowest percentile']:.1f}")

    profile = student_factor_profile(row, schema)
    fig = px.bar(
        profile,
        x="Factor name",
        y="Percentile",
        color="Band",
        category_orders={"Band": ["Low", "Low-moderate", "Moderate", "High"]},
        color_discrete_map=BAND_COLOURS,
        title=f"{selected}: nine-factor PASS profile",
        range_y=[0, 100],
        text_auto=".1f",
    )
    fig.update_layout(height=470, xaxis_title="", yaxis_title="Percentile", margin=dict(b=120))
    fig.update_xaxes(tickangle=-35)
    st.plotly_chart(fig, use_container_width=True)

    flagged = profile[profile["Percentile"].notna() & (profile["Percentile"] <= 30)].copy()
    if flagged.empty:
        st.success("All nine factors are at/above the 31st percentile. Continue normal pastoral monitoring and avoid over-interpreting a positive snapshot.")
    else:
        st.markdown("**Conversation and intervention focus**")
        for _, f in flagged.sort_values("Percentile").iterrows():
            n = int(f["Factor"])
            intervention = INTERVENTIONS[n]
            st.markdown(f"**F{n} {FACTOR_NAMES[n]} — {f['Percentile']:.1f} ({f['Band']})**")
            st.caption(FACTOR_DESCRIPTIONS[n])
            st.markdown(f"- First question: {intervention['questions'][0]}")
            st.markdown(f"- First practical response: {intervention['targeted'][0]}")


def downloadable_csv(df: pd.DataFrame, label: str, filename: str, key: str) -> None:
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(label, data=csv, file_name=filename, mime="text/csv", key=key)


def subgroup_options(df: pd.DataFrame) -> list[str]:
    candidates = ["Gender", "EAL", "SEND", "FSM"]
    available = []
    for c in candidates:
        if c not in df.columns:
            continue
        vals = df[c].dropna().astype(str).str.strip()
        vals = vals[~vals.str.lower().isin(["", "unspecified", "nan", "none"])]
        if vals.nunique() >= 2:
            available.append(c)
    return available


def specialist_factor_summary(df: pd.DataFrame, schema, factors: list[int]) -> pd.DataFrame:
    fs = factor_summary(df, schema)
    if fs.empty:
        return fs
    order = {factor: i for i, factor in enumerate(factors)}
    fs = fs[fs["Factor"].isin(factors)].copy()
    fs["_order"] = fs["Factor"].map(order)
    return fs.sort_values("_order").drop(columns="_order")


def specialist_working_data(df: pd.DataFrame, schema, factors: list[int]) -> pd.DataFrame:
    out = df.copy()
    factor_cols = {n: schema.factor_cols[n] for n in factors}
    cols = list(factor_cols.values())

    completed = out["Completed PASS"].fillna(False).astype(bool)
    scores = out[cols]
    out["Domain immediate count"] = ((scores <= 5).sum(axis=1)).where(completed, 0).astype(int)
    out["Domain concern count"] = ((scores <= 20).sum(axis=1)).where(completed, 0).astype(int)
    out["Domain moderate count"] = (((scores >= 21) & (scores <= 30)).sum(axis=1)).where(completed, 0).astype(int)
    out["Domain lowest percentile"] = scores.min(axis=1, skipna=True)

    def domain_status(row) -> str:
        if not bool(row["Completed PASS"]):
            return "Not completed"
        vals = row[cols]
        if (vals <= 5).any():
            return "Immediate review"
        if (vals <= 20).any():
            return "Targeted support"
        if (vals <= 30).any():
            return "Monitor"
        return "Generally positive"

    def lowest_factor(row) -> str:
        values = {n: row[col] for n, col in factor_cols.items() if not pd.isna(row[col])}
        if not values:
            return ""
        n = min(values, key=values.get)
        return f"F{n} {FACTOR_NAMES[n]}"

    def concern_factors(row, threshold: float) -> str:
        found = []
        for n, col in factor_cols.items():
            value = row[col]
            if not pd.isna(value) and float(value) <= threshold:
                found.append(f"F{n} {FACTOR_NAMES[n]}")
        return "; ".join(found)

    out["Domain attention"] = out.apply(domain_status, axis=1)
    out["Domain lowest factor"] = out.apply(lowest_factor, axis=1)
    out["Domain factors ≤20"] = out.apply(lambda row: concern_factors(row, 20), axis=1)
    out["Domain factors ≤5"] = out.apply(lambda row: concern_factors(row, 5), axis=1)
    return out


def specialist_attention_summary(df: pd.DataFrame, schema, factors: list[int], group_col: str) -> pd.DataFrame:
    working = specialist_working_data(df, schema, factors)
    working = working.copy()
    working["Attention"] = working["Domain attention"]
    return attention_summary(working, group_col)


def specialist_priority_table(df: pd.DataFrame, schema, factors: list[int]) -> pd.DataFrame:
    working = specialist_working_data(df, schema, factors)
    display = working[[
        "Student",
        "Grade",
        "Homeroom",
        "Domain attention",
        "Domain immediate count",
        "Domain concern count",
        "Domain moderate count",
        "Domain lowest factor",
        "Domain lowest percentile",
        "Domain factors ≤5",
        "Domain factors ≤20",
        "Attention",
    ]].copy()
    display = display.rename(columns={
        "Domain attention": "Specialist review",
        "Domain immediate count": "Factors ≤5",
        "Domain concern count": "Factors ≤20",
        "Domain moderate count": "Factors 21–30",
        "Domain lowest factor": "Lowest relevant factor",
        "Domain lowest percentile": "Lowest relevant percentile",
        "Domain factors ≤5": "Relevant factors ≤5",
        "Domain factors ≤20": "Relevant factors ≤20",
        "Attention": "Overall PASS attention",
    })
    rank = {label: i for i, label in enumerate(ATTENTION_ORDER)}
    display["_rank"] = display["Specialist review"].map(rank).fillna(99)
    display = display.sort_values(
        ["_rank", "Factors ≤5", "Factors ≤20", "Factors 21–30", "Lowest relevant percentile"],
        ascending=[True, False, False, False, True],
    ).drop(columns="_rank")
    return display


def specialist_status_strip(df: pd.DataFrame, schema, factors: list[int], label: str) -> None:
    working = specialist_working_data(df, schema, factors)
    total = len(working)
    completed = int(working["Completed PASS"].sum())
    status = working["Domain attention"].astype(str)
    immediate = int((status == "Immediate review").sum())
    targeted = int((status == "Targeted support").sum())
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Students", total)
    c2.metric("PASS completed", f"{completed} ({100*completed/total:.1f}%)" if total else "0")
    c3.metric(f"{label} immediate", immediate)
    c4.metric(f"{label} targeted", targeted)


def show_specialist_action_cards(
    context_df: pd.DataFrame,
    schema,
    factors: list[int],
    heading: str,
    universal_heading: str,
) -> None:
    st.subheader(heading)
    fs = specialist_factor_summary(context_df, schema, factors)
    if fs.empty:
        st.info("No completed PASS records in this selection.")
        return
    top = fs.sort_values(["% ≤20", "% ≤5"], ascending=False).head(3)
    for index, (_, row) in enumerate(top.iterrows()):
        n = int(row["Factor"])
        item = INTERVENTIONS[n]
        with st.expander(
            f"F{n} – {FACTOR_NAMES[n]} | {float(row['% ≤20']):.1f}% at/under 20th percentile",
            expanded=index == 0,
        ):
            st.write(FACTOR_DESCRIPTIONS[n])
            left, right = st.columns(2)
            with left:
                st.markdown(f"**{universal_heading}**")
                for action in item["universal"]:
                    st.markdown(f"- {action}")
            with right:
                st.markdown("**Targeted response**")
                for action in item["targeted"]:
                    st.markdown(f"- {action}")
            st.markdown("**Useful student questions**")
            for question in item["questions"]:
                st.markdown(f"- {question}")


def specialist_scope(df: pd.DataFrame, key: str) -> tuple[pd.DataFrame, str, bool]:
    grades = sorted(df["Grade"].dropna().astype(str).unique().tolist())
    choice = st.selectbox("Scope", ["Whole Middle School", *grades], key=key)
    if choice == "Whole Middle School":
        return df.copy(), choice, True
    return df[df["Grade"] == choice].copy(), choice, False


def render_learning_support(df: pd.DataFrame, schema) -> None:
    st.header("Learning Support view — identify learning barriers and coordinate support")
    st.markdown(
        '<div class="ois-callout"><b>Use PASS to identify patterns that may be affecting access to learning.</b> '
        'This view focuses on learner capability, self-regard, preparedness, work ethic, confidence and curriculum demands. '
        'A low PASS score does not identify SEND or a specific learning difficulty.</div>',
        unsafe_allow_html=True,
    )
    sub, scope_label, whole_school = specialist_scope(df, "ls_scope")
    specialist_status_strip(sub, schema, LEARNING_SUPPORT_FACTORS, "LS")

    tabs = st.tabs(["Learning profile", "Cohort patterns", "Student review queue", "Support planner", "Student explorer"])

    with tabs[0]:
        fs = specialist_factor_summary(sub, schema, LEARNING_SUPPORT_FACTORS)
        factor_chart(fs, f"{scope_label}: learning-support PASS factors")
        factor_table(fs)
        st.caption("Learning Support lens: F2, F3, F4, F6, F7 and F9. Triangulate with attainment, work samples, teacher observation, screening and existing support plans.")

    with tabs[1]:
        group_col = "Grade" if whole_school else "Homeroom"
        summary = specialist_attention_summary(sub, schema, LEARNING_SUPPORT_FACTORS, group_col)
        attention_chart(summary, group_col, f"{scope_label}: learning-support review profile by {group_col.lower()}")
        st.dataframe(summary, hide_index=True, use_container_width=True)

    with tabs[2]:
        priorities = specialist_priority_table(sub, schema, LEARNING_SUPPORT_FACTORS)
        queue = priorities[priorities["Specialist review"].isin(["Immediate review", "Targeted support", "Monitor"])].copy()
        st.dataframe(queue, hide_index=True, use_container_width=True)
        downloadable_csv(queue, "Download Learning Support review queue", "pass_learning_support_review_queue.csv", "ls_students_dl")
        st.info("This is a review queue, not an automatic Learning Support referral list. Check whether the pattern is explained by curriculum fit, organisation, confidence, attendance, language, prior attainment or an already-known learning need before assigning support.")

    with tabs[3]:
        show_specialist_action_cards(
            sub,
            schema,
            LEARNING_SUPPORT_FACTORS,
            f"{scope_label}: Learning Support priorities",
            "Classroom / access response",
        )
        st.markdown(
            "**Suggested Learning Support workflow**  \n"
            "1. Start with students showing multiple relevant factors at/under the 20th percentile.  \n"
            "2. Compare PASS with attainment, work completion, teacher evidence and existing LS records.  \n"
            "3. Agree one measurable access-to-learning intervention before adding multiple supports.  \n"
            "4. Review evidence after 3–4 weeks and adjust only if the intervention is not working."
        )

    with tabs[4]:
        show_student_profile(sub, schema, "ls")


def render_counsellor(df: pd.DataFrame, schema) -> None:
    st.header("Counsellor view — pastoral patterns, check-in triage and student context")
    st.markdown(
        '<div class="ois-callout"><b>Use PASS as an additional pastoral signal, not as a mental-health or risk assessment.</b> '
        'This view focuses on feelings about school, learner self-regard, relationships with teachers, confidence and attendance. '
        'Students should not be referred to counselling solely because of a PASS percentile.</div>',
        unsafe_allow_html=True,
    )
    sub, scope_label, whole_school = specialist_scope(df, "counsellor_scope")
    specialist_status_strip(sub, schema, COUNSELLOR_FACTORS, "Pastoral")

    tabs = st.tabs(["Pastoral profile", "Cohort patterns", "Counsellor review queue", "Conversation planner", "Student explorer"])

    with tabs[0]:
        fs = specialist_factor_summary(sub, schema, COUNSELLOR_FACTORS)
        factor_chart(fs, f"{scope_label}: pastoral PASS factors")
        factor_table(fs)
        st.caption("Counsellor lens: F1, F3, F5, F7 and F8. Read these alongside known pastoral history, attendance, student voice, behaviour and current safeguarding information.")

    with tabs[1]:
        group_col = "Grade" if whole_school else "Homeroom"
        summary = specialist_attention_summary(sub, schema, COUNSELLOR_FACTORS, group_col)
        attention_chart(summary, group_col, f"{scope_label}: pastoral review profile by {group_col.lower()}")
        st.dataframe(summary, hide_index=True, use_container_width=True)

    with tabs[2]:
        priorities = specialist_priority_table(sub, schema, COUNSELLOR_FACTORS)
        queue = priorities[priorities["Specialist review"].isin(["Immediate review", "Targeted support", "Monitor"])].copy()
        st.dataframe(queue, hide_index=True, use_container_width=True)
        downloadable_csv(queue, "Download counsellor review queue", "pass_counsellor_review_queue.csv", "counsellor_students_dl")
        st.warning("A low pastoral PASS factor does not indicate a mental-health condition, self-harm risk or safeguarding risk. Use the queue to identify who merits contextual review or a check-in; follow existing referral and safeguarding procedures when other evidence warrants it.")

    with tabs[3]:
        show_specialist_action_cards(
            sub,
            schema,
            COUNSELLOR_FACTORS,
            f"{scope_label}: pastoral conversation priorities",
            "Universal pastoral response",
        )
        st.markdown(
            "**Suggested counsellor workflow**  \n"
            "1. Check whether students are already known to counselling, safeguarding or the grade team before initiating duplicate contact.  \n"
            "2. Prioritise repeated/multiple low pastoral factors where other evidence also raises concern.  \n"
            "3. Use the PASS profile to shape the opening conversation, not to tell the student what is wrong.  \n"
            "4. Record agreed next steps through the school's normal pastoral/safeguarding systems."
        )
        st.warning("If a conversation raises a safeguarding concern, stop using PASS as the decision framework and follow the school's safeguarding procedure immediately.")

    with tabs[4]:
        show_student_profile(sub, schema, "counsellor")


def render_slt(df: pd.DataFrame, schema) -> None:
    st.header("SLT view — school climate and intervention load")
    st.markdown(
        '<div class="ois-callout"><b>Use this view for decisions, not individual case management.</b> It shows completion, factor patterns, grade variation and where staff capacity may need to be directed.</div>',
        unsafe_allow_html=True,
    )
    data_quality_strip(df)
    tabs = st.tabs(["School picture", "Grade comparison", "Homeroom variation", "Subgroups", "Intervention priorities"])

    with tabs[0]:
        fs = factor_summary(df, schema)
        factor_chart(fs, "School-wide PASS concerns by factor")
        factor_table(fs)
        downloadable_csv(fs, "Download school factor summary", "pass_school_factor_summary.csv", "slt_factor_dl")

    with tabs[1]:
        grades = attention_summary(df, "Grade")
        attention_chart(grades, "Grade", "Student attention profile by grade")
        st.dataframe(grades.sort_values("Grade"), hide_index=True, use_container_width=True)
        downloadable_csv(grades, "Download grade summary", "pass_grade_summary.csv", "slt_grade_dl")

    with tabs[2]:
        hrs = homeroom_summary(df, schema)
        hrs.insert(1, "HRT", hrs["Homeroom"].map(HOMEROOM_TEACHERS).fillna(""))
        cols = ["Homeroom", "HRT", "Students", "Completed", "Completion %", "Immediate review", "Targeted support", "Monitor", "Generally positive", "Immediate/targeted %", "Most common concern", "Top concern % ≤20"]
        st.caption("Use this as a resourcing and follow-up map. Do not infer teacher quality from a homeroom pattern without triangulation.")
        st.dataframe(hrs[cols], hide_index=True, use_container_width=True)
        downloadable_csv(hrs[cols], "Download homeroom summary", "pass_homeroom_summary.csv", "slt_hr_dl")

    with tabs[3]:
        options = subgroup_options(df)
        if not options:
            st.info("No meaningful subgroup fields are populated in this export beyond grade/homeroom.")
        else:
            subgroup = st.selectbox("Subgroup", options)
            summary = attention_summary(df.rename(columns={subgroup: "Selected subgroup"}), "Selected subgroup")
            attention_chart(summary, "Selected subgroup", f"Attention profile by {subgroup}")
            st.dataframe(summary, hide_index=True, use_container_width=True)

    with tabs[4]:
        show_action_cards(df, schema, "Top school-wide intervention priorities")
        st.info("For SLT, the useful question is: which response needs a whole-school system change, and which should remain targeted casework?")


def render_gl(df: pd.DataFrame, schema) -> None:
    st.header("Grade Level Leader view — diagnose the grade and plan interventions")
    grades = sorted(df["Grade"].dropna().astype(str).unique().tolist())
    grade = st.selectbox("Grade", grades, key="gl_grade")
    sub = df[df["Grade"] == grade].copy()
    data_quality_strip(sub)

    tabs = st.tabs(["Grade diagnosis", "Homerooms", "Student priorities", "Intervention planner", "Student explorer"])
    with tabs[0]:
        fs = factor_summary(sub, schema)
        factor_chart(fs, f"{grade}: concern profile across the nine PASS factors")
        factor_table(fs)

    with tabs[1]:
        hrs = homeroom_summary(sub, schema)
        hrs.insert(1, "HRT", hrs["Homeroom"].map(HOMEROOM_TEACHERS).fillna(""))
        st.caption("Start with patterns, then check whether they are consistent across homerooms or concentrated in one group.")
        st.dataframe(hrs, hide_index=True, use_container_width=True)
        attention_chart(attention_summary(sub, "Homeroom"), "Homeroom", f"{grade}: attention profile by homeroom")

    with tabs[2]:
        priorities = student_priority_table(sub)
        focus = priorities[priorities["Attention"] != "Generally positive"].copy()
        st.dataframe(focus, hide_index=True, use_container_width=True)
        downloadable_csv(focus, f"Download {grade} priority list", f"{grade.replace(' ', '_')}_pass_priority_list.csv", "gl_students_dl")
        st.caption("Names are deliberately kept out of the SLT view. This is the working list for GL case review and allocation.")

    with tabs[3]:
        show_action_cards(sub, schema, f"{grade}: intervention priorities")
        st.markdown("**Suggested operating rhythm**")
        st.markdown(
            "1. Review Immediate cases first and confirm whether there is already pastoral/safeguarding context.  \n"
            "2. Assign Targeted cases to HRT/GL/Student Support with one clear first action.  \n"
            "3. Choose no more than two grade-wide actions from the factor pattern.  \n"
            "4. Review evidence after 3–4 weeks; do not wait for the next PASS window to check whether support is working."
        )

    with tabs[4]:
        show_student_profile(sub, schema, "gl")


def render_hrt(df: pd.DataFrame, schema) -> None:
    st.header("Homeroom Teacher view — know your students and act early")
    homerooms = sorted(df["Homeroom"].dropna().astype(str).unique().tolist())
    signed_in = st.session_state.get("staff_name", "").strip().casefold()
    own_homeroom = next(
        (hr for hr, teacher in HOMEROOM_TEACHERS.items() if teacher.casefold() == signed_in and hr in homerooms),
        None,
    )
    default_index = homerooms.index(own_homeroom) if own_homeroom in homerooms else 0
    homeroom = st.selectbox(
        "Homeroom",
        homerooms,
        index=default_index,
        key="hrt_hr",
        format_func=lambda hr: f"{hr} — {HOMEROOM_TEACHERS.get(hr, 'HRT not mapped')}",
    )
    teacher = HOMEROOM_TEACHERS.get(homeroom, "HRT not mapped")
    st.caption(f"Homeroom teacher: **{teacher}**")
    sub = df[df["Homeroom"] == homeroom].copy()
    data_quality_strip(sub)

    tabs = st.tabs(["My homeroom", "Check-in queue", "Interventions", "Student explorer"])
    with tabs[0]:
        fs = factor_summary(sub, schema)
        factor_chart(fs, f"Homeroom {homeroom}: concern profile")
        factor_table(fs)

    with tabs[1]:
        priorities = student_priority_table(sub)
        queue = priorities[priorities["Attention"].isin(["Immediate review", "Targeted support", "Monitor", "Not completed"])].copy()
        st.dataframe(queue, hide_index=True, use_container_width=True)
        downloadable_csv(queue, f"Download {homeroom} check-in queue", f"homeroom_{homeroom}_pass_checkins.csv", "hrt_students_dl")
        st.markdown(
            "**Use the queue this way:** Immediate = prompt adult review; Targeted = planned check-in/intervention; Monitor = watch and speak if other evidence agrees; Not completed = follow up the missing data."
        )

    with tabs[2]:
        show_action_cards(sub, schema, f"Homeroom {homeroom}: most useful actions")
        st.warning("If a conversation raises a safeguarding concern, move out of the PASS workflow and follow the school's safeguarding procedure immediately.")

    with tabs[3]:
        show_student_profile(sub, schema, "hrt")


google_auth_gate()

st.title("OIS Middle School PASS Dashboard")
st.caption("Pupil Attitudes to Self and School | Middle School pastoral analysis and intervention planning")

with st.sidebar:
    st.caption(f"Signed in as **{st.session_state.get('staff_name', 'OIS staff')}**")
    st.caption(st.session_state.get("staff_email", ""))
    st.button("Log out", on_click=st.logout, use_container_width=True)
    st.divider()
    st.header("1. Load PASS data")
    uploaded = st.file_uploader("Upload Testwise PASS Excel export", type=["xlsx"])
    st.caption("Live pupil data is processed in the current Streamlit session. Do not commit the export to GitHub.")

if not uploaded:
    st.info("Upload the PASS Excel export to begin. The app expects the Testwise StudentData layout with nine PASS percentile columns.")
    st.markdown(
        """
### Designed for five layers of use

- **SLT:** high-level school climate, completion, grade/homeroom variation and intervention load — no student names.
- **Grade Level Leaders:** grade diagnosis, homeroom comparison, named student priority list and intervention planning.
- **Homeroom Teachers:** a clear picture of their own homeroom, check-in queue and individual student profiles.
- **Learning Support:** cross-grade learning-barrier patterns, a review queue and targeted access-to-learning responses.
- **Counsellors:** pastoral/relational patterns, a contextual review queue and student conversation planning.

The point is to turn PASS into an operating system for follow-up, not another report staff look at once and forget.
        """
    )
    interpretation_note()
    st.stop()

try:
    df, schema, sheet_name = load_pass_excel(uploaded)
except Exception as exc:
    st.error(f"Could not read this PASS export: {exc}")
    st.stop()

with st.sidebar:
    st.success(f"Loaded {len(df)} students from ‘{sheet_name}’.")
    st.header("2. Choose view")
    role = st.radio(
        "Role",
        ["SLT", "Grade Level Leader", "Homeroom Teacher", "Learning Support", "Counsellor"],
        index=0,
    )
    st.caption("The role selector changes the analysis view; it is not role-based access control. Google sign-in secures access to OIS staff accounts. Role-based permissions are still separate from authentication, so authorised users can currently switch views.")
    st.divider()
    interpretation_note()
    st.caption("PASS is a pastoral screening/attitudinal tool. It should be triangulated with other evidence and must not be treated as a clinical or safeguarding diagnosis.")

if role == "SLT":
    render_slt(df, schema)
elif role == "Grade Level Leader":
    render_gl(df, schema)
elif role == "Homeroom Teacher":
    render_hrt(df, schema)
elif role == "Learning Support":
    render_learning_support(df, schema)
else:
    render_counsellor(df, schema)
