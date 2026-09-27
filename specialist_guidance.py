from __future__ import annotations

from typing import Dict, List

import streamlit as st

from pass_logic import FACTOR_NAMES


def factor_label(number: int) -> str:
    return f"Factor {number} – {FACTOR_NAMES[number]}"


LEARNING_SUPPORT_FACTORS = [2, 3, 4, 6, 7, 9]
COUNSELLOR_FACTORS = [1, 3, 5, 7, 8]


GUIDANCE: Dict[str, Dict[int, Dict[str, str]]] = {
    "Learning Support": {
        2: {
            "why": "The student may not feel capable or successful as a learner. This can reflect a skill gap, repeated difficulty, or a perception that does not match attainment evidence.",
            "do": "Triangulate with attainment/MAP, work samples and teacher observation. Identify successful contexts, then set a small mastery goal and the scaffold needed to reach it.",
            "where": "Start in subject classrooms with the relevant teacher and HRT. Move to a Learning Support case review when the pattern is repeated across subjects or survey waves.",
        },
        3: {
            "why": "Learning may be affecting how the student sees themselves. Setbacks can become personal rather than remaining task-specific.",
            "do": "Use strengths-and-evidence conversations, reduce public comparison and create short achievable success experiences. Check whether the concern is only academic or more general.",
            "where": "Classroom/HRT if mainly academic. Involve the counsellor if the concern is broader, emotionally significant or affecting the student's wider sense of self.",
        },
        4: {
            "why": "Preparedness concerns can point to organisation, task-start, planning, equipment or metacognitive routines rather than ability.",
            "do": "Choose one routine to teach explicitly: equipment, planning, task start, checking or submission. Use a checklist and review it after 2–3 weeks.",
            "where": "Daily classroom and homeroom routines. Coordinate with HRT and subject teachers so the same routine is reinforced consistently.",
        },
        6: {
            "why": "Low work-ethic scores can reflect task initiation, persistence, relevance, overload, distraction or difficulty. They should not simply be read as laziness.",
            "do": "Find the barrier first. Compare subjects, then use chunking, visible milestones, a task-start cue and short review cycles. Monitor actual completion data.",
            "where": "Subject lessons and HRT monitoring. Escalate to GL if the pattern is cross-curricular or linked to wider expectations/behaviour.",
        },
        7: {
            "why": "Low confidence can show avoidance of challenge, fear of failure or low perseverance when the answer is uncertain.",
            "do": "Use low-stakes rehearsal, graduated challenge and explicit help-seeking strategies. Check whether the difficulty is academic confidence or emotional anxiety.",
            "where": "Learning Support/subject teacher when academic. Involve the counsellor when anxiety or emotional distress appears to drive avoidance.",
        },
        9: {
            "why": "The amount, pace, difficulty, clarity or relevance of learning may feel badly matched to the student.",
            "do": "Compare the PASS result with attainment and subject patterns. Ask whether work feels too difficult, too easy, unclear, too much, or disconnected from prior learning before changing support.",
            "where": "Subject-level curriculum access and differentiation first. Coordinate with subject teachers and GL; use Learning Support for repeated access barriers across subjects.",
        },
    },
    "Counsellor": {
        1: {
            "why": "Reduced feelings about school can signal lower belonging, comfort or perceived safety. PASS does not identify the cause.",
            "do": "Use a contextual check-in: when does school feel easiest/hardest, who feels safe to approach, and has anything changed socially or emotionally?",
            "where": "Pastoral/counselling check-in. Liaise with HRT/GL for school context. If a safeguarding disclosure emerges, move immediately to the safeguarding process.",
        },
        3: {
            "why": "Learner self-regard may be academic, but it can also sit inside a wider pattern of self-esteem, shame or fear of failure.",
            "do": "Explore whether negative self-talk is limited to learning or more general. Reinforce strengths and identify protective relationships and successful contexts.",
            "where": "Counsellor if the issue is broad or emotionally significant; Learning Support/HRT if it is primarily about learning confidence or skill access.",
        },
        5: {
            "why": "This reflects the student's perception of relationships with teachers. It is not automatically a counselling issue.",
            "do": "Identify whether the concern is one teacher/subject or a general pattern. Understand the interaction before assuming motive or blame.",
            "where": "Usually start with HRT/GL and the relevant teacher. Counsellor involvement is useful when the issue is linked to trust, previous experiences, distress or broader relational patterns.",
        },
        7: {
            "why": "Low learning confidence can reflect fear of failure, anxiety under challenge or avoidance when uncertain.",
            "do": "Explore the emotional response to challenge and what happens when the student feels stuck. Reinforce coping and help-seeking where appropriate.",
            "where": "Counsellor when anxiety/emotional response is prominent; Learning Support/subject teacher when the issue is mainly skill, challenge or classroom access.",
        },
        8: {
            "why": "This measures how the student feels about attending school; it is not the same as actual attendance data.",
            "do": "Compare with actual attendance and explore barriers such as anxiety, peer relationships, sleep, workload, transport, health or family circumstances.",
            "where": "HRT/GL attendance process plus counsellor support where emotional barriers are present. Family contact should follow the school's normal attendance/pastoral process.",
        },
    },
}


