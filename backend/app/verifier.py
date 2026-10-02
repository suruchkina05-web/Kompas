# app/verifier.py
import re

from app.explain import BANNED, FALLBACK
from app.rules.engine import evaluate, load_steps, _latest
from app.schemas import PatientState, Plan, Source, Step

PLAUSIBLE = {
    "hemoglobin": (30, 250),   # г/л
    "ferritin": (0.5, 3000),   # нг/мл
}

DEFAULT_SOURCE = Source(
    document="Клинические рекомендации «Железодефицитная анемия» (ID 669, 2024)",
    section="Лечение: тяжёлая анемия (гемоглобин менее 70 г/л)",
    quote="",
)


def _numbers(text: str) -> set[str]:
    """Числа из текста, кроме однозначных целых."""
    found = set()
    for n in re.findall(r"\d+(?:[.,]\d+)?", text):
        n = n.replace(",", ".")
        if len(n) >= 2:
            found.add(n)
    return found


def _allowed_numbers(state: PatientState, step: Step, catalog: dict) -> set[str]:
    parts = [str(state.age), step.title, step.trigger or "",
             catalog.get(step.id, {}).get("purpose", "")]
    for lab in state.labs:
        parts.append(f"{lab.value:g} {lab.unit} {lab.taken_on or ''}")
    return _numbers(" ".join(parts))


def verify_plan(state: PatientState, plan: Plan) -> Plan:
    catalog = load_steps()
    notes: list[str] = []

    # 1. значения анализов правдоподобны
    for lab in state.labs:
        rng = PLAUSIBLE.get(lab.code)
        if rng and not (rng[0] <= lab.value <= rng[1]):
            notes.append(
                f"Значение {lab.code} = {lab.value:g} {lab.unit} выглядит неправдоподобно: "
                f"проверьте, что оно извлечено верно (единицы измерения)."
            )

    # 2. независимый инвариант безопасности: Hb < 70 г/л -> срочный шаг
    hb = _latest(state, "hemoglobin")
    has_urgent = any(s.id == "urgent_visit" and s.zone == "now" for s in plan.steps)
    if hb is not None and hb.value < 70 and not has_urgent:
        meta = catalog["urgent_visit"]
        sources = next((s.sources for s in plan.steps if s.sources), None) or [DEFAULT_SOURCE]
        plan.steps.insert(0, Step(
            id="urgent_visit",
            title=meta["title"],
            kind="urgent",
            zone="now",
            why=f"Гемоглобин {hb.value:g} г/л ниже 70 г/л. Не откладывайте обращение к врачу.",
            confidence="doctor_decides",
            trigger="гемоглобин ниже 70 г/л: это тяжёлая анемия, не откладывайте обращение",
            sources=sources,
        ))
        notes.append("Verifier добавил срочный шаг: гемоглобин ниже 70 г/л.")

    # 3. в плане есть все шаги, которые требуют правила
    expected = {c["step"] for c in evaluate(state)}
    missing = expected - {s.id for s in plan.steps}
    for sid in sorted(missing):
        title = catalog.get(sid, {}).get("title", sid)
        notes.append(f"В плане нет шага, который требуют правила: {title}.")

    # 4. проверка каждого активного шага
    for s in plan.steps:
        if s.skipped_reason:
            continue
        if not s.sources:
            s.confidence = "doctor_decides"
            notes.append(f"У шага «{s.title}» нет источника: помечен «решает врач».")

        why = (s.why or "").strip()
        problem = None
        if not why:
            problem = "нет объяснения"
        elif any(b in why.lower() for b in BANNED):
            problem = "запрещённая формулировка"
        else:
            extra = _numbers(why) - _allowed_numbers(state, s, catalog)
            if extra:
                problem = "в объяснении числа, которых нет в данных пациента: " + ", ".join(sorted(extra))
        if problem:
            s.why = FALLBACK
            s.confidence = "doctor_decides"
            notes.append(f"Шаг «{s.title}»: {problem}. Текст заменён на безопасный.")

    plan.verifier_notes = list(plan.verifier_notes) + notes
    return plan