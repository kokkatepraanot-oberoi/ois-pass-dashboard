from pathlib import Path

p = Path("app.py")
text = p.read_text()
text = text.replace(
    'longi = longitudinal_status_table(history_df, current, schema)[["Student ID", "Longitudinal status", "Concern waves (max factor)"]]',
    'longi = longitudinal_status_table(history_df, current, schema)[["Student ID", "Longitudinal status", "Repeated concern across survey waves", "PASS waves available", "Repeated concern meaning"]]',
)
old = 'profile = student_factor_profile(row, schema)\n    if factors:'
new = 'profile = student_factor_profile(row, schema)\n    profile["PASS factor"] = profile.apply(lambda r: f"Factor {int(r[\'Factor\'])} – {r[\'Factor name\']}", axis=1)\n    if factors:'
if old in text and 'profile["PASS factor"]' not in text:
    text = text.replace(old, new, 1)
text = text.replace('x="Factor name",\n        y="Percentile",', 'x="PASS factor",\n        y="Percentile",', 1)
text = text.replace(
    'st.dataframe(profile[["Factor", "Factor name", "Percentile", "Band", "Description"]], hide_index=True, use_container_width=True)',
    'st.dataframe(profile[["PASS factor", "Percentile", "Band", "Description"]], hide_index=True, use_container_width=True)',
)
p.write_text(text)
