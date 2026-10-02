# app/diff.py
from app.schemas import Plan, PlanDiff, Step, PatientState
from app.rules.engine import load_steps

LAB_NAMES = {"hemoglobin": "гемоглобин", "ferritin": "ферритин", "tsh": "ТТГ", "ldl": "ЛПНП"}


def _active(plan: Plan) -> dict[str, Step]:
    """Только шаги, которые пациенту ещё нужно сделать (без уже сданных)."""
    return {s.id: s for s in plan.steps if not s.skipped_reason}


def diff_plans(old: Plan, new: Plan, state: PatientState, new_labs=None) -> PlanDiff:
    a, b = _active(old), _active(new)
    added = [b[i] for i in b if i not in a]
    removed = [a[i] for i in a if i not in b]
    changed = [(a[i], b[i]) for i in b if i in a and a[i].zone != b[i].zone]
    return PlanDiff(added=added, removed=removed, changed=changed,
                    explanation=_explain(added, removed, changed, new_labs or []))


def _explain(added, removed, changed, new_labs) -> str:
    if not (added or removed or changed):
        return "Новые данные не изменили маршрут."
    catalog = load_steps()
    parts = []

    if new_labs:
        txt = "; ".join(
            f"{LAB_NAMES.get(l.code, l.code)} {l.value:g} {l.unit}"
            + (f" ({l.taken_on})" if l.taken_on else "")
            for l in new_labs
        )
        parts.append(f"Новый результат: {txt}.")

    if added:
        reasons = list(dict.fromkeys(s.trigger for s in added if s.trigger))
        if reasons:
            parts.append("Почему маршрут изменился: " + "; ".join(reasons) + ".")
        parts.append("Добавлено в маршрут: " + "; ".join(s.title for s in added) + ".")

    if removed:
        got = {l.code for l in new_labs}
        notes = []
        for s in removed:
            done = catalog.get(s.id, {}).get("lab_code") in got
            notes.append(s.title + (" (результат уже получен)" if done else ""))
        parts.append("Больше не нужно: " + "; ".join(notes) + ".")

    if changed:
        parts.append("Изменён срок у: " + "; ".join(n.title for _, n in changed) + ".")

    return " ".join(parts)