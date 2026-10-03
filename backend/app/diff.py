from app.schemas import PatientPlan, PlanDiff

def diff_plans(old_plan: PatientPlan, new_plan: PatientPlan) -> PlanDiff:
    old_steps = {s.id: s for s in old_plan.steps}
    new_steps = {s.id: s for s in new_plan.steps}

    added = [s for s_id, s in new_steps.items() if s_id not in old_steps]
    removed = [s for s_id, s in old_steps.items() if s_id not in new_steps]
    unchanged = [s for s_id, s in new_steps.items() if s_id in old_steps]

    return PlanDiff(added=added, removed=removed, unchanged=unchanged)