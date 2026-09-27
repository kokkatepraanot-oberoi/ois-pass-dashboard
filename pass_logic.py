from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import pandas as pd


FACTOR_NAMES: Dict[int, str] = {
    1: "Feelings about school",
    2: "Perceived learning capability",
    3: "Self-regard as a learner",
    4: "Preparedness for learning",
    5: "Attitudes to teachers",
    6: "General work ethic",
    7: "Confidence in learning",
    8: "Attitudes to attendance",
    9: "Response to curriculum demands",
}

FACTOR_SHORT: Dict[int, str] = {
    1: "School feelings",
    2: "Learning capability",
    3: "Learner self-regard",
    4: "Preparedness",
    5: "Teachers",
    6: "Work ethic",
    7: "Learning confidence",
    8: "Attendance",
    9: "Curriculum demands",
}

FACTOR_DESCRIPTIONS: Dict[int, str] = {
    1: "Sense of wellbeing, safety and comfort in school.",
    2: "How positive and successful students feel about their capabilities as learners.",
    3: "How learning affects the student's wider concept of self.",
    4: "Perceptions of behaviour, organisation and attitude in learning situations, including metacognitive skills.",
    5: "Perceptions of relationships with teachers.",
    6: "Attitudes and responses to work in general.",
    7: "Confidence, perseverance and feelings when approaching challenging learning.",
    8: "Attitudes towards attending school.",
    9: "Perceptions of whether the level and demands of learning feel appropriate.",
}

# OIS-created responses. Not copied from GL's intervention bank.
INTERVENTIONS: Dict[int, Dict[str, List[str] | str]] = {
    1: {
        "focus": "Belonging, safety and connection",
        "universal": [
            "Strengthen predictable homeroom routines and visible adult presence at transition points.",
            "Use short belonging check-ins and make help-seeking routes explicit to all students.",
        ],
        "targeted": [
            "Identify one trusted adult and one safe peer connection for the student.",
            "Map when/where school feels least comfortable: arrival, break, transitions, a particular lesson or social setting.",
        ],
        "questions": [
            "When during the school day do you feel most comfortable? Least comfortable?",
            "Who in school would you go to if something felt difficult?",
        ],
    },
    2: {
        "focus": "Belief in learning capability",
        "universal": [
            "Make success criteria and examples of quality explicit before independent work.",
            "Use feedback that names effective strategies, not fixed ability.",
        ],
        "targeted": [
            "Set one short mastery goal and collect evidence of progress over 2–3 weeks.",
            "Pre-teach or rehearse the first step of difficult tasks so the student can start successfully.",
        ],
        "questions": [
            "Which subjects make you feel capable? What is different there?",
            "What usually happens in your head when work looks difficult?",
        ],
    },
    3: {
        "focus": "Learner self-regard",
        "universal": [
            "Normalise mistakes and revision as part of strong learning.",
            "Reduce public comparison and create regular opportunities for private reflection on growth.",
        ],
        "targeted": [
            "Use a strengths-and-evidence conversation: name a strength and identify where it has been demonstrated.",
            "Create a small achievable goal that can be completed and reviewed quickly.",
        ],
        "questions": [
            "What are you proud of as a learner this term?",
            "What would make you feel more successful in class?",
        ],
    },
    4: {
        "focus": "Preparedness and learning routines",
        "universal": [
            "Make lesson-start routines consistent: equipment, first task, deadlines and success criteria.",
            "Teach planning, checking and reflection explicitly rather than assuming students already use these skills.",
        ],
        "targeted": [
            "Use a simple checklist for equipment, task-start and submission until the routine becomes independent.",
            "Agree one organisation habit to monitor for two weeks rather than trying to fix everything at once.",
        ],
        "questions": [
            "What usually gets in the way of being ready to learn?",
            "Which routine would make the biggest difference this week?",
        ],
    },
    5: {
        "focus": "Student–teacher relationships",
        "universal": [
            "Tighten consistency around expectations, correction and follow-through across the team.",
            "Build deliberate positive contact so interactions are not dominated by correction or task compliance.",
        ],
        "targeted": [
            "Use a short restorative/relationship-repair conversation with the relevant adult where appropriate.",
            "Identify whether the concern is general or linked to one subject, adult, communication style or recent event.",
        ],
        "questions": [
            "In which lessons do you feel most understood by the teacher?",
            "What do adults do that helps you respond well? What makes it harder?",
        ],
    },
    6: {
        "focus": "Work ethic, task initiation and persistence",
        "universal": [
            "Break longer tasks into visible milestones with short feedback loops.",
            "Make completion expectations explicit and celebrate sustained effort, not just finished products.",
        ],
        "targeted": [
            "Set a specific task-start cue and a short first work interval, then review completion.",
            "Check whether low engagement is linked to difficulty, relevance, organisation, fatigue or peer distraction before choosing an intervention.",
        ],
        "questions": [
            "Which type of work is easiest for you to start? Which is hardest?",
            "What helps you keep going when a task takes longer than expected?",
        ],
    },
    7: {
        "focus": "Confidence and resilience in learning",
        "universal": [
            "Use low-stakes practice before public performance or graded tasks.",
            "Model how to respond when stuck and make help-seeking a normal learning behaviour.",
        ],
        "targeted": [
            "Use graduated challenge: secure an accessible first step, then increase difficulty deliberately.",
            "Check whether avoidance is linked to anxiety, fear of failure, previous experience or an actual skill gap.",
        ],
        "questions": [
            "What do you do when you are not sure of an answer?",
            "What would make difficult work feel safer to attempt?",
        ],
    },
    8: {
        "focus": "Attendance and connection to school",
        "universal": [
            "Reinforce predictable arrival routines and a positive start to the day.",
            "Ensure students know that attendance concerns are discussed supportively and early.",
        ],
        "targeted": [
            "Explore the barrier before assuming motivation: transport, sleep, anxiety, relationships, workload, health or family circumstances.",
            "Agree a named adult check-in at arrival and review the pattern alongside actual attendance data.",
        ],
        "questions": [
            "What makes coming to school easier or harder on different days?",
            "Is there a particular day, lesson or situation you find yourself wanting to avoid?",
        ],
    },
    9: {
        "focus": "Fit between student and curriculum demands",
        "universal": [
            "Check clarity, workload, pacing and scaffolding across subjects rather than assuming the issue is ability.",
            "Use examples, chunking and retrieval/practice routines to reduce unnecessary cognitive load.",
        ],
        "targeted": [
            "Explore whether learning feels too difficult, too easy, unclear, overwhelming or disconnected from prior knowledge.",
            "Compare the PASS concern with subject attainment and teacher observations before changing challenge level.",
        ],
        "questions": [
            "Where does schoolwork feel best matched to you? Where does it feel badly matched?",
            "When work feels difficult, is the main issue the content, amount, pace, instructions or something else?",
        ],
    },
}

