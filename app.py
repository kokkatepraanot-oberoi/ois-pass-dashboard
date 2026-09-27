from __future__ import annotations

import io
from typing import List

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from pass_logic import (
    ATTENTION_ORDER,
    FACTOR_DESCRIPTIONS,
    FACTOR_NAMES,
    INTERVENTIONS,
    LONGITUDINAL_ORDER,
    attention_summary,
    available_waves,
    factor_actions_for_context,
    factor_summary,
    has_history,
    homeroom_summary,
    latest_snapshot,
    load_pass_excel,
    longitudinal_status_table,
    student_factor_journey,
    student_factor_profile,
    student_priority_table,
    wave_factor_trend_for_chart,
    wave_transition_summary,
)


st.set_page_config(
    page_title="OIS Middle School PASS Dashboard",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)


ATTENTION_COLOURS = {
    "Immediate review": "#ff6b6b",
    "Targeted support": "#ffb020",
    "Monitor": "#ffd43b",
    "Generally positive": "#34c759",
    "Not completed": "#94a3b8",
}

BAND_COLOURS = {
    "Low": "#ff6b6b",
    "Low-moderate": "#ffb020",
    "Moderate": "#ffd43b",
    "High": "#34c759",
}

LONGITUDINAL_COLOURS = {
    "New concern": "#ff9f0a",
    "Persistent concern": "#ff6b6b",
    "Chronic concern": "#ff375f",
    "Recovered": "#34c759",
    "Watch deterioration": "#ffd43b",
    "Stable positive": "#30b0c7",
    "Insufficient history": "#94a3b8",
}

LEARNING_SUPPORT_FACTORS = [2, 3, 4, 6, 7, 9]
COUNSELLOR_FACTORS = [1, 3, 5, 7, 8]

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

ALLOWED_GOOGLE_DOMAIN = "oberoi-is.org"

# Project owner / SLT administrator. Additional roles should be configured in
# Streamlit secrets rather than hard-coded into the repository.
DEFAULT_ADMIN_EMAILS = {"praanot.kokkate@oberoi-is.org"}
ALL_VIEWS = ["SLT", "Grade Level Leader", "Homeroom Teacher", "Learning Support", "Counsellor"]


def _normalise_person(value: str) -> str:
    return " ".join(str(value or "").strip().casefold().split())


def _secret_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [x.strip().casefold() for x in value.split(",") if x.strip()]
    try:
        return [str(x).strip().casefold() for x in value if str(x).strip()]
    except TypeError:
        return []


def resolve_access() -> dict:
    """Resolve role permissions from Google identity + Streamlit secrets.

    Secrets may contain:
      [roles]
      slt = ["name@oberoi-is.org"]
      learning_support = ["name@oberoi-is.org"]
      counsellor = ["name@oberoi-is.org"]

      [roles.grade_leaders]
      "name@oberoi-is.org" = ["Year 6"]

      [roles.homerooms]
      "name@oberoi-is.org" = ["6.1"]
    """
    email = str(st.session_state.get("staff_email", "")).strip().casefold()
    name = _normalise_person(st.session_state.get("staff_name", ""))
    roles = st.secrets.get("roles", {})
    admin_emails = set(DEFAULT_ADMIN_EMAILS) | set(_secret_list(roles.get("admin", [])))

    if email in admin_emails or email in set(_secret_list(roles.get("slt", []))):
        return {"views": ALL_VIEWS.copy(), "grades": None, "homerooms": None, "is_admin": True}

    views: list[str] = []
    grades: list[str] = []
    homerooms: list[str] = []

    if email in set(_secret_list(roles.get("learning_support", []))):
        views.append("Learning Support")
    if email in set(_secret_list(roles.get("counsellor", []))):
        views.append("Counsellor")

    grade_map = roles.get("grade_leaders", {})
    try:
        configured_grades = grade_map.get(email, [])
    except Exception:
        configured_grades = []
    if isinstance(configured_grades, str):
        configured_grades = [configured_grades]
    grades = [str(g).strip() for g in configured_grades if str(g).strip()]
    if grades:
        views.append("Grade Level Leader")

    homeroom_map = roles.get("homerooms", {})
    try:
        configured_homerooms = homeroom_map.get(email, [])
    except Exception:
        configured_homerooms = []
    if isinstance(configured_homerooms, str):
        configured_homerooms = [configured_homerooms]
    homerooms = [str(h).strip() for h in configured_homerooms if str(h).strip()]

    # Safe convenience: infer an HRT's own homeroom from their verified Google display name.
    if not homerooms:
        homerooms = [hr for hr, teacher in HOMEROOM_TEACHERS.items() if _normalise_person(teacher) == name]
    if homerooms:
        views.append("Homeroom Teacher")

    # De-duplicate while preserving order.
    views = list(dict.fromkeys(views))
    return {"views": views, "grades": grades or None, "homerooms": homerooms or None, "is_admin": False}


