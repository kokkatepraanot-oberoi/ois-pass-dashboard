# PASS Analysis Framework for OIS Middle School

## 1. SLT: high-level analysis

SLT should not work from named student lists. The dashboard should answer five questions:

1. **Did enough students complete PASS for the picture to be trustworthy?**
2. **Which of the nine factors are the main school-wide concerns?** Use the percentage of completed students at/under the 20th percentile and the percentage in the lowest 5%.
3. **Which grades show different patterns?** Compare intervention load and factor distributions; avoid treating a simple average of individual percentiles as a cohort PASS percentile.
4. **Is concern concentrated in particular homerooms?** Use this as a resourcing/follow-up map, not as a judgement of the HRT.
5. **What should change at system level?** Choose 2–3 priorities only.

Core outputs: completion, factor band distribution, grade comparison, homeroom variation, intervention load, top 3 system priorities.

## 2. Grade Level Leaders: detailed grade analysis

GLs need enough detail to plan and allocate interventions:

- Grade factor profile across all nine PASS factors.
- Homeroom comparison within the grade.
- Named student priority list sorted by PASS concern bands.
- Number and breadth of low factors for each student.
- Student-level nine-factor profile.
- Suggested grade-wide, targeted and check-in responses.
- Downloadable working list for intervention allocation.

The GL should deliberately separate:

- **Universal response:** a grade pattern that suggests a common issue.
- **Targeted response:** a group of students with a similar factor concern.
- **Individual response:** a student's specific factor pattern and context.

## 3. Homeroom Teachers: clear student picture

HRTs need a simple operational view:

- Homeroom factor profile.
- Check-in queue: Immediate, Targeted, Monitor, Not completed.
- Lowest factor and all factors at/under the 20th percentile for each student.
- Individual profile with suggested opening question and first practical response.

The HRT should not be asked to interpret psychometrics. The dashboard translates the data into: **who needs a conversation, what the conversation should explore, and what first action is reasonable.**

## 4. Learning Support: learning access and barrier review

Learning Support should use a focused lens rather than treating every low PASS factor as a learning-support issue. The dashboard focuses on:

- **F2 Perceived learning capability**
- **F3 Self-regard as a learner**
- **F4 Preparedness for learning**
- **F6 General work ethic**
- **F7 Confidence in learning**
- **F9 Response to curriculum demands**

### What Learning Support should analyse

1. Which students show **multiple learning-related factors at/under the 20th percentile**?
2. Are patterns concentrated in a grade or homeroom, suggesting a curriculum/routine issue rather than an individual learning need?
3. Does the PASS pattern agree with attainment, work samples, teacher observation, language profile, screening and existing support records?
4. What is the **smallest useful intervention** that can be tried and measured over 3–4 weeks?

A low score in this view **does not identify SEND or a specific learning difficulty**. It creates a review priority only.

## 5. Counsellors: pastoral context and check-in triage

The counsellor view focuses on:

- **F1 Feelings about school**
- **F3 Self-regard as a learner**
- **F5 Attitudes to teachers**
- **F7 Confidence in learning**
- **F8 Attitudes to attendance**

### What counsellors should analyse

1. Which students show **multiple low pastoral/relational factors**, particularly where other evidence already raises concern?
2. Are there grade or homeroom patterns that should be addressed through pastoral systems rather than individual counselling?
3. Is the student already known to counselling, safeguarding or the grade team, so contact is coordinated rather than duplicated?
4. Which PASS factor gives the best **opening question** for a student check-in?

PASS is **not a mental-health, self-harm or safeguarding risk assessment**. A low factor should never trigger a clinical conclusion or counselling referral by itself. If a conversation raises a safeguarding concern, staff should follow the school's safeguarding procedure immediately.

## 6. Guardrails

- PASS is not a clinical diagnosis.
- A low factor is a prompt for enquiry, not proof of a cause.
- Triangulate with attendance, attainment, behaviour, teacher observations and student voice.
- Do not infer teacher performance from homeroom/class patterns without further evidence.
- Do not treat a Learning Support or Counsellor specialist queue as an automatic referral list.
- If a discussion raises a safeguarding concern, follow the school's safeguarding procedure rather than keeping the matter within the PASS intervention workflow.
- Do not upload or commit live pupil data to GitHub.

## 7. Access boundary

The dashboard currently uses a shared app password plus a role selector. The selector changes the view only; it does not prevent a user from switching to another role. If HRTs, GLs, Learning Support and counsellors need different permissions, role-based authentication should be added before broad rollout.