def relevant_factors(role_name: str) -> List[int]:
    return LEARNING_SUPPORT_FACTORS if role_name == "Learning Support" else COUNSELLOR_FACTORS


def render_reading_guide(role_name: str) -> None:
    factors = relevant_factors(role_name)
    st.markdown("### How to read this specialist view")
    c1, c2, c3 = st.columns(3)
    c1.info("**Immediate concern (≤5th percentile)**\n\nAt least one relevant PASS factor is in the lowest band. Review promptly and triangulate; this is not a diagnosis.")
    c2.warning("**Targeted concern (6th–20th percentile)**\n\nA relevant factor is in the low-moderate band. Plan a check-in/intervention when other evidence supports it.")
    c3.success("**Watch (21st–30th percentile)**\n\nA relevant factor sits in the moderate band. Monitor and act if other evidence points the same way.")
    st.caption("This specialist lens only counts: " + "; ".join(factor_label(n) for n in factors) + ".")
    with st.expander("What do the longitudinal labels and 'repeated concern across survey waves' mean?"):
        st.markdown(
            "- **New concern:** a relevant factor is ≤20 now but was not ≤20 in the previous wave.\n"
            "- **Persistent concern:** the same relevant factor is ≤20 now and was also ≤20 in the previous wave.\n"
            "- **Chronic concern:** the same relevant factor has been ≤20 in at least three available waves and is still a current concern.\n"
            "- **Recovered:** a previous ≤20 concern has moved above the watch band.\n"
            "- **Repeated concern across survey waves = 5** means at least one relevant factor was ≤20 in five available PASS waves. It does **not** mean five different problems, and the waves do not have to be consecutive. A value of 3 means the maximum for any one relevant factor is three waves."
        )


def render_intervention_guidance(role_name: str) -> None:
    st.markdown(f"### What {role_name} can do")
    if role_name == "Learning Support":
        st.markdown("**Purpose:** identify barriers to accessing learning, test hypotheses against classroom/attainment evidence, and coordinate practical support. PASS should not be used to diagnose SEND.")
    else:
        st.markdown("**Purpose:** identify pastoral/relational signals that merit context or conversation. PASS should not be used as a mental-health assessment or automatic counselling referral.")
    for number, item in GUIDANCE[role_name].items():
        with st.expander(factor_label(number)):
            st.markdown(f"**Why this may matter**  \n{item['why']}")
            st.markdown(f"**What you can do**  \n{item['do']}")
            st.markdown(f"**Where / who should intervene**  \n{item['where']}")
    st.error("**Safeguarding overrides PASS.** If a student discloses or presents a safeguarding concern, stop using the PASS intervention workflow and follow the school's safeguarding procedure immediately.")
