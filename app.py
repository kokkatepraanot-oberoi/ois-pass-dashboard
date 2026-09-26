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


def password_gate() -> None:
    expected = st.secrets.get("APP_PASSWORD", "")
    if not expected:
        st.sidebar.caption("Local/unlocked mode. Configure APP_PASSWORD in Streamlit secrets before school deployment.")
        return
    if st.session_state.get("pass_authenticated"):
        return
    st.title("OIS Middle School PASS Dashboard")
    entered = st.text_input("School access password", type="password")
    if st.button("Enter"):
        if entered == expected:
            st.session_state["pass_authenticated"] = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    st.stop()


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
        return
    long = summary.melt(
        id_vars=[group_col, "Completed"],
        value_vars=["Immediate review", "Targeted support", "Monitor", "Generally positive"],
        var_name="Attention",
        value_name="Students",
    )
    long["Percent"] = long.apply(lambda r: 100 * r["Students"] / r["Completed"] if r["Completed"] else 0, axis=1)
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
        cols = ["Homeroom", "Students", "Completed", "Completion %", "Immediate review", "Targeted support", "Monitor", "Generally positive", "Immediate/targeted %", "Most common concern", "Top concern % ≤20"]
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
    homeroom = st.selectbox("Homeroom", homerooms, key="hrt_hr")
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


password_gate()

st.title("OIS Middle School PASS Dashboard")
st.caption("Pupil Attitudes to Self and School | Middle School pastoral analysis and intervention planning")

with st.sidebar:
    st.header("1. Load PASS data")
    uploaded = st.file_uploader("Upload Testwise PASS Excel export", type=["xlsx"])
    st.caption("Live pupil data is processed in the current Streamlit session. Do not commit the export to GitHub.")

if not uploaded:
    st.info("Upload the PASS Excel export to begin. The app expects the Testwise StudentData layout with nine PASS percentile columns.")
    st.markdown(
        """
### Designed for three levels of use

- **SLT:** high-level school climate, completion, grade/homeroom variation and intervention load — no student names.
- **Grade Level Leaders:** grade diagnosis, homeroom comparison, named student priority list and intervention planning.
- **Homeroom Teachers:** a clear picture of their own homeroom, check-in queue and individual student profiles.

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
    role = st.radio("Role", ["SLT", "Grade Level Leader", "Homeroom Teacher"], index=0)
    st.divider()
    interpretation_note()
    st.caption("PASS is a pastoral screening/attitudinal tool. It should be triangulated with other evidence and must not be treated as a clinical or safeguarding diagnosis.")

if role == "SLT":
    render_slt(df, schema)
elif role == "Grade Level Leader":
    render_gl(df, schema)
else:
    render_hrt(df, schema)
