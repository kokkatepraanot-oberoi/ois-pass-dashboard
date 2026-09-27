from pathlib import Path

p = Path("pass_logic.py")
text = p.read_text()
old = '''                "Repeated concern across survey waves": max(factor_concern_waves.values(), default=0),
                "PASS waves available": int(hist["Wave key"].nunique()),
                "Repeated concern meaning": (
                    f"At least one selected PASS factor scored at or below the 20th percentile in "
                    f"{max(factor_concern_waves.values(), default=0)} of {int(hist['Wave key'].nunique())} available survey waves. "
                    "This is not a count of different problems and the waves do not have to be consecutive."
                ),'''
new = '''                "Repeated concern across survey waves": max(factor_concern_waves.values(), default=0),
                "PASS waves available": int(hist["Wave key"].nunique()),
                "Most repeated concern factor": (
                    f"Factor {max(factor_concern_waves, key=factor_concern_waves.get)} – {FACTOR_NAMES[max(factor_concern_waves, key=factor_concern_waves.get)]}"
                    if factor_concern_waves else ""
                ),
                "Repeated concern pattern": (
                    f"Factor {max(factor_concern_waves, key=factor_concern_waves.get)} – {FACTOR_NAMES[max(factor_concern_waves, key=factor_concern_waves.get)]}: "
                    f"at or below the 20th percentile in {max(factor_concern_waves.values(), default=0)} of {int(hist['Wave key'].nunique())} available PASS waves."
                    if factor_concern_waves else "No repeated concern history available."
                ),
                "Repeated concern meaning": (
                    f"At least one selected PASS factor scored at or below the 20th percentile in "
                    f"{max(factor_concern_waves.values(), default=0)} of {int(hist['Wave key'].nunique())} available survey waves. "
                    "This is not a count of different problems and the waves do not have to be consecutive."
                ),'''
if old not in text:
    raise SystemExit("Repeated concern block not found")
text = text.replace(old, new, 1)
p.write_text(text)

p = Path("app.py")
text = p.read_text()
old_cols = '''            "Student ID", "Longitudinal status", "Repeated concern across survey waves",
            "PASS waves available", "Repeated concern meaning", "Chronic factors",'''
new_cols = '''            "Student ID", "Longitudinal status", "Repeated concern across survey waves",
            "PASS waves available", "Most repeated concern factor", "Repeated concern pattern", "Repeated concern meaning", "Chronic factors",'''
if old_cols in text:
    text = text.replace(old_cols, new_cols, 1)
old_display = '''            "Why this is a concern", "Longitudinal status",
            "Repeated concern across survey waves", "PASS waves available", "Repeated concern meaning",'''
new_display = '''            "Why this is a concern", "Longitudinal status",
            "Most repeated concern factor", "Repeated concern pattern", "Repeated concern meaning",'''
if old_display in text:
    text = text.replace(old_display, new_display, 1)
p.write_text(text)