BAND_ORDER = ["Low", "Low-moderate", "Moderate", "High"]
ATTENTION_ORDER = ["Immediate review", "Targeted support", "Monitor", "Generally positive", "Not completed"]
LONGITUDINAL_ORDER = ["New concern", "Persistent concern", "Chronic concern", "Recovered", "Watch deterioration", "Stable positive", "Insufficient history"]


@dataclass(frozen=True)
class Schema:
    factor_cols: Dict[int, str]
    forename: str
    surname: str
    grade: str
    group: str
    survey_date: str
    unique_id: str


def factor_band(value: float | int | None) -> str:
    if pd.isna(value):
        return "Missing"
    value = float(value)
    if value <= 5:
        return "Low"
    if value <= 20:
        return "Low-moderate"
    if value <= 30:
        return "Moderate"
    return "High"


def detect_schema(df: pd.DataFrame) -> Schema:
    missing_core = [c for c in ["Forename", "Surname", "Current Year", "Group"] if c not in df.columns]
    if missing_core:
        raise ValueError("Missing required column(s): " + ", ".join(missing_core))

    factor_cols: Dict[int, str] = {}
    for n in range(1, 10):
        matches = [c for c in df.columns if f"Factor {n}" in str(c) and "Percentile" in str(c)]
        if not matches:
            raise ValueError(f"Could not find PASS Factor {n} percentile column.")
        factor_cols[n] = matches[0]

    survey_date = "PASS - Date of Survey" if "PASS - Date of Survey" in df.columns else ""
    unique_id = "TW Unique ID" if "TW Unique ID" in df.columns else ""
    return Schema(
        factor_cols=factor_cols,
        forename="Forename",
        surname="Surname",
        grade="Current Year",
        group="Group",
        survey_date=survey_date,
        unique_id=unique_id,
    )


