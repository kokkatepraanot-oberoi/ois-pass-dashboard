from pathlib import Path

p = Path('app.py')
text = p.read_text()

old_css = '''        div.stTabs [data-baseweb="tab-list"] {\n            gap: 0.55rem;\n            background: rgba(255,255,255,0.48);\n            padding: .4rem;\n            border-radius: 18px;\n            border: 1px solid rgba(255,255,255,.66);\n            backdrop-filter: blur(16px);\n        }\n        div.stTabs [data-baseweb="tab"] {\n            height: 44px;\n            border-radius: 14px;\n            background: rgba(255,255,255,0.26);\n            padding: 0 18px;\n            color: #4b5563;\n            font-weight: 600;\n        }\n        div.stTabs [aria-selected="true"] {\n            background: linear-gradient(180deg, rgba(255,255,255,0.95), rgba(243,247,255,0.82));\n            color: #0f172a;\n            box-shadow: 0 6px 16px rgba(0,122,255,0.12);\n        }\n'''

new_css = '''        .ois-nav-label {\n            display:flex; align-items:center; gap:.55rem;\n            margin: .95rem 0 .45rem 0;\n            color:#334155; font-size:.78rem; font-weight:800;\n            letter-spacing:.08em; text-transform:uppercase;\n        }\n        .ois-nav-label::before {\n            content:""; width:8px; height:8px; border-radius:999px;\n            background:linear-gradient(135deg,#007aff,#5ac8fa);\n            box-shadow:0 0 0 5px rgba(0,122,255,.10);\n        }\n        div.stTabs [data-baseweb="tab-list"] {\n            gap: .7rem;\n            background: rgba(241,245,249,.72);\n            padding: .55rem;\n            border-radius: 22px;\n            border: 1px solid rgba(148,163,184,.22);\n            box-shadow: inset 0 1px 0 rgba(255,255,255,.88), 0 10px 30px rgba(15,23,42,.06);\n            backdrop-filter: blur(20px);\n            overflow-x:auto;\n            scrollbar-width: thin;\n        }\n        div.stTabs [data-baseweb="tab"] {\n            min-height: 54px;\n            min-width: 145px;\n            border-radius: 16px;\n            background: rgba(255,255,255,.82);\n            border: 1px solid rgba(148,163,184,.24);\n            padding: 0 18px;\n            color: #334155;\n            font-weight: 700;\n            font-size: .92rem;\n            box-shadow: 0 5px 14px rgba(15,23,42,.05);\n            transition: transform .16s ease, box-shadow .16s ease, border-color .16s ease, background .16s ease;\n            white-space: nowrap;\n        }\n        div.stTabs [data-baseweb="tab"]:hover {\n            transform: translateY(-1px);\n            border-color: rgba(0,122,255,.30);\n            box-shadow: 0 8px 20px rgba(15,23,42,.09);\n            background: rgba(255,255,255,.98);\n        }\n        div.stTabs [aria-selected="true"] {\n            background: linear-gradient(135deg, #007aff 0%, #3998ff 100%) !important;\n            color: #ffffff !important;\n            border-color: rgba(0,122,255,.75) !important;\n            box-shadow: 0 10px 24px rgba(0,122,255,.26) !important;\n            transform: translateY(-1px);\n        }\n        div.stTabs [aria-selected="true"] p,\n        div.stTabs [aria-selected="true"] span {color:#ffffff !important;}\n        div.stTabs [data-baseweb="tab-highlight"] {display:none;}\n        div.stTabs [data-baseweb="tab-border"] {display:none;}\n'''

if old_css in text:
    text = text.replace(old_css, new_css, 1)
else:
    # Idempotence: only fail when the upgraded styles are absent.
    if '.ois-nav-label' not in text:
        raise SystemExit('Could not find the existing tab CSS block to upgrade.')

replacements = {
'''    tabs = st.tabs(["School picture", "Trends over time", "Emerging vs persistent", "Grade comparison", "Homeroom variation", "Intervention priorities"])''':
'''    st.markdown('<div class="ois-nav-label">Navigate this SLT view</div>', unsafe_allow_html=True)\n    tabs = st.tabs(["🏫 School picture", "📈 Trends over time", "🔁 Emerging & persistent", "🎓 Grade comparison", "👥 Homeroom variation", "🎯 Intervention priorities"])''',
'''    tabs = st.tabs(["Current picture", "Trends over time", "Student journey table", "Homerooms", "Intervention planner", "Student explorer"])''':
'''    st.markdown('<div class="ois-nav-label">Navigate this grade view</div>', unsafe_allow_html=True)\n    tabs = st.tabs(["📊 Current picture", "📈 Trends over time", "🧭 Student journeys", "🏫 Homerooms", "🎯 Intervention planner", "👤 Student explorer"])''',
'''    tabs = st.tabs(["My homeroom", "Student journey", "Check-in queue", "Interventions", "Student explorer"])''':
'''    st.markdown('<div class="ois-nav-label">Navigate your homeroom workflow</div>', unsafe_allow_html=True)\n    tabs = st.tabs(["🏠 My homeroom", "🧭 Student journey", "💬 Check-in queue", "🛠 Interventions", "👤 Student explorer"])''',
'''    tabs = st.tabs(["Profile", "Cohort patterns", "Review queue", "How to intervene", "Student explorer"])''':
'''    st.markdown(f'<div class="ois-nav-label">Navigate the {role_name} workflow</div>', unsafe_allow_html=True)\n    tabs = st.tabs(["📊 Profile", "👥 Cohort patterns", "📋 Review queue", "🛠 How to intervene", "👤 Student explorer"])''',
}

for old, new in replacements.items():
    if old in text:
        text = text.replace(old, new, 1)
    elif new not in text:
        raise SystemExit(f'Could not find navigation block: {old[:60]}...')

old_mobile = '''            div.stTabs [data-baseweb="tab-list"] {overflow-x: auto; flex-wrap: nowrap;}\n            div.stTabs [data-baseweb="tab"] {padding: 0 12px; white-space: nowrap;}\n'''
new_mobile = '''            div.stTabs [data-baseweb="tab-list"] {overflow-x: auto; flex-wrap: nowrap; gap:.45rem; padding:.45rem;}\n            div.stTabs [data-baseweb="tab"] {padding: 0 13px; white-space: nowrap; min-width: 132px; min-height:50px; font-size:.86rem;}\n            .ois-nav-label {margin-top:.75rem;}\n'''
if old_mobile in text:
    text = text.replace(old_mobile, new_mobile, 1)

p.write_text(text)
