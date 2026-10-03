from app.schemas import Comparison, PatientPlan


def compare_with_text(plan: PatientPlan, raw_text: str) -> Comparison:
    orders_text = raw_text.lower()
    matched = []
    possibly_missing = []

    for step in plan.steps:
        # Проверяем вхождение ключевых слов названия шага в текст назначений
        words = [w for w in step.title.lower().split() if len(w) > 3]
        if any(w in orders_text for w in words):
            matched.append(step)
        else:
            possibly_missing.append(step)

    return Comparison(
        matched=matched,
        possibly_missing=possibly_missing,
        unclear=[],
        questions_for_doctor=[
            f"Уточнить необходимость шага: {s.title}" for s in possibly_missing
        ],
    )