from pathlib import Path

path = Path("pass_logic.py")
text = path.read_text(encoding="utf-8")

replacements = [
    (
        '                "Current factors ≤20": len(current_concerns),\n                "Current factors ≤5": len(current_immediate),',
        '                "Current factors ≤5": len(current_immediate),\n                "Current factors ≤20": len(current_concerns),',
    ),
    (
        '                    "% ≤20": round(100 * (scores <= 20).sum() / total, 1),\n                    "% ≤5": round(100 * (scores <= 5).sum() / total, 1),',
        '                    "% ≤5": round(100 * (scores <= 5).sum() / total, 1),\n                    "% ≤20": round(100 * (scores <= 20).sum() / total, 1),',
    ),
]

changed = False
for old, new in replacements:
    if old in text:
        text = text.replace(old, new)
        changed = True

# Verify the longitudinal output is now consistently immediate-first.
wrong = '"Current factors ≤20": len(current_concerns),\n                "Current factors ≤5": len(current_immediate),'
if wrong in text:
    raise SystemExit("Longitudinal band order is still incorrect")

if changed:
    path.write_text(text, encoding="utf-8")
    print("PASS band display order updated: ≤5 before ≤20.")
else:
    print("PASS band display order already correct; no changes needed.")