def _format_group(value) -> str:
    if pd.isna(value):
        return "Unknown"
    try:
        as_float = float(value)
        if as_float.is_integer():
            return str(int(as_float))
        return f"{as_float:.1f}".rstrip("0").rstrip(".")
    except Exception:
        return str(value).strip()


def load_pass_excel(uploaded_file) -> Tuple[pd.DataFrame, Schema, str]:
    book = pd.ExcelFile(uploaded_file)
    sheet_name = "StudentData" if "StudentData" in book.sheet_names else book.sheet_names[0]
    df = pd.read_excel(book, sheet_name=sheet_name)
    schema = detect_schema(df)
    clean = prepare_data(df, schema)
    return clean, schema, sheet_name


def prepare_data(df: pd.DataFrame, schema: Schema) -> pd.DataFrame:
    out = df.copy()
    out["Student"] = (
        out[schema.forename].fillna("").astype(str).str.strip()
        + " "
        + out[schema.surname].fillna("").astype(str).str.strip()
    ).str.strip()
    out["Grade"] = out[schema.grade].fillna("Unknown").astype(str).str.strip()
    out["Homeroom"] = out[schema.group].apply(_format_group)
    if schema.unique_id and schema.unique_id in out.columns:
        out["Student ID"] = out[schema.unique_id].fillna("").astype(str).str.strip()
    else:
        out["Student ID"] = out["Student"]

    if schema.survey_date and schema.survey_date in out.columns:
        out["Survey date"] = pd.to_datetime(out[schema.survey_date], errors="coerce")
    else:
        out["Survey date"] = pd.NaT
    if out["Survey date"].isna().all():
        out["Survey date"] = pd.Timestamp.today().normalize()
    out["Wave sort"] = out["Survey date"].fillna(pd.Timestamp.today().normalize())

    # Testwise exports can contain late completions several weeks after the main
    # administration date. Treat dates separated by <=60 days as one survey wave
    # so late March/April or September/October completions do not become fake waves.
    unique_dates = sorted(pd.Timestamp(d).normalize() for d in out["Wave sort"].dropna().unique())
    date_to_wave = {}
    wave_start = None
    previous_date = None
    for date in unique_dates:
        if previous_date is None or (date - previous_date).days > 60:
            wave_start = date
        date_to_wave[date] = wave_start
        previous_date = date
    out["Wave key"] = out["Wave sort"].dt.normalize().map(date_to_wave)
    out["Wave"] = pd.to_datetime(out["Wave key"]).dt.strftime("%b %Y")

    # Testwise applies the student's CURRENT year/group to historical rows.
    # Infer the year the student would have been in at each survey wave so
    # cohort trend charts do not imply, for example, that a current Year 6
    # student was already in Year 6 in 2024. This is an inferred progression
    # based on academic-year movement and is labelled as such in the UI.
    current_grade_num = pd.to_numeric(out["Grade"].str.extract(r"(\d+)")[0], errors="coerce")
    wave_dates = pd.to_datetime(out["Wave key"], errors="coerce")
    latest_wave_date = wave_dates.max()
    if pd.notna(latest_wave_date):
        latest_ay_start = latest_wave_date.year if latest_wave_date.month >= 7 else latest_wave_date.year - 1
        wave_ay_start = wave_dates.dt.year.where(wave_dates.dt.month >= 7, wave_dates.dt.year - 1)
        inferred_grade_num = current_grade_num - (latest_ay_start - wave_ay_start)
        out["Grade at survey (inferred)"] = inferred_grade_num.apply(
            lambda value: f"Year {int(value)}" if pd.notna(value) and value >= 1 else "Unknown"
        )
    else:
        out["Grade at survey (inferred)"] = "Unknown"

    factor_columns = list(schema.factor_cols.values())
    for c in factor_columns:
        out[c] = pd.to_numeric(out[c], errors="coerce")

    out["Completed PASS"] = out[factor_columns].notna().all(axis=1)
    out["Immediate count"] = out[factor_columns].apply(lambda row: int((row <= 5).sum()) if row.notna().all() else 0, axis=1)
    out["Concern count"] = out[factor_columns].apply(lambda row: int((row <= 20).sum()) if row.notna().all() else 0, axis=1)
    out["Moderate count"] = out[factor_columns].apply(lambda row: int(((row >= 21) & (row <= 30)).sum()) if row.notna().all() else 0, axis=1)
    out["Lowest percentile"] = out[factor_columns].min(axis=1, skipna=True)

    def attention(row) -> str:
        if not bool(row["Completed PASS"]):
            return "Not completed"
        vals = row[factor_columns]
        if (vals <= 5).any():
            return "Immediate review"
        if (vals <= 20).any():
            return "Targeted support"
        if (vals <= 30).any():
            return "Monitor"
        return "Generally positive"

    out["Attention"] = out.apply(attention, axis=1)
    out["Attention"] = pd.Categorical(out["Attention"], categories=ATTENTION_ORDER, ordered=True)

    def factors_in_range(row, low: float | None, high: float) -> str:
        names = []
        for n, col in schema.factor_cols.items():
            val = row[col]
            if pd.isna(val):
                continue
            if low is None and val <= high:
                names.append(f"Factor {n} – {FACTOR_NAMES[n]}")
            elif low is not None and low <= val <= high:
                names.append(f"Factor {n} – {FACTOR_NAMES[n]}")
        return "; ".join(names)

    out["Bottom 5% factors"] = out.apply(lambda r: factors_in_range(r, None, 5), axis=1)
    out["≤20th percentile factors"] = out.apply(lambda r: factors_in_range(r, None, 20), axis=1)
    out["21–30th percentile factors"] = out.apply(lambda r: factors_in_range(r, 21, 30), axis=1)

    def lowest_factor(row) -> str:
        vals = {n: row[col] for n, col in schema.factor_cols.items() if not pd.isna(row[col])}
        if not vals:
            return ""
        n = min(vals, key=vals.get)
        return f"Factor {n} – {FACTOR_NAMES[n]}"

    out["Lowest factor"] = out.apply(lowest_factor, axis=1)
    return out


