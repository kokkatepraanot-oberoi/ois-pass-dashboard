from pathlib import Path
import re

p = Path("app.py")
text = p.read_text()

new_specialist = r'''def render_specialist(latest_df: pd.DataFrame, history_df: pd.DataFrame, schema, role_name: str, factors: List[int], intro: str, queue_caption: str) -> None:
    grades = sorted(latest_df["Grade"].dropna().astype(str).unique().tolist())
    scope = st.selectbox("Scope", ["Whole Middle School", *grades], key=f"scope_{role_name}")
    current = latest_df.copy() if scope == "Whole Middle School" else latest_df[latest_df["Grade"] == scope].copy()
    history = history_df.copy() if scope == "Whole Middle School" else history_df[history_df["Grade"] == scope].copy()
    st.markdown(f'<div class="ois-callout"><b>{role_name}:</b> {intro}</div>', unsafe_allow_html=True)
    render_reading_guide(role_name)
    metric_strip(current, extra_label="Specialist factors", extra_value=len(factors))
    tabs = st.tabs(["Profile", "Cohort patterns", "Review queue", "How to intervene", "Student explorer"])

    with tabs[0]:
        fs = factor_summary(current, schema)
        fs = fs[fs["Factor"].isin(factors)]
        factor_chart(fs, f"{scope}: {role_name} factor profile")
        factor_table(fs)
        st.markdown("**Specialist factors in this view:** " + "; ".join(factor_label(n) for n in factors))

    with tabs[1]:
        group_col = "Grade" if scope == "Whole Middle School" else "Homeroom"
        summary = specialist_summary(current, schema, factors, group_col)
        attention_chart(summary, group_col, f"{scope}: {role_name} review profile by {group_col.lower()}")
        st.dataframe(summary, hide_index=True, use_container_width=True)
        if has_history(history_df):
            trend_title = "Whole Middle School: specialist trend over time" if scope == "Whole Middle School" else f"Current {scope} cohort: specialist PASS journey over time"
            trend_line_chart(history, schema, trend_title, factors=factors)
            if scope != "Whole Middle School":
                st.caption("* Earlier year labels are inferred from the student's current year and survey date. Testwise stamps current year/group labels onto historical rows, so earlier points may be Primary results for current Year 6 students.")

    with tabs[2]:
        queue = specialist_priority_table(current, schema, factors, history_df if has_history(history_df) else None)
        queue = queue[queue["Specialist priority"].isin(["Immediate review", "Targeted support", "Monitor"])].copy()
        st.markdown("#### Review queue")
        st.caption("Read the named factor columns first. The counts are secondary. A student appears here because at least one factor relevant to this specialist role is in an intervention/watch band.")
        filter_priority = st.multiselect(
            "Show priorities",
            ["Immediate review", "Targeted support", "Monitor"],
            default=["Immediate review", "Targeted support", "Monitor"],
            key=f"specialist_filter_{role_name}",
        )
        display_queue = queue[queue["Specialist priority"].isin(filter_priority)].copy()
        preferred = [
            "Student", "Student ID", "Grade", "Homeroom", "Specialist priority",
            "Immediate concern factors (≤5th percentile)",
            "Targeted concern factors (6th–20th percentile)",
            "Watch factors (21st–30th percentile)",
            "Why this is a concern", "Longitudinal status",
            "Repeated concern across survey waves", "PASS waves available", "Repeated concern meaning",
        ]
        st.dataframe(display_queue[[c for c in preferred if c in display_queue.columns]], hide_index=True, use_container_width=True)
        downloadable_csv(display_queue, f"Download {role_name} review queue", f"{role_name.lower().replace(' ', '_')}_review_queue.csv", f"{role_name}_dl")
        st.caption(queue_caption)

    with tabs[3]:
        render_intervention_guidance(role_name)
        st.divider()
        st.markdown("### Put the intervention into action")
        queue_for_actions = specialist_priority_table(current, schema, factors, history_df if has_history(history_df) else None)
        queue_for_actions = queue_for_actions[queue_for_actions["Specialist priority"].isin(["Immediate review", "Targeted support", "Monitor"])].copy()
        persistent_action_manager(
            queue_for_actions,
            role_name,
            f"{role_name} | {scope}",
            role_name.lower().replace(" ", "_"),
            schema,
            factors=factors,
            latest_wave=current["Wave"].iloc[0],
        )

    with tabs[4]:
        show_student_profile(current, history_df if has_history(history_df) else current, schema, role_name.lower().replace(' ', '_'), factors=factors)'''

pattern = r"def render_specialist\(.*?\n\ndef main\(\) -> None:"
if not re.search(pattern, text, flags=re.S):
    raise SystemExit("render_specialist block not found")
text = re.sub(pattern, new_specialist + "\n\ndef main() -> None:", text, count=1, flags=re.S)
p.write_text(text)
