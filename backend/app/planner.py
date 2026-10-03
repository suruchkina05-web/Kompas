from app.rules.engine import evaluate_rules, load_steps
from app.schemas import PatientState, PlanResponse, PlanStep


def build_plan(state: PatientState) -> PlanResponse:
    """Строит маршрут обследования и консультаций пациента на основе лучевой диагностики."""
    all_steps_meta = load_steps()
    triggered_ids = evaluate_rules(state)

    steps: list[PlanStep] = []
    for step_id in triggered_ids:
        meta = all_steps_meta.get(step_id, {})
        steps.append(
            PlanStep(
                id=step_id,
                title=meta.get("title", step_id),
                description=meta.get("description", ""),
                zone=meta.get("zone", "now"),
                skipped_reason=None,
            )
        )

    return PlanResponse(
        patient_id=state.patient_id,
        steps=steps,
    )