def available_waves(df: pd.DataFrame) -> List[str]:
    waves = (
        df[["Wave", "Wave key"]]
        .drop_duplicates(subset=["Wave"])
        .sort_values("Wave key")
    )
    return waves["Wave"].tolist()


def latest_snapshot(df: pd.DataFrame) -> pd.DataFrame:
    latest = df["Wave key"].max()
    latest_df = df[df["Wave key"] == latest].copy()
    return latest_df.reset_index(drop=True)


def previous_wave_snapshot(df: pd.DataFrame) -> pd.DataFrame:
    dates = sorted(df["Wave key"].dropna().unique())
    if len(dates) < 2:
        return pd.DataFrame(columns=df.columns)
    prev = dates[-2]
    return df[df["Wave key"] == prev].copy().reset_index(drop=True)


def has_history(df: pd.DataFrame) -> bool:
    return df["Wave"].nunique() > 1


def factor_summary(df: pd.DataFrame, schema: Schema) -> pd.DataFrame:
    rows = []
    for n, col in schema.factor_cols.items():
        scores = df.loc[df["Completed PASS"], col].dropna()
        total = len(scores)
        if total == 0:
            continue
        low = int((scores <= 5).sum())
        low_mod = int(((scores >= 6) & (scores <= 20)).sum())
        moderate = int(((scores >= 21) & (scores <= 30)).sum())
        high = int((scores >= 31).sum())
        rows.append(
            {
                "Factor": n,
                "Factor name": FACTOR_NAMES[n],
                "Median percentile": round(float(scores.median()), 1),
                "Low (≤5)": low,
                "Low-moderate (6–20)": low_mod,
                "Moderate (21–30)": moderate,
                "High (31–100)": high,
                "% ≤5": round(100 * low / total, 1),
                "% ≤20": round(100 * (low + low_mod) / total, 1),
                "% 21–30": round(100 * moderate / total, 1),
                "% ≥31": round(100 * high / total, 1),
                "Completed": total,
            }
        )
    return pd.DataFrame(rows)


