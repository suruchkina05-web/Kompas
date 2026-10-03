from app.rules.engine import evaluate_rules
from app.schemas import PatientPlan, PatientState


def verify_plan(state: PatientState, plan: PatientPlan) -> list[str]:
    """Проверяет полноту сформированного плана на основе правил."""
    expected_step_ids = evaluate_rules(state)
    current_step_ids = {s.id for s in plan.steps}

    missing_warnings = []
    for step_id in expected_step_ids:
        if step_id not in current_step_ids:
            missing_warnings.append(
                f"Внимание: Шаг '{step_id}' рекомендуется правилами, но отсутствует в итоговом плане."
            )

    return missing_warnings