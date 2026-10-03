from app.rules.engine import evaluate_rules, load_steps
from app.schemas import PatientPlan, PatientState, PlanStep, StepSource


def build_plan(state: PatientState) -> PatientPlan:
    all_steps_meta = load_steps()
    triggered_ids = evaluate_rules(state)

    steps = []
    for step_id in triggered_ids:
        meta = all_steps_meta.get(step_id, {})
        ref = meta.get("guideline_ref", "Клинические рекомендации Минздрава РФ")
        steps.append(
            PlanStep(
                id=step_id,
                title=meta.get("title", "Обследование"),
                zone=meta.get("zone", "now"),
                why=meta.get("description", ""),
                kind=meta.get("kind", "imaging"),
                guideline_ref=ref,
                trigger="Выявлены изменения по результатам лучевой диагностики",
                sources=[StepSource(document=ref, section="Порядок обследования")],
            )
        )

    red_flags = []
    if any(s.zone == "now" for s in steps):
        red_flags = [
            "Одышка в покое или при незначительной нагрузке",
            "Кровохарканье или выраженная боль в грудной клетке",
            "Резкий подъём температуры выше 38.5°C",
        ]

    return PatientPlan(version=1, steps=steps, red_flags=red_flags)