def apply_theme() -> None:
    st.markdown(
        """
        <style>
        :root {
            --glass-bg: rgba(255,255,255,0.55);
            --glass-border: rgba(255,255,255,0.50);
            --ink: #17202a;
            --muted: #5b6472;
            --accent: #007aff;
            --accent-soft: rgba(0,122,255,0.12);
            --success: #34c759;
            --warning: #ff9f0a;
            --danger: #ff3b30;
        }
        .stApp {
            background:
                radial-gradient(circle at 0% 0%, rgba(113, 192, 255, 0.28), transparent 30%),
                radial-gradient(circle at 100% 0%, rgba(163, 146, 255, 0.25), transparent 30%),
                radial-gradient(circle at 50% 100%, rgba(112, 230, 183, 0.22), transparent 35%),
                linear-gradient(180deg, #f5f7fb 0%, #ecf2f8 100%);
            color: var(--ink);
        }
        [data-testid="stHeader"] {background: rgba(255,255,255,0.24); backdrop-filter: blur(18px);}
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, rgba(255,255,255,0.72), rgba(248,250,253,0.62));
            backdrop-filter: blur(22px);
            border-right: 1px solid rgba(255,255,255,0.65);
        }
        .block-container {padding-top: 1.2rem; padding-bottom: 3rem; max-width: 1500px;}
        .ois-hero {
            padding: 1.4rem 1.6rem;
            border-radius: 28px;
            background: linear-gradient(135deg, rgba(255,255,255,0.68), rgba(255,255,255,0.38));
            border: 1px solid var(--glass-border);
            backdrop-filter: blur(28px);
            box-shadow: 0 16px 44px rgba(23, 32, 42, 0.10);
            margin-bottom: 1rem;
        }
        .ois-subtitle {color: var(--muted); font-size: 0.98rem; margin-top: 0.25rem;}
        .ois-chip-row {display:flex; flex-wrap:wrap; gap:.55rem; margin-top:.75rem;}
        .ois-chip {
            padding: .35rem .75rem; border-radius: 999px;
            background: rgba(255,255,255,0.68);
            border: 1px solid rgba(255,255,255,0.7);
            color: #334155; font-size: .82rem; font-weight: 600;
            box-shadow: 0 6px 18px rgba(15,23,42,0.06);
        }
        div[data-testid="stMetric"] {
            background: linear-gradient(180deg, rgba(255,255,255,0.78), rgba(255,255,255,0.58));
            border: 1px solid rgba(255,255,255,0.78);
            border-radius: 22px;
            padding: 14px 16px;
            box-shadow: 0 12px 26px rgba(15,23,42,0.08);
        }
        .ois-panel {
            background: linear-gradient(180deg, rgba(255,255,255,0.70), rgba(255,255,255,0.52));
            border: 1px solid rgba(255,255,255,0.75);
            border-radius: 24px;
            box-shadow: 0 14px 34px rgba(15,23,42,0.08);
            padding: 1rem 1.05rem;
            margin-bottom: 1rem;
        }
        div.stTabs [data-baseweb="tab-list"] {
            gap: 0.55rem;
            background: rgba(255,255,255,0.48);
            padding: .4rem;
            border-radius: 18px;
            border: 1px solid rgba(255,255,255,.66);
            backdrop-filter: blur(16px);
        }
        div.stTabs [data-baseweb="tab"] {
            height: 44px;
            border-radius: 14px;
            background: rgba(255,255,255,0.26);
            padding: 0 18px;
            color: #4b5563;
            font-weight: 600;
        }
        div.stTabs [aria-selected="true"] {
            background: linear-gradient(180deg, rgba(255,255,255,0.95), rgba(243,247,255,0.82));
            color: #0f172a;
            box-shadow: 0 6px 16px rgba(0,122,255,0.12);
        }
        .stButton > button, .stDownloadButton > button {
            border-radius: 14px;
            border: 1px solid rgba(255,255,255,0.72);
            background: linear-gradient(180deg, rgba(255,255,255,0.82), rgba(242,247,255,0.68));
            color: #0f172a;
            font-weight: 600;
            box-shadow: 0 8px 22px rgba(15,23,42,0.08);
        }
        .stButton > button[kind="primary"] {
            background: linear-gradient(180deg, rgba(0,122,255,0.92), rgba(34,145,255,0.88));
            color: white;
            border: 1px solid rgba(0,122,255,0.65);
        }
        .stDataFrame, [data-testid="stExpander"] {
            background: rgba(255,255,255,0.50);
            border-radius: 20px;
            border: 1px solid rgba(255,255,255,0.68);
            backdrop-filter: blur(18px);
        }
        .ois-callout {
            padding: 13px 15px;
            border-radius: 18px;
            background: linear-gradient(180deg, rgba(0,122,255,0.10), rgba(255,255,255,0.55));
            border: 1px solid rgba(255,255,255,0.74);
            margin: 0.4rem 0 1rem 0;
            color: #1e293b;
        }
        .small-note {font-size: .9rem; color: #667085;}
        @media (max-width: 900px) {
            .block-container {padding-left: .75rem; padding-right: .75rem;}
            .ois-hero {padding: 1rem 1.05rem; border-radius: 22px;}
            .ois-hero h1 {font-size: 1.55rem !important;}
            div.stTabs [data-baseweb="tab-list"] {overflow-x: auto; flex-wrap: nowrap;}
            div.stTabs [data-baseweb="tab"] {padding: 0 12px; white-space: nowrap;}
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def google_auth_gate() -> None:
    auth_config = st.secrets.get("auth", {})
    if not auth_config:
        st.title("OIS Middle School PASS Dashboard")
        st.error("School Google sign-in is not configured yet. An administrator must add the Google OIDC settings to the Streamlit app secrets.")
        st.caption("The dashboard fails closed until Google authentication is configured.")
        st.stop()

    if not st.user.is_logged_in:
        st.markdown('<div class="ois-hero"><h1 style="margin:0">OIS Middle School PASS Dashboard</h1><div class="ois-subtitle">Authorised OIS staff only. Sign in with your school Google account.</div></div>', unsafe_allow_html=True)
        st.button("Sign in with school Google", on_click=st.login, type="primary")
        st.stop()

    identity = st.user.to_dict()
    email = str(identity.get("email", "")).strip().lower()
    name = str(identity.get("name", "")).strip() or email.split("@")[0]

    if identity.get("email_verified") is False:
        st.error("Google did not return a verified email address for this account.")
        st.button("Sign out", on_click=st.logout)
        st.stop()

    if not email.endswith(f"@{ALLOWED_GOOGLE_DOMAIN}"):
        st.error("Access is restricted to OIS school Google accounts (@oberoi-is.org).")
        if email:
            st.caption(f"Signed in as {email}")
        st.button("Sign out and use school account", on_click=st.logout, type="primary")
        st.stop()

    st.session_state["staff_name"] = name
    st.session_state["staff_email"] = email


def hero(latest_df: pd.DataFrame, history_df: pd.DataFrame) -> None:
    latest_wave = latest_df["Wave"].iloc[0] if not latest_df.empty else "Latest"
    chips = [
        f"Latest wave: {latest_wave}",
        f"Students: {len(latest_df)}",
        f"Waves available: {history_df['Wave'].nunique()}",
        "Apple-inspired glass UI",
        "Google Workspace protected",
    ]
    html = '<div class="ois-hero">'
    html += '<h1 style="margin:0 0 .2rem 0; font-size:2rem;">OIS Middle School PASS Dashboard</h1>'
    html += '<div class="ois-subtitle">Pupil Attitudes to Self and School | leadership, intervention planning and longitudinal insight</div>'
    html += '<div class="ois-chip-row">' + ''.join(f'<div class="ois-chip">{c}</div>' for c in chips) + '</div></div>'
    st.markdown(html, unsafe_allow_html=True)


def interpretation_note() -> None:
    with st.expander("How PASS is being interpreted in this dashboard"):
        st.markdown(
            """
- **1st–5th percentile:** low / immediate concern
- **6th–20th percentile:** low-moderate
- **21st–30th percentile:** moderate
- **31st–100th percentile:** high

The app then uses an OIS workflow label to support action:
- **Immediate review**: at least one factor is at/under the 5th percentile
- **Targeted support**: no factor at/under 5, but at least one factor is at/under the 20th percentile
- **Monitor**: no factor at/under 20, but at least one factor is in the 21st–30th percentile
- **Generally positive**: all nine factors are at/above the 31st percentile

Where multiple survey waves are present, the app also highlights:
- **New concern**
- **Persistent concern**
- **Chronic concern**
- **Recovered**
- **Watch deterioration**
- **Stable positive**

PASS is a **screening / attitudinal tool**. It is not a diagnosis and must be triangulated with attendance, attainment, behaviour, teacher observation and student voice.
            """
        )


def downloadable_csv(df: pd.DataFrame, label: str, filename: str, key: str) -> None:
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(label, data=csv, file_name=filename, mime="text/csv", key=key)


def metric_strip(df: pd.DataFrame, extra_label: str | None = None, extra_value: str | int | None = None) -> None:
    total = len(df)
    completed = int(df["Completed PASS"].sum())
    immediate = int((df["Attention"].astype(str) == "Immediate review").sum())
    targeted = int((df["Attention"].astype(str) == "Targeted support").sum())
    cols = st.columns(5 if extra_label else 4)
    cols[0].metric("Students", total)
    cols[1].metric("PASS completed", f"{completed} ({100*completed/total:.1f}%)" if total else "0")
    cols[2].metric("Immediate review", immediate)
    cols[3].metric("Targeted support", targeted)
    if extra_label:
        cols[4].metric(extra_label, extra_value if extra_value is not None else "—")


def factor_chart(fs: pd.DataFrame, title: str) -> None:
    if fs.empty:
        st.info("No completed PASS records in this selection.")
        return
    plot = fs.copy()
    plot["Label"] = plot.apply(lambda r: f"F{int(r['Factor'])}", axis=1)
    fig = go.Figure()
    fig.add_bar(name="Lowest 5%", x=plot["Label"], y=plot["% ≤5"], marker_color="#ff6b6b")
    fig.add_bar(name="6–20th percentile", x=plot["Label"], y=(plot["% ≤20"] - plot["% ≤5"]), marker_color="#ffb020")
    fig.update_layout(
        barmode="stack",
        title=title,
        yaxis_title="% of completed students",
        xaxis_title="PASS factor",
        height=430,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=60, b=40),
    )
    st.plotly_chart(fig, use_container_width=True)


def factor_table(fs: pd.DataFrame) -> None:
    if fs.empty:
        return
    display = fs[["Factor", "Factor name", "Median percentile", "% ≤5", "% ≤20", "% 21–30", "% ≥31", "Completed"]].copy()
    display = display.sort_values(["% ≤20", "% ≤5"], ascending=False)
    st.dataframe(display, hide_index=True, use_container_width=True)


def attention_chart(summary: pd.DataFrame, group_col: str, title: str) -> None:
    if summary.empty:
        st.info("No PASS records are available for this comparison.")
        return
    attention_cols = ["Immediate review", "Targeted support", "Monitor", "Generally positive"]
    long = summary.melt(
        id_vars=[group_col, "Completed"],
        value_vars=attention_cols,
        var_name="Attention",
        value_name="Students in band",
    )
    long["Percent"] = (100 * pd.to_numeric(long["Students in band"], errors="coerce").fillna(0) / pd.to_numeric(long["Completed"], errors="coerce").replace(0, pd.NA)).fillna(0)
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
    fig.update_layout(
        barmode="stack",
        height=420,
        yaxis_title="% of completed students",
        xaxis_title="",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=60, b=40),
    )
    st.plotly_chart(fig, use_container_width=True)


def trend_line_chart(history_df: pd.DataFrame, schema, title: str, factors: List[int] | None = None, value_col: str = "% ≤20") -> None:
    trend = wave_factor_trend_for_chart(history_df, schema, factors=factors)
    if trend.empty:
        st.info("Not enough historical survey waves for this trend view.")
        return
    trend["Series"] = trend["Factor"].apply(lambda n: f"F{int(n)}")
    x_col = "Wave"
    if "Grade at survey (inferred)" in history_df.columns and history_df["Grade"].nunique() == 1:
        wave_context = (
            history_df[["Wave", "Wave key", "Grade at survey (inferred)"]]
            .sort_values("Wave key")
            .drop_duplicates(subset=["Wave"], keep="last")
        )
        grade_map = dict(zip(wave_context["Wave"], wave_context["Grade at survey (inferred)"]))
        trend["Wave display"] = trend["Wave"].map(
            lambda wave: f"{wave}<br><sup>{grade_map.get(wave, '')}*</sup>"
        )
        x_col = "Wave display"
    fig = px.line(
        trend.sort_values("Wave sort"),
        x=x_col,
        y=value_col,
        color="Series",
        markers=True,
        title=title,
        hover_data={"Factor name": True, "Wave sort": False},
    )
    fig.update_layout(
        height=420,
        yaxis_title=value_col,
        xaxis_title="Survey wave",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=60, b=40),
    )
    st.plotly_chart(fig, use_container_width=True)


def transition_chart(history_df: pd.DataFrame, schema, title: str, factors: List[int] | None = None) -> None:
    trans = wave_transition_summary(history_df, schema, factors=factors)
    if trans.empty:
        st.info("At least two survey waves are needed for emerging/persistent comparisons.")
        return
    long = trans.melt(
        id_vars=["Factor", "Factor name"],
        value_vars=["Persistent", "New", "Recovered", "Watch deterioration"],
        var_name="Transition",
        value_name="Students",
    )
    fig = px.bar(
        long,
        x="Factor",
        y="Students",
        color="Transition",
        barmode="group",
        title=title,
        text_auto=True,
    )
    fig.update_layout(
        height=420,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=60, b=40),
    )
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(trans, hide_index=True, use_container_width=True)


def show_action_cards(context_df: pd.DataFrame, schema, heading: str) -> None:
    st.subheader(heading)
    actions = factor_actions_for_context(context_df, schema, top_n=3)
    if not actions:
        st.info("No completed PASS records in this selection.")
        return
    for idx, item in enumerate(actions):
        with st.expander(
            f"F{item['factor']} – {item['name']} | {item['pct_concern']:.1f}% at/under 20th percentile",
            expanded=idx == 0,
        ):
            st.write(item["description"])
            left, right = st.columns(2)
            with left:
                st.markdown("**Whole-cohort / homeroom response**")
                for action in item["universal"]:
                    st.markdown(f"- {action}")
            with right:
                st.markdown("**Targeted response**")
                for action in item["targeted"]:
                    st.markdown(f"- {action}")
            st.markdown("**Useful student questions**")
            for q in item["questions"]:
                st.markdown(f"- {q}")


def student_summary_text(history_df: pd.DataFrame, student_id: str, schema, factors: List[int] | None = None) -> List[str]:
    journey = student_factor_journey(history_df, schema, student_id, factors=factors)
    if journey.empty:
        return ["No student history available."]
    out = []
    for factor, sub in journey.groupby("Factor"):
        sub = sub.sort_values("Wave sort")
        first = sub.iloc[0]["Percentile"]
        last = sub.iloc[-1]["Percentile"]
        if pd.isna(first) or pd.isna(last):
            continue
        name = FACTOR_NAMES[int(factor)]
        if last <= 20 and first > 20:
            out.append(f"F{factor} {name} has become a current concern over time.")
        elif last > 30 and first <= 20:
            out.append(f"F{factor} {name} has moved into a healthier band since the earlier survey.")
        elif last < first - 15:
            out.append(f"F{factor} {name} has declined noticeably across the available waves.")
    return out[:4] or ["No strong longitudinal movement stands out across the selected factors."]


def show_student_profile(current_df: pd.DataFrame, history_df: pd.DataFrame, schema, key_prefix: str, factors: List[int] | None = None) -> None:
    completed_sub = current_df[current_df["Completed PASS"]].copy()
    if completed_sub.empty:
        st.info("No completed student profiles in this selection.")
        return
    options = completed_sub[["Student", "Student ID"]].drop_duplicates().sort_values("Student")
    display_names = options["Student"].tolist()
    mapping = dict(zip(options["Student"], options["Student ID"]))
    selected_name = st.selectbox("Select student", display_names, key=f"{key_prefix}_student")
    student_id = mapping[selected_name]
    row = completed_sub[completed_sub["Student ID"] == student_id].iloc[0]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Homeroom", row["Homeroom"])
    c2.metric("Attention", str(row["Attention"]))
    c3.metric("Factors ≤20", int(row["Concern count"]))
    c4.metric("Lowest percentile", f"{row['Lowest percentile']:.1f}")

    profile = student_factor_profile(row, schema)
    if factors:
        profile = profile[profile["Factor"].isin(factors)]
    fig = px.bar(
        profile,
        x="Factor name",
        y="Percentile",
        color="Band",
        category_orders={"Band": ["Low", "Low-moderate", "Moderate", "High"]},
        color_discrete_map=BAND_COLOURS,
        title="Current PASS profile",
        text_auto=".1f",
    )
    fig.update_layout(
        height=430,
        yaxis_title="Percentile",
        xaxis_title="",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=60, b=70),
    )
    st.plotly_chart(fig, use_container_width=True)

    if has_history(history_df):
        journey = student_factor_journey(history_df, schema, student_id, factors=factors)
        if not journey.empty:
            line = px.line(
                journey.sort_values("Wave sort"),
                x="Wave",
                y="Percentile",
                color="Factor name",
                markers=True,
                title="Student journey over time",
            )
            line.update_layout(
                height=430,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=20, r=20, t=60, b=40),
            )
            st.plotly_chart(line, use_container_width=True)
            st.markdown("**What stands out**")
            for bullet in student_summary_text(history_df, student_id, schema, factors=factors):
                st.markdown(f"- {bullet}")

    st.dataframe(profile[["Factor", "Factor name", "Percentile", "Band", "Description"]], hide_index=True, use_container_width=True)
    st.markdown("**Useful student questions**")
    for _, r in profile.sort_values("Percentile", na_position="last").head(2).iterrows():
        item = INTERVENTIONS[int(r["Factor"])]
        st.markdown(f"**F{int(r['Factor'])} {r['Factor name']}**")
        for q in item["questions"]:
            st.markdown(f"- {q}")


def build_domain_data(df: pd.DataFrame, schema, factors: List[int]) -> pd.DataFrame:
    out = df.copy()
    cols = [schema.factor_cols[n] for n in factors]

    def domain_attention(row):
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

    out["Domain attention"] = out.apply(domain_attention, axis=1)
    out["Domain factors ≤5"] = out[cols].apply(lambda row: int((row <= 5).sum()) if row.notna().all() else 0, axis=1)
    out["Domain factors ≤20"] = out[cols].apply(lambda row: int((row <= 20).sum()) if row.notna().all() else 0, axis=1)
    out["Domain factors 21–30"] = out[cols].apply(lambda row: int(((row >= 21) & (row <= 30)).sum()) if row.notna().all() else 0, axis=1)
    out["Lowest relevant percentile"] = out[cols].min(axis=1, skipna=True)
    return out


def specialist_summary(df: pd.DataFrame, schema, factors: List[int], group_col: str) -> pd.DataFrame:
    working = build_domain_data(df, schema, factors)
    items = []
    for group, sub in working.groupby(group_col, dropna=False):
        completed = int(sub["Completed PASS"].sum())
        total = len(sub)
        counts = sub["Domain attention"].astype(str).value_counts()
        item = {group_col: group, "Students": total, "Completed": completed}
        for label in ATTENTION_ORDER:
            item[label] = int(counts.get(label, 0))
        item["Immediate/targeted %"] = round(100 * (item["Immediate review"] + item["Targeted support"]) / completed, 1) if completed else 0
        items.append(item)
    return pd.DataFrame(items)


def specialist_priority_table(df: pd.DataFrame, schema, factors: List[int], history_df: pd.DataFrame | None = None) -> pd.DataFrame:
    working = build_domain_data(df, schema, factors)
    cols = [
        "Student", "Student ID", "Grade", "Homeroom", "Domain attention", "Domain factors ≤5", "Domain factors ≤20", "Domain factors 21–30", "Lowest relevant percentile", "Attention",
    ]
    out = working[cols].copy().rename(columns={"Domain attention": "Specialist review"})
    if history_df is not None and has_history(history_df):
        longi = longitudinal_status_table(history_df, df, schema, factors=factors)[["Student ID", "Longitudinal status", "Concern waves (max factor)"]]
        out = out.merge(longi, on="Student ID", how="left")
    rank = {v: i for i, v in enumerate(ATTENTION_ORDER)}
    out["_rank"] = out["Specialist review"].map(rank).fillna(99)
    out = out.sort_values(["_rank", "Domain factors ≤5", "Domain factors ≤20", "Lowest relevant percentile"], ascending=[True, False, False, True]).drop(columns="_rank")
    return out


def intervention_tracker(scope_label: str, key_prefix: str) -> None:
    st.markdown("**Intervention tracker (session-based)**")
    template = pd.DataFrame(
        [
            {
                "Student/Cohort": "",
                "PASS issue": "",
                "Baseline": "",
                "Action": "",
                "Owner": "",
                "Start date": "",
                "Review date": "",
                "Evidence to collect": "",
                "Outcome": "",
            }
        ]
    )
    key = f"tracker_{key_prefix}"
    if key not in st.session_state:
        st.session_state[key] = template.copy()
    edited = st.data_editor(st.session_state[key], num_rows="dynamic", use_container_width=True, key=f"tracker_editor_{key_prefix}")
    st.session_state[key] = edited
    downloadable_csv(edited, f"Download {scope_label} intervention tracker", f"{key_prefix}_intervention_tracker.csv", f"dl_{key_prefix}")
    st.caption("This tracker is session-based in Streamlit. For long-term storage, export the CSV and keep it in the school's protected workflow.")


def download_excel_bundle(latest_df: pd.DataFrame, history_df: pd.DataFrame, schema, label: str, filename: str, key: str) -> None:
    buffer = io.BytesIO()
    longi = longitudinal_status_table(history_df, latest_df, schema) if has_history(history_df) else pd.DataFrame()
    transitions = wave_transition_summary(history_df, schema) if has_history(history_df) else pd.DataFrame()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        factor_summary(latest_df, schema).to_excel(writer, sheet_name="Latest factor summary", index=False)
        attention_summary(latest_df, "Grade").to_excel(writer, sheet_name="Grade summary", index=False)
        homeroom_summary(latest_df, schema).to_excel(writer, sheet_name="Homeroom summary", index=False)
        student_priority_table(latest_df).to_excel(writer, sheet_name="Latest student list", index=False)
        if not longi.empty:
            longi.to_excel(writer, sheet_name="Longitudinal", index=False)
        if not transitions.empty:
            transitions.to_excel(writer, sheet_name="Wave transitions", index=False)
    st.download_button(label, data=buffer.getvalue(), file_name=filename, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key=key)


def workflow_editor(seed_df: pd.DataFrame, key_prefix: str, heading: str = "Action / review log") -> None:
    st.markdown(f"**{heading}**")
    state_key = f"workflow_{key_prefix}"
    upload = st.file_uploader("Load an existing action log (optional)", type=["csv"], key=f"upload_{key_prefix}")
    if upload is not None:
        try:
            loaded = pd.read_csv(upload)
            st.session_state[state_key] = loaded
        except Exception as exc:
            st.warning(f"Could not load that action log: {exc}")

    if state_key not in st.session_state:
        base_cols = ["Student", "Student ID", "Attention"]
        available = [c for c in base_cols if c in seed_df.columns]
        seed = seed_df[available].head(40).copy() if available else pd.DataFrame()
        if "Student" not in seed.columns:
            seed["Student"] = ""
        if "Student ID" not in seed.columns:
            seed["Student ID"] = ""
        if "Attention" not in seed.columns:
            seed["Attention"] = ""
        seed["Concern / focus"] = ""
        seed["Action agreed"] = ""
        seed["Owner"] = st.session_state.get("staff_name", "")
        seed["Review date"] = ""
        seed["Status"] = "Not started"
        seed["Escalate to"] = ""
        seed["Brief evidence / outcome"] = ""
        st.session_state[state_key] = seed

    edited = st.data_editor(
        st.session_state[state_key],
        num_rows="dynamic",
        use_container_width=True,
        key=f"editor_{key_prefix}",
        column_config={
            "Status": st.column_config.SelectboxColumn(options=["Not started", "In progress", "Review due", "Complete"]),
            "Escalate to": st.column_config.SelectboxColumn(options=["", "GL", "Learning Support", "Counsellor", "SLT", "Safeguarding"]),
        },
    )
    st.session_state[state_key] = edited
    downloadable_csv(edited, "Download action log", f"{key_prefix}_action_log.csv", f"workflow_dl_{key_prefix}")
    st.caption("The log is held only in the current Streamlit session. Download it before leaving. Keep notes brief; detailed counselling or safeguarding records belong in the school's approved systems.")


def render_slt(latest_df: pd.DataFrame, history_df: pd.DataFrame, schema) -> None:
    st.markdown('<div class="ois-callout"><b>SLT:</b> focus on patterns, capacity and whole-school response — not named student casework.</div>', unsafe_allow_html=True)
    metric_strip(latest_df, extra_label="Survey waves", extra_value=history_df["Wave"].nunique())
    tabs = st.tabs(["School picture", "Trends over time", "Emerging vs persistent", "Grade comparison", "Homeroom variation", "Intervention priorities"])

    with tabs[0]:
        fs = factor_summary(latest_df, schema)
        factor_chart(fs, "Current school-wide PASS concerns by factor")
        factor_table(fs)
        downloadable_csv(fs, "Download school factor summary", "pass_school_factor_summary.csv", "slt_factor_dl")

    with tabs[1]:
        if has_history(history_df):
            trend_line_chart(history_df, schema, "Five-wave factor trend (% at/under 20th percentile)")
            st.info("Historical analysis is based on the survey waves in the uploaded file. Where historical rows carry current year/homeroom labels, interpret trends as 'current cohort journey' rather than 'historical year-group snapshot'.")
        else:
            st.info("Upload a multi-wave PASS export to unlock trend analysis.")

    with tabs[2]:
        if has_history(history_df):
            transition_chart(history_df, schema, "Latest wave compared with previous wave")
            longi = longitudinal_status_table(history_df, latest_df, schema)
            counts = longi["Longitudinal status"].value_counts().reindex(LONGITUDINAL_ORDER, fill_value=0).reset_index()
            counts.columns = ["Longitudinal status", "Students"]
            fig = px.bar(counts, x="Longitudinal status", y="Students", color="Longitudinal status", color_discrete_map=LONGITUDINAL_COLOURS, title="Student longitudinal profile")
            fig.update_layout(height=380, showlegend=False, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
            strategic = longi[longi["Longitudinal status"].isin(["New concern", "Persistent concern", "Chronic concern", "Recovered", "Watch deterioration"])].copy()
            slt_longitudinal = (
                strategic.groupby(["Grade", "Longitudinal status"], dropna=False)
                .size()
                .reset_index(name="Students")
                .sort_values(["Grade", "Students"], ascending=[True, False])
            )
            st.dataframe(slt_longitudinal, hide_index=True, use_container_width=True)
            st.caption("The SLT longitudinal view deliberately stays at cohort level. Named students remain in the GL, HRT and specialist views.")
        else:
            st.info("At least two survey waves are needed for emerging/persistent analysis.")

    with tabs[3]:
        grades = attention_summary(latest_df, "Grade")
        attention_chart(grades, "Grade", "Current attention profile by grade")
        st.dataframe(grades.sort_values("Grade"), hide_index=True, use_container_width=True)

    with tabs[4]:
        hrs = homeroom_summary(latest_df, schema)
        hrs.insert(1, "HRT", hrs["Homeroom"].map(HOMEROOM_TEACHERS).fillna(""))
        cols = ["Homeroom", "HRT", "Students", "Completed", "Completion %", "Immediate review", "Targeted support", "Monitor", "Generally positive", "Immediate/targeted %", "Most common concern", "Top concern % ≤20"]
        st.dataframe(hrs[cols], hide_index=True, use_container_width=True)
        downloadable_csv(hrs[cols], "Download homeroom summary", "pass_homeroom_summary.csv", "slt_hr_dl")

    with tabs[5]:
        show_action_cards(latest_df, schema, "Top school-wide intervention priorities")
        st.markdown("**Leadership prompts**")
        st.markdown("- Which 2–3 factor patterns require a system response rather than individual casework?")
        st.markdown("- Which grade or homeroom requires follow-up support or capacity-building?")
        st.markdown("- Which emerging patterns look new this cycle and therefore deserve immediate enquiry?")
        intervention_tracker("SLT", "slt")
        download_excel_bundle(latest_df, history_df, schema, "Download SLT analysis workbook", "OIS_PASS_SLT_analysis.xlsx", "slt_excel_bundle")


def render_gl(latest_df: pd.DataFrame, history_df: pd.DataFrame, schema, allowed_grades: list[str] | None = None) -> None:
    grades = sorted(latest_df["Grade"].dropna().astype(str).unique().tolist())
    if allowed_grades:
        grades = [g for g in grades if g in allowed_grades]
    if not grades:
        st.error("No grade has been assigned to your Grade Level Leader account.")
        st.stop()
    grade = grades[0] if len(grades) == 1 else st.selectbox("Grade", grades, key="gl_grade")
    if len(grades) == 1:
        st.caption(f"Access restricted to **{grade}**")
    current = latest_df[latest_df["Grade"] == grade].copy()
    history = history_df[history_df["Grade"] == grade].copy() if has_history(history_df) else current.copy()
    st.markdown('<div class="ois-callout"><b>GL:</b> diagnose the grade, identify students/cohorts needing follow-up, and allocate interventions clearly.</div>', unsafe_allow_html=True)
    metric_strip(current, extra_label="Homerooms", extra_value=current["Homeroom"].nunique())
    tabs = st.tabs(["Current picture", "Trends over time", "Student journey table", "Homerooms", "Intervention planner", "Student explorer"])

    with tabs[0]:
        fs = factor_summary(current, schema)
        factor_chart(fs, f"{grade}: current concern profile")
        factor_table(fs)
        download_excel_bundle(current, history, schema, f"Download {grade} analysis workbook", f"{grade.replace(' ', '_')}_PASS_analysis.xlsx", "gl_excel_bundle")

    with tabs[1]:
        if has_history(history_df):
            trend_line_chart(history, schema, f"Current {grade} cohort: PASS journey over time (% at/under 20th percentile)")
            st.caption("* Earlier year labels are inferred from the student’s current year and survey date because Testwise stamps the current year/group onto historical rows. For current Year 6, the 2024–26 points are Primary PASS results until Sep 2026.")
            transition_chart(history, schema, f"Current {grade} cohort: latest wave vs previous wave")
        else:
            st.info("Upload a multi-wave PASS export to unlock grade trends.")

    with tabs[2]:
        longi = longitudinal_status_table(history_df if has_history(history_df) else current, current, schema)
        st.dataframe(longi, hide_index=True, use_container_width=True)
        downloadable_csv(longi, f"Download {grade} student journey table", f"{grade.replace(' ', '_')}_journey_table.csv", "gl_journey_dl")

    with tabs[3]:
        hrs = homeroom_summary(current, schema)
        hrs.insert(1, "HRT", hrs["Homeroom"].map(HOMEROOM_TEACHERS).fillna(""))
        st.dataframe(hrs, hide_index=True, use_container_width=True)
        attention_chart(attention_summary(current, "Homeroom"), "Homeroom", f"{grade}: attention profile by homeroom")

    with tabs[4]:
        priorities = student_priority_table(current)
        focus = priorities[priorities["Attention"] != "Generally positive"].copy()
        st.dataframe(focus, hide_index=True, use_container_width=True)
        show_action_cards(current, schema, f"{grade}: intervention priorities")
        intervention_tracker(grade, f"gl_{grade.replace(' ', '_')}")
        workflow_editor(focus, f"gl_{grade.replace(' ', '_')}", "Student intervention / review log")

    with tabs[5]:
        show_student_profile(current, history_df if has_history(history_df) else current, schema, "gl")


def render_hrt(latest_df: pd.DataFrame, history_df: pd.DataFrame, schema, allowed_homerooms: list[str] | None = None) -> None:
    homerooms = sorted(latest_df["Homeroom"].dropna().astype(str).unique().tolist())
    if allowed_homerooms:
        homerooms = [hr for hr in homerooms if hr in allowed_homerooms]
    if not homerooms:
        st.error("No homeroom has been assigned to your account.")
        st.stop()
    homeroom = homerooms[0] if len(homerooms) == 1 else st.selectbox("Homeroom", homerooms, format_func=lambda hr: f"{hr} — {HOMEROOM_TEACHERS.get(hr, 'HRT not mapped')}")
    if len(homerooms) == 1:
        st.caption(f"Access restricted to **{homeroom} — {HOMEROOM_TEACHERS.get(homeroom, 'HRT')}**")
    current = latest_df[latest_df["Homeroom"] == homeroom].copy()
    history = history_df[history_df["Homeroom"] == homeroom].copy() if has_history(history_df) else current.copy()
    st.caption(f"Homeroom teacher: **{HOMEROOM_TEACHERS.get(homeroom, 'HRT not mapped')}**")
    st.markdown('<div class="ois-callout"><b>HRT:</b> keep this simple — know which students need a conversation, what the likely pattern is, and what your first action should be.</div>', unsafe_allow_html=True)
    metric_strip(current, extra_label="Students in homeroom", extra_value=len(current))
    tabs = st.tabs(["My homeroom", "Student journey", "Check-in queue", "Interventions", "Student explorer"])

    with tabs[0]:
        fs = factor_summary(current, schema)
        factor_chart(fs, f"Homeroom {homeroom}: current concern profile")
        factor_table(fs)

    with tabs[1]:
        if has_history(history_df):
            longi = longitudinal_status_table(history_df, current, schema)
            st.dataframe(longi, hide_index=True, use_container_width=True)
            counts = longi["Longitudinal status"].value_counts().reindex(LONGITUDINAL_ORDER, fill_value=0).reset_index()
            counts.columns = ["Longitudinal status", "Students"]
            fig = px.bar(counts, x="Longitudinal status", y="Students", color="Longitudinal status", color_discrete_map=LONGITUDINAL_COLOURS, title="Homeroom longitudinal picture")
            fig.update_layout(height=360, showlegend=False, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Upload a multi-wave PASS export to unlock student-journey patterns.")

    with tabs[2]:
        priorities = student_priority_table(current)
        queue = priorities[priorities["Attention"].isin(["Immediate review", "Targeted support", "Monitor", "Not completed"])].copy()
        if has_history(history_df):
            longi = longitudinal_status_table(history_df, current, schema)[["Student ID", "Longitudinal status", "Concern waves (max factor)"]]
            queue = queue.merge(longi, on="Student ID", how="left")
        st.dataframe(queue, hide_index=True, use_container_width=True)
        downloadable_csv(queue, f"Download {homeroom} check-in queue", f"homeroom_{homeroom}_pass_checkins.csv", "hrt_students_dl")
        st.markdown("**Use this queue this way**")
        st.markdown("- Immediate = prompt adult review")
        st.markdown("- Targeted = planned check-in/intervention")
        st.markdown("- Monitor = watch and speak if other evidence agrees")
        st.markdown("- Not completed = follow up the missing data")

    with tabs[3]:
        show_action_cards(current, schema, f"Homeroom {homeroom}: most useful actions")
        intervention_tracker(homeroom, f"hrt_{homeroom}")
        workflow_editor(queue if 'queue' in locals() else student_priority_table(current), f"hrt_{homeroom}", "HRT check-in / review log")
        st.warning("If a conversation raises a safeguarding concern, stop using PASS as the decision framework and follow the school's safeguarding process immediately.")

    with tabs[4]:
        show_student_profile(current, history_df if has_history(history_df) else current, schema, "hrt")


def render_specialist(latest_df: pd.DataFrame, history_df: pd.DataFrame, schema, role_name: str, factors: List[int], intro: str, queue_caption: str) -> None:
    grades = sorted(latest_df["Grade"].dropna().astype(str).unique().tolist())
    scope = st.selectbox("Scope", ["Whole Middle School", *grades], key=f"scope_{role_name}")
    current = latest_df.copy() if scope == "Whole Middle School" else latest_df[latest_df["Grade"] == scope].copy()
    history = history_df.copy() if scope == "Whole Middle School" else history_df[history_df["Grade"] == scope].copy()
    st.markdown(f'<div class="ois-callout"><b>{role_name}:</b> {intro}</div>', unsafe_allow_html=True)
    metric_strip(current, extra_label="Specialist factors", extra_value=len(factors))
    tabs = st.tabs(["Profile", "Cohort patterns", "Review queue", "Intervention planning", "Student explorer"])

    with tabs[0]:
        fs = factor_summary(current, schema)
        fs = fs[fs["Factor"].isin(factors)]
        factor_chart(fs, f"{scope}: {role_name} factor profile")
        factor_table(fs)

    with tabs[1]:
        group_col = "Grade" if scope == "Whole Middle School" else "Homeroom"
        summary = specialist_summary(current, schema, factors, group_col)
        attention_chart(summary, group_col, f"{scope}: {role_name} review profile by {group_col.lower()}")
        st.dataframe(summary, hide_index=True, use_container_width=True)
        if has_history(history_df):
            trend_title = "Whole Middle School: specialist trend over time" if scope == "Whole Middle School" else f"Current {scope} cohort: specialist PASS journey over time"
            trend_line_chart(history, schema, trend_title, factors=factors)
            if scope != "Whole Middle School":
                st.caption("* Earlier year labels are inferred from the student’s current year and survey date. Testwise stamps current year/group labels onto historical rows, so earlier points may be Primary results for current Year 6 students.")

    with tabs[2]:
        queue = specialist_priority_table(current, schema, factors, history_df if has_history(history_df) else None)
        queue = queue[queue["Specialist review"].isin(["Immediate review", "Targeted support", "Monitor"])].copy()
        st.dataframe(queue, hide_index=True, use_container_width=True)
        downloadable_csv(queue, f"Download {role_name} review queue", f"{role_name.lower().replace(' ', '_')}_review_queue.csv", f"{role_name}_dl")
        st.caption(queue_caption)

    with tabs[3]:
        show_action_cards(current[[*current.columns]], schema, f"{scope}: priority actions")
        intervention_tracker(role_name, role_name.lower().replace(' ', '_'))
        workflow_editor(queue if 'queue' in locals() else specialist_priority_table(current, schema, factors), role_name.lower().replace(' ', '_'), f"{role_name} review log")

    with tabs[4]:
        show_student_profile(current, history_df if has_history(history_df) else current, schema, role_name.lower().replace(' ', '_'), factors=factors)


def main() -> None:
    apply_theme()
    google_auth_gate()

    with st.sidebar:
        st.caption(f"Signed in as **{st.session_state.get('staff_name', 'OIS staff')}**")
        st.caption(st.session_state.get("staff_email", ""))
        st.button("Log out", on_click=st.logout, use_container_width=True)
        st.divider()
        st.header("1. Load PASS data")
        uploaded = st.file_uploader("Upload Testwise PASS Excel export", type=["xlsx"])
        st.caption("A single-wave export will run the core dashboard. A multi-wave export unlocks longitudinal analysis.")

    if not uploaded:
        st.markdown('<div class="ois-hero"><h1 style="margin:0">OIS Middle School PASS Dashboard</h1><div class="ois-subtitle">Upload a PASS export to begin. The app supports current snapshots and multi-wave historical analysis.</div></div>', unsafe_allow_html=True)
        st.markdown('<div class="ois-panel"><b>Designed for five layers of use</b><ul><li>SLT: school climate, trend patterns and intervention load</li><li>Grade Level Leaders: grade diagnosis, student journeys and action planning</li><li>Homeroom Teachers: homeroom picture, check-in queue and student conversations</li><li>Learning Support: access-to-learning patterns and review queue</li><li>Counsellors: pastoral/relational patterns and contextual review queue</li></ul></div>', unsafe_allow_html=True)
        interpretation_note()
        st.stop()

    try:
        history_df, schema, sheet_name = load_pass_excel(uploaded)
    except Exception as exc:
        st.error(f"Could not read this PASS export: {exc}")
        st.stop()

    latest_df = latest_snapshot(history_df)
    hero(latest_df, history_df)

    with st.sidebar:
        st.success(f"Loaded {len(history_df)} rows from '{sheet_name}'.")
        st.caption(f"Latest wave used for current analysis: **{latest_df['Wave'].iloc[0]}**")
        waves = available_waves(history_df)
        st.caption("Available waves: " + ", ".join(waves))
        st.header("2. Your view")
        access = resolve_access()
        if not access["views"]:
            st.error("Your Google account is authenticated, but no PASS dashboard role has been assigned to it.")
            st.caption("Ask the dashboard administrator to add your school email to the role configuration.")
            st.stop()
        role = access["views"][0] if len(access["views"]) == 1 else st.radio("Role", access["views"], index=0)
        if len(access["views"]) == 1:
            st.caption(f"Role: **{role}**")
        interpretation_note()
        st.caption("Views are now permission-controlled from the signed-in Google identity. HRT access is restricted to assigned homerooms; GL access can be restricted to assigned grades.")

    if role == "SLT":
        render_slt(latest_df, history_df, schema)
    elif role == "Grade Level Leader":
        render_gl(latest_df, history_df, schema, allowed_grades=access.get("grades"))
    elif role == "Homeroom Teacher":
        render_hrt(latest_df, history_df, schema, allowed_homerooms=access.get("homerooms"))
    elif role == "Learning Support":
        render_specialist(
            latest_df,
            history_df,
            schema,
            "Learning Support",
            LEARNING_SUPPORT_FACTORS,
            "identify likely barriers to accessing learning without treating PASS as SEND diagnosis.",
            "This is a review queue, not an automatic Learning Support referral list.",
        )
    else:
        render_specialist(
            latest_df,
            history_df,
            schema,
            "Counsellor",
            COUNSELLOR_FACTORS,
            "use PASS as a pastoral signal and discussion prompt, not as a mental-health assessment.",
            "A low pastoral PASS factor does not indicate a mental-health condition or safeguarding outcome on its own.",
        )


if __name__ == "__main__":
    main()
