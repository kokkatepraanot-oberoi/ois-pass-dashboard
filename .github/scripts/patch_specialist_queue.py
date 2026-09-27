from pathlib import Path
import re

p = Path("app.py")
text = p.read_text()

# Import explicit specialist helpers.
if "from specialist_guidance import (" not in text:
    marker = "\n\n\nst.set_page_config("
    insertion = '''\n\nfrom specialist_guidance import (\n    factor_label,\n    render_intervention_guidance,\n    render_reading_guide,\n)\n\n\nst.set_page_config('''
    if marker not in text:
        raise SystemExit("Could not find set_page_config marker")
    text = text.replace(marker, insertion, 1)

new_build = r'''def build_domain_data(df: pd.DataFrame, schema, factors: List[int]) -> pd.DataFrame:
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

    def factor_list(row, lower, upper):
        values = []
        for number in factors:
            value = row[schema.factor_cols[number]]
            if pd.isna(value):
                continue
            if lower <= float(value) <= upper:
                values.append(f"{factor_label(number)} (percentile {float(value):.1f})")
        return "; ".join(values)

    out["Specialist priority"] = out.apply(domain_attention, axis=1)
    out["Immediate concern factors (≤5th percentile)"] = out.apply(lambda r: factor_list(r, 0, 5), axis=1)
    out["Targeted concern factors (6th–20th percentile)"] = out.apply(lambda r: factor_list(r, 6, 20), axis=1)
    out["Watch factors (21st–30th percentile)"] = out.apply(lambda r: factor_list(r, 21, 30), axis=1)
    out["Number of immediate concern factors"] = out[cols].apply(lambda row: int((row <= 5).sum()) if row.notna().all() else 0, axis=1)
    out["Number of concern factors (≤20th)"] = out[cols].apply(lambda row: int((row <= 20).sum()) if row.notna().all() else 0, axis=1)
    out["Number of watch factors (21st–30th)"] = out[cols].apply(lambda row: int(((row >= 21) & (row <= 30)).sum()) if row.notna().all() else 0, axis=1)
    out["Lowest relevant percentile"] = out[cols].min(axis=1, skipna=True)

    def why(row):
        status = row["Specialist priority"]
        if status == "Immediate review":
            return "At least one specialist-relevant factor is at or below the 5th percentile. Review promptly and triangulate with other evidence."
        if status == "Targeted support":
            return "At least one specialist-relevant factor is between the 6th and 20th percentile. A planned check-in/support response may be appropriate."
        if status == "Monitor":
            return "No specialist factor is ≤20, but at least one is in the 21st–30th percentile watch band. Monitor and use other evidence before intervening."
        if status == "Generally positive":
            return "All specialist-relevant factors are at or above the 31st percentile in the latest PASS wave."
        return "PASS was not completed in the latest wave."

    out["Why this is a concern"] = out.apply(why, axis=1)
    return out'''
pattern = r"def build_domain_data\(.*?\n\ndef specialist_summary"
if not re.search(pattern, text, flags=re.S):
    raise SystemExit("build_domain_data block not found")
text = re.sub(pattern, new_build + "\n\ndef specialist_summary", text, count=1, flags=re.S)

new_priority = r'''def specialist_priority_table(df: pd.DataFrame, schema, factors: List[int], history_df: pd.DataFrame | None = None) -> pd.DataFrame:
    working = build_domain_data(df, schema, factors)
    cols = [
        "Student", "Student ID", "Grade", "Homeroom", "Specialist priority",
        "Immediate concern factors (≤5th percentile)",
        "Targeted concern factors (6th–20th percentile)",
        "Watch factors (21st–30th percentile)",
        "Number of immediate concern factors",
        "Number of concern factors (≤20th)",
        "Number of watch factors (21st–30th)",
        "Lowest relevant percentile", "Why this is a concern", "Attention",
    ]
    out = working[cols].copy()
    if history_df is not None and has_history(history_df):
        long_cols = [
            "Student ID", "Longitudinal status", "Repeated concern across survey waves",
            "PASS waves available", "Repeated concern meaning", "Chronic factors",
            "Persistent factors", "New factors", "Recovered factors", "Deteriorating factors",
        ]
        longi = longitudinal_status_table(history_df, df, schema, factors=factors)[long_cols]
        out = out.merge(longi, on="Student ID", how="left")
    rank = {v: i for i, v in enumerate(ATTENTION_ORDER)}
    out["_rank"] = out["Specialist priority"].map(rank).fillna(99)
    return out.sort_values(
        ["_rank", "Number of immediate concern factors", "Number of concern factors (≤20th)", "Lowest relevant percentile"],
        ascending=[True, False, False, True],
    ).drop(columns="_rank")'''
pattern = r"def specialist_priority_table\(.*?\n\ndef intervention_tracker"
if not re.search(pattern, text, flags=re.S):
    raise SystemExit("specialist_priority_table block not found")
text = re.sub(pattern, new_priority + "\n\ndef intervention_tracker", text, count=1, flags=re.S)

p.write_text(text)
