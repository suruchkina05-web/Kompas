from app.rules.engine import evaluate_rules, load_steps
from app.schemas import PatientState, PlanResponse, PlanStep


def verify_plan(state: PatientState, plan: PlanResponse) -> dict:
    """Проверяет соответствие текущего плана пациента правилам маршрутизации."""
    all_steps_meta = load_steps()
    expected_ids = set(evaluate_rules(state))
    actual_ids = {step.id for step in plan.steps}

    missing_steps = list(expected_ids - actual_ids)
    extra_steps = list(actual_ids - expected_ids)

    is_valid = len(missing_steps) == 0

    return {
        "is_valid": is_valid,
        "missing_step_ids": missing_steps,
        "extra_step_ids": extra_steps,
    }