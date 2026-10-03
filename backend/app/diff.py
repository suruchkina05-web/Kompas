from app.schemas import Comparison, PatientState, PlanDiff, PlanResponse, PlanStep


def diff_plans(old_plan: PlanResponse, new_plan: PlanResponse) -> PlanDiff:
    """Сравнивает два плана маршрутизации и вычисляет добавленные и удалённые шаги."""
    old_steps = {s.id: s for s in old_plan.steps}
    new_steps = {s.id: s for s in new_plan.steps}

    added = [step for step_id, step in new_steps.items() if step_id not in old_steps]
    removed = [step for step_id, step in old_steps.items() if step_id not in new_steps]

    return PlanDiff(added=added, removed=removed)


def compare_plans(before: PlanResponse, after: PlanResponse) -> Comparison:
    """Формирует объект сравнения двух планов с подробной разницей (diff)."""
    difference = diff_plans(before, after)
    return Comparison(
        before=before,
        after=after,
        diff=difference,
    )