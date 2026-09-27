from pathlib import Path

p = Path("app.py")
text = p.read_text()

if "from persistent_actions import render_action_manager" not in text:
    marker = "\n\n\nst.set_page_config("
    insertion = "\n\nfrom persistent_actions import render_action_manager\n\n\nst.set_page_config("
    if marker not in text:
        raise SystemExit("set_page_config marker not found")
    text = text.replace(marker, insertion, 1)

text = text.replace(
    'intervention_tracker("SLT", "slt")',
    'render_action_manager(pd.DataFrame(), "SLT", "Whole Middle School", "slt", schema, latest_wave=latest_df["Wave"].iloc[0])',
)
text = text.replace(
    'intervention_tracker(grade, f"gl_{grade.replace(\' \', \'_\')}")\n        workflow_editor(focus, f"gl_{grade.replace(\' \', \'_\')}", "Student intervention / review log")',
    'render_action_manager(focus, "Grade Level Leader", grade, f"gl_{grade.replace(\' \', \'_\')}", schema, latest_wave=current["Wave"].iloc[0])',
)
text = text.replace(
    'intervention_tracker(homeroom, f"hrt_{homeroom}")\n        workflow_editor(queue if \'queue\' in locals() else student_priority_table(current), f"hrt_{homeroom}", "HRT check-in / review log")',
    'render_action_manager(queue if \'queue\' in locals() else student_priority_table(current), "Homeroom Teacher", homeroom, f"hrt_{homeroom}", schema, latest_wave=current["Wave"].iloc[0])',
)

# Specialist render patch uses this name.
text = text.replace("persistent_action_manager(", "render_action_manager(")

p.write_text(text)