def wave_factor_summary(df: pd.DataFrame, schema: Schema) -> pd.DataFrame:
    rows = []
    for wave in available_waves(df):
        sub = df[df["Wave"] == wave]
        fs = factor_summary(sub, schema)
        if fs.empty:
            continue
        fs = fs.copy()
        fs.insert(0, "Wave", wave)
        rows.append(fs)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def attention_summary(df: pd.DataFrame, group_col: str) -> pd.DataFrame:
    items = []
    for group, sub in df.groupby(group_col, dropna=False):
        completed = int(sub["Completed PASS"].sum())
        total = len(sub)
        counts = sub["Attention"].astype(str).value_counts()
        item = {
            group_col: group,
            "Students": total,
            "Completed": completed,
            "Completion %": round(100 * completed / total, 1) if total else 0,
        }
        for label in ATTENTION_ORDER:
            item[label] = int(counts.get(label, 0))
        item["Immediate/targeted %"] = round(
            100 * (item["Immediate review"] + item["Targeted support"]) / completed, 1
        ) if completed else 0
        items.append(item)
    return pd.DataFrame(items)


def homeroom_summary(df: pd.DataFrame, schema: Schema) -> pd.DataFrame:
    base = attention_summary(df, "Homeroom")
    top_factors = []
    for homeroom in base["Homeroom"].tolist():
        sub = df[df["Homeroom"] == homeroom]
        fs = factor_summary(sub, schema)
        if fs.empty:
            top_factors.append(("", 0.0))
        else:
            row = fs.sort_values(["% ≤20", "% ≤5"], ascending=False).iloc[0]
            top_factors.append((f"Factor {int(row['Factor'])} – {row['Factor name']}", float(row["% ≤20"])))
    base["Most common concern"] = [x[0] for x in top_factors]
    base["Top concern % ≤20"] = [x[1] for x in top_factors]
    return base.sort_values(["Immediate/targeted %", "Immediate review"], ascending=False)


def student_priority_table(df: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "Student",
        "Student ID",
        "Grade",
        "Homeroom",
        "Attention",
        "Immediate count",
        "Concern count",
        "Moderate count",
        "Lowest factor",
        "Lowest percentile",
        "Bottom 5% factors",
        "≤20th percentile factors",
        "21–30th percentile factors",
    ]
    result = df[cols].copy()
    result["Attention"] = result["Attention"].astype(str)
    rank = {v: i for i, v in enumerate(ATTENTION_ORDER)}
    result["_rank"] = result["Attention"].map(rank).fillna(99)
    result = result.sort_values(
        ["_rank", "Immediate count", "Concern count", "Moderate count", "Lowest percentile"],
        ascending=[True, False, False, False, True],
    ).drop(columns="_rank")
    return result


def factor_actions_for_context(df: pd.DataFrame, schema: Schema, top_n: int = 3) -> List[Dict[str, object]]:
    fs = factor_summary(df, schema)
    if fs.empty:
        return []
    selected = fs.sort_values(["% ≤20", "% ≤5"], ascending=False).head(top_n)
    output = []
    for _, row in selected.iterrows():
        n = int(row["Factor"])
        output.append(
            {
                "factor": n,
                "name": FACTOR_NAMES[n],
                "description": FACTOR_DESCRIPTIONS[n],
                "pct_concern": float(row["% ≤20"]),
                "pct_immediate": float(row["% ≤5"]),
                "focus": INTERVENTIONS[n]["focus"],
                "universal": INTERVENTIONS[n]["universal"],
                "targeted": INTERVENTIONS[n]["targeted"],
                "questions": INTERVENTIONS[n]["questions"],
            }
        )
    return output


def student_factor_profile(row: pd.Series, schema: Schema) -> pd.DataFrame:
    records = []
    for n, col in schema.factor_cols.items():
        value = row[col]
        records.append(
            {
                "Factor": n,
                "Factor name": FACTOR_NAMES[n],
                "Percentile": None if pd.isna(value) else float(value),
                "Band": factor_band(value),
                "Description": FACTOR_DESCRIPTIONS[n],
            }
        )
    return pd.DataFrame(records)


