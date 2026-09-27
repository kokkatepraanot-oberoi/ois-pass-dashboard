from pathlib import Path

p = Path("app.py")
text = p.read_text()
text = text.replace('out.append(f"F{factor} {name} has become a current concern over time.")', 'out.append(f"Factor {factor} – {name} has become a current concern over time.")')
text = text.replace('out.append(f"F{factor} {name} has moved into a healthier band since the earlier survey.")', 'out.append(f"Factor {factor} – {name} has moved into a healthier band since the earlier survey.")')
text = text.replace('out.append(f"F{factor} {name} has declined noticeably across the available waves.")', 'out.append(f"Factor {factor} – {name} has declined noticeably across the available waves.")')

old = '''    fig = px.bar(
        long,
        x="Factor",
        y="Students",'''
new = '''    long["PASS factor"] = long.apply(lambda r: f"Factor {int(r['Factor'])} – {r['Factor name']}", axis=1)
    fig = px.bar(
        long,
        x="PASS factor",
        y="Students",'''
if old in text:
    text = text.replace(old, new, 1)
p.write_text(text)

p = Path("pass_logic.py")
text = p.read_text()
# Remove the old ambiguous exported field now that the explicit field exists.
text = text.replace('                "Concern waves (max factor)": max(factor_concern_waves.values(), default=0),\n', '')
text = text.replace('["_rank", "Current factors ≤5", "Current factors ≤20", "Concern waves (max factor)", "Lowest percentile"]', '["_rank", "Current factors ≤5", "Current factors ≤20", "Repeated concern across survey waves", "Lowest percentile"]')
p.write_text(text)
