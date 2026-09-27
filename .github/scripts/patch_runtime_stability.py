from pathlib import Path

p = Path('app.py')
text = p.read_text()

# 1) HRT longitudinal merge: tolerate renamed/optional columns instead of hard-crashing.
old = '''        if has_history(history_df):\n            longi = longitudinal_status_table(history_df, current, schema)[["Student ID", "Longitudinal status", "Repeated concern across survey waves", "PASS waves available", "Repeated concern meaning"]]\n            queue = queue.merge(longi, on="Student ID", how="left")\n'''
new = '''        if has_history(history_df):\n            longi_raw = longitudinal_status_table(history_df, current, schema)\n            if "Repeated concern across survey waves" not in longi_raw.columns and "Concern waves (max factor)" in longi_raw.columns:\n                longi_raw["Repeated concern across survey waves"] = longi_raw["Concern waves (max factor)"]\n            long_cols = [\n                "Student ID", "Longitudinal status", "Repeated concern across survey waves",\n                "PASS waves available", "Most repeated concern factor",\n                "Repeated concern pattern", "Repeated concern meaning",\n            ]\n            longi = longi_raw.reindex(columns=long_cols)\n            queue = queue.merge(longi, on="Student ID", how="left")\n'''
if old in text:
    text = text.replace(old, new, 1)

# 2) Specialist longitudinal merge: same defensive behaviour.
old = '''        longi = longitudinal_status_table(history_df, df, schema, factors=factors)[long_cols]\n        out = out.merge(longi, on="Student ID", how="left")\n'''
new = '''        longi_raw = longitudinal_status_table(history_df, df, schema, factors=factors)\n        if "Repeated concern across survey waves" not in longi_raw.columns and "Concern waves (max factor)" in longi_raw.columns:\n            longi_raw["Repeated concern across survey waves"] = longi_raw["Concern waves (max factor)"]\n        longi = longi_raw.reindex(columns=long_cols)\n        out = out.merge(longi, on="Student ID", how="left")\n'''
if old in text:
    text = text.replace(old, new, 1)

# 3) Student explorer: always reconstruct safe identity columns if a transformed frame loses them.
old = '''def show_student_profile(current_df: pd.DataFrame, history_df: pd.DataFrame, schema, key_prefix: str, factors: List[int] | None = None) -> None:\n    completed_sub = current_df[current_df["Completed PASS"]].copy()\n    if completed_sub.empty:\n        st.info("No completed student profiles in this selection.")\n        return\n    options = completed_sub[["Student", "Student ID"]].drop_duplicates().sort_values("Student")\n    display_names = options["Student"].tolist()\n    mapping = dict(zip(options["Student"], options["Student ID"]))\n    selected_name = st.selectbox("Select student", display_names, key=f"{key_prefix}_student")\n'''
new = '''def show_student_profile(current_df: pd.DataFrame, history_df: pd.DataFrame, schema, key_prefix: str, factors: List[int] | None = None) -> None:\n    completed_sub = current_df.copy()\n    if "Completed PASS" in completed_sub.columns:\n        completed_sub = completed_sub[completed_sub["Completed PASS"]].copy()\n    if completed_sub.empty:\n        st.info("No completed student profiles in this selection.")\n        return\n    if "Student" not in completed_sub.columns:\n        if schema.forename in completed_sub.columns and schema.surname in completed_sub.columns:\n            completed_sub["Student"] = (\n                completed_sub[schema.forename].fillna("").astype(str).str.strip()\n                + " "\n                + completed_sub[schema.surname].fillna("").astype(str).str.strip()\n            ).str.strip()\n        else:\n            st.warning("Student names are not available in this view.")\n            return\n    if "Student ID" not in completed_sub.columns:\n        if getattr(schema, "unique_id", "") and schema.unique_id in completed_sub.columns:\n            completed_sub["Student ID"] = completed_sub[schema.unique_id].fillna("").astype(str).str.strip()\n        else:\n            completed_sub["Student ID"] = completed_sub["Student"]\n    options = completed_sub.reindex(columns=["Student", "Student ID"]).dropna(subset=["Student"]).drop_duplicates().sort_values("Student")\n    if options.empty:\n        st.info("No student profiles are available in this selection.")\n        return\n    display_names = options["Student"].astype(str).tolist()\n    mapping = dict(zip(options["Student"].astype(str), options["Student ID"].astype(str)))\n    selected_name = st.selectbox("Select student", display_names, key=f"profile_{key_prefix}_student")\n'''
if old in text:
    text = text.replace(old, new, 1)

# 4) Any old session-based intervention tracker labels should not imply production persistence.
text = text.replace('**Intervention tracker (session-based)**', '**Intervention planning workspace**')
text = text.replace("This tracker is session-based in Streamlit. For long-term storage, export the CSV and keep it in the school's protected workflow.", "Use this as a temporary planning workspace until persistent OIS storage is connected.")

p.write_text(text)