def context_summary_text(df: pd.DataFrame, schema: Schema) -> str:
    completed = int(df["Completed PASS"].sum())
    total = len(df)
    fs = factor_summary(df, schema)
    if fs.empty:
        return "No completed PASS records available."
    top = fs.sort_values(["% ≤20", "% ≤5"], ascending=False).head(3)
    parts = [f"{total} students; {completed} completed ({100*completed/total:.1f}%)."]
    parts.append(
        "Highest concern factors: "
        + ", ".join(
            f"Factor {int(r['Factor'])} – {r['Factor name']} ({r['% ≤20']:.1f}% at/under 20th percentile)"
            for _, r in top.iterrows()
        )
        + "."
    )
    return " ".join(parts)


def student_history(df: pd.DataFrame, student_id: str) -> pd.DataFrame:
    return df[df["Student ID"] == student_id].sort_values("Wave sort").copy()


def student_factor_journey(df: pd.DataFrame, schema: Schema, student_id: str, factors: List[int] | None = None) -> pd.DataFrame:
    rows = []
    sub = student_history(df, student_id)
    factors = factors or list(schema.factor_cols.keys())
    for _, row in sub.iterrows():
        for n in factors:
            col = schema.factor_cols[n]
            value = row[col]
            rows.append(
                {
                    "Wave": row["Wave"],
                    "Wave sort": row["Wave sort"],
                    "Factor": n,
                    "Factor name": FACTOR_NAMES[n],
                    "Percentile": None if pd.isna(value) else float(value),
                    "Band": factor_band(value),
                }
            )
    return pd.DataFrame(rows)


def longitudinal_status_table(history_df: pd.DataFrame, latest_df: pd.DataFrame, schema: Schema, factors: List[int] | None = None) -> pd.DataFrame:
    factors = factors or list(schema.factor_cols.keys())
    factor_cols = {n: schema.factor_cols[n] for n in factors}
    all_dates = sorted(history_df["Wave key"].dropna().unique())
    prev_date = all_dates[-2] if len(all_dates) >= 2 else None
    previous_df = history_df[history_df["Wave key"] == prev_date].copy() if prev_date is not None else pd.DataFrame()

    rows = []
    for _, row in latest_df.iterrows():
        sid = row["Student ID"]
        hist = history_df[history_df["Student ID"] == sid].sort_values("Wave key")
        current_values = {n: row[col] for n, col in factor_cols.items()}
        current_concerns = {n for n, value in current_values.items() if pd.notna(value) and value <= 20}
        current_immediate = {n for n, value in current_values.items() if pd.notna(value) and value <= 5}
        current_moderate = {n for n, value in current_values.items() if pd.notna(value) and 21 <= value <= 30}

        factor_concern_waves = {}
        for n, col in factor_cols.items():
            values = hist[["Wave key", col]].dropna().drop_duplicates(subset=["Wave key"], keep="last")
            factor_concern_waves[n] = int((values[col] <= 20).sum())

        prev_values = {}
        prev_match = previous_df[previous_df["Student ID"] == sid]
        if not prev_match.empty:
            prev_row = prev_match.sort_values("Wave sort").iloc[-1]
            prev_values = {n: prev_row[col] for n, col in factor_cols.items()}
        previous_concerns = {n for n, value in prev_values.items() if pd.notna(value) and value <= 20}

        chronic_factors = {n for n in current_concerns if factor_concern_waves.get(n, 0) >= 3}
        persistent_factors = current_concerns & previous_concerns
        new_factors = current_concerns - previous_concerns
        recovered_factors = previous_concerns - current_concerns

        deterioration_factors = set()
        for n in factors:
            cur = current_values.get(n)
            prev = prev_values.get(n)
            if pd.isna(cur) or pd.isna(prev):
                continue
            if (prev > 30 and cur <= 30) or (prev - cur >= 15):
                deterioration_factors.add(n)

        if not bool(row["Completed PASS"]):
            trend = "Insufficient history"
        elif chronic_factors:
            trend = "Chronic concern"
        elif persistent_factors:
            trend = "Persistent concern"
        elif new_factors:
            trend = "New concern"
        elif previous_concerns and not current_concerns and not current_moderate:
            trend = "Recovered"
        elif deterioration_factors:
            trend = "Watch deterioration"
        else:
            trend = "Stable positive"

        rows.append(
            {
                "Student": row["Student"],
                "Student ID": sid,
                "Grade": row["Grade"],
                "Homeroom": row["Homeroom"],
                "Attention": str(row["Attention"]),
                "Longitudinal status": trend,
                "Current factors ≤5": len(current_immediate),
                "Current factors ≤20": len(current_concerns),
                "Current factors 21–30": len(current_moderate),
                "Previous factors ≤20": len(previous_concerns),
                "Chronic factors": "; ".join(f"Factor {n} – {FACTOR_NAMES[n]}" for n in sorted(chronic_factors)),
                "Persistent factors": "; ".join(f"Factor {n} – {FACTOR_NAMES[n]}" for n in sorted(persistent_factors)),
                "New factors": "; ".join(f"Factor {n} – {FACTOR_NAMES[n]}" for n in sorted(new_factors)),
                "Recovered factors": "; ".join(f"Factor {n} – {FACTOR_NAMES[n]}" for n in sorted(recovered_factors)),
                "Deteriorating factors": "; ".join(f"Factor {n} – {FACTOR_NAMES[n]}" for n in sorted(deterioration_factors)),
                "Repeated concern across survey waves": max(factor_concern_waves.values(), default=0),
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
                ),
                "Lowest factor": row["Lowest factor"],
                "Lowest percentile": row["Lowest percentile"],
                "≤20th percentile factors": row["≤20th percentile factors"],
            }
        )
    out = pd.DataFrame(rows)
    rank = {v: i for i, v in enumerate(LONGITUDINAL_ORDER)}
    out["_rank"] = out["Longitudinal status"].map(rank).fillna(99)
    out = out.sort_values(
        ["_rank", "Current factors ≤5", "Current factors ≤20", "Repeated concern across survey waves", "Lowest percentile"],
        ascending=[True, False, False, False, True],
    ).drop(columns="_rank")
    return out

