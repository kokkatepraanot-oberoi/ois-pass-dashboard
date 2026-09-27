from pathlib import Path

# PASS logic labels and repeated-concern explanation
p = Path("pass_logic.py")
text = p.read_text()
text = text.replace('f"F{n} {FACTOR_SHORT[n]}"', 'f"Factor {n} – {FACTOR_NAMES[n]}"')
text = text.replace('f"F{n} {FACTOR_NAMES[n]}"', 'f"Factor {n} – {FACTOR_NAMES[n]}"')
text = text.replace('f"F{int(row[\'Factor\'])} {row[\'Factor name\']}"', 'f"Factor {int(row[\'Factor\'])} – {row[\'Factor name\']}"')
text = text.replace('f"F{int(r[\'Factor\'])} {r[\'Factor name\']} ({r[\'% ≤20\']:.1f}% at/under 20th percentile)"', 'f"Factor {int(r[\'Factor\'])} – {r[\'Factor name\']} ({r[\'% ≤20\']:.1f}% at/under 20th percentile)"')
old = '''                "Concern waves (max factor)": max(factor_concern_waves.values(), default=0),
                "Lowest factor": row["Lowest factor"],'''
new = '''                "Concern waves (max factor)": max(factor_concern_waves.values(), default=0),
                "Repeated concern across survey waves": max(factor_concern_waves.values(), default=0),
                "PASS waves available": int(hist["Wave key"].nunique()),
                "Repeated concern meaning": (
                    f"At least one selected PASS factor scored at or below the 20th percentile in "
                    f"{max(factor_concern_waves.values(), default=0)} of {int(hist['Wave key'].nunique())} available survey waves. "
                    "This is not a count of different problems and the waves do not have to be consecutive."
                ),
                "Lowest factor": row["Lowest factor"],'''
if old in text:
    text = text.replace(old, new, 1)
p.write_text(text)

# App chart / table labels
p = Path("app.py")
text = p.read_text()
text = text.replace('plot["Label"] = plot.apply(lambda r: f"F{int(r[\'Factor\'])}", axis=1)', 'plot["Label"] = plot.apply(lambda r: f"Factor {int(r[\'Factor\'])} – {r[\'Factor name\']}", axis=1)')
text = text.replace('trend["Series"] = trend["Factor"].apply(lambda n: f"F{int(n)}")', 'trend["Series"] = trend["Factor"].apply(lambda n: f"Factor {int(n)} – {FACTOR_NAMES[int(n)]}")')
text = text.replace('f"F{item[\'factor\']} – {item[\'name\']} |', 'f"Factor {item[\'factor\']} – {item[\'name\']} |')
text = text.replace('f"**F{int(r[\'Factor\'])} {r[\'Factor name\']}**"', 'f"**Factor {int(r[\'Factor\'])} – {r[\'Factor name\']}**"')
old_table = 'display = fs[["Factor", "Factor name", "Median percentile", "% ≤5", "% ≤20", "% 21–30", "% ≥31", "Completed"]].copy()'
if old_table in text and 'display.insert(0, "PASS factor"' not in text:
    new_table = old_table + '\n    display.insert(0, "PASS factor", display.apply(lambda r: f"Factor {int(r[\'Factor\'])} – {r[\'Factor name\']}", axis=1))\n    display = display.drop(columns=["Factor", "Factor name"])'
    text = text.replace(old_table, new_table, 1)
p.write_text(text)
