from pathlib import Path

p = Path("app.py")
text = p.read_text()
text = text.replace('counts = sub["Domain attention"].astype(str).value_counts()', 'counts = sub["Specialist priority"].astype(str).value_counts()')
old = '    render_reading_guide(role_name)\n    metric_strip(current, extra_label="Specialist factors", extra_value=len(factors))\n    tabs = st.tabs(["Profile", "Cohort patterns", "Review queue", "How to intervene", "Student explorer"])'
new = '''    render_reading_guide(role_name)
    specialist_current = build_domain_data(current, schema, factors)
    total = len(specialist_current)
    completed = int(specialist_current["Completed PASS"].sum())
    immediate = int((specialist_current["Specialist priority"] == "Immediate review").sum())
    targeted = int((specialist_current["Specialist priority"] == "Targeted support").sum())
    metric_cols = st.columns(5)
    metric_cols[0].metric("Students", total)
    metric_cols[1].metric("PASS completed", f"{completed} ({100*completed/total:.1f}%)" if total else "0")
    metric_cols[2].metric("Specialist immediate review", immediate)
    metric_cols[3].metric("Specialist targeted support", targeted)
    metric_cols[4].metric("Factors in this specialist lens", len(factors))
    tabs = st.tabs(["Profile", "Cohort patterns", "Review queue", "How to intervene", "Student explorer"])'''
if old in text:
    text = text.replace(old, new, 1)
p.write_text(text)