def wave_transition_summary(history_df: pd.DataFrame, schema: Schema, factors: List[int] | None = None) -> pd.DataFrame:
    factors = factors or list(schema.factor_cols.keys())
    factor_cols = {n: schema.factor_cols[n] for n in factors}
    dates = sorted(history_df["Wave key"].dropna().unique())
    if len(dates) < 2:
        return pd.DataFrame()
    prev_date, current_date = dates[-2], dates[-1]
    prev_df = history_df[history_df["Wave key"] == prev_date][["Student ID", *factor_cols.values()]].copy()
    current_df = history_df[history_df["Wave key"] == current_date][["Student ID", *factor_cols.values()]].copy()
    merged = current_df.merge(prev_df, on="Student ID", how="inner", suffixes=("_cur", "_prev"))
    rows = []
    for n, col in factor_cols.items():
        cur = merged[f"{col}_cur"]
        prev = merged[f"{col}_prev"]
        rows.append(
            {
                "Factor": n,
                "Factor name": FACTOR_NAMES[n],
                "Persistent": int(((cur <= 20) & (prev <= 20)).sum()),
                "New": int(((cur <= 20) & (prev > 20)).sum()),
                "Recovered": int(((cur > 30) & (prev <= 20)).sum()),
                "Watch deterioration": int(((cur <= 30) & (prev > 30)).sum()),
                "Compared students": int(len(merged)),
            }
        )
    return pd.DataFrame(rows)


def wave_factor_trend_for_chart(history_df: pd.DataFrame, schema: Schema, factors: List[int] | None = None) -> pd.DataFrame:
    factors = factors or list(schema.factor_cols.keys())
    rows = []
    for wave in available_waves(history_df):
        sub = history_df[history_df["Wave"] == wave]
        for n in factors:
            col = schema.factor_cols[n]
            scores = sub.loc[sub["Completed PASS"], col].dropna()
            total = len(scores)
            if total == 0:
                continue
            rows.append(
                {
                    "Wave": wave,
                    "Wave sort": sub["Wave key"].iloc[0],
                    "Factor": n,
                    "Factor name": FACTOR_NAMES[n],
                    "Median percentile": float(scores.median()),
                    "% ≤5": round(100 * (scores <= 5).sum() / total, 1),
                    "% ≤20": round(100 * (scores <= 20).sum() / total, 1),
                    "Completed": total,
                }
            )
    return pd.DataFrame(rows)
