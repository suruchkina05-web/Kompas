# app/explain.py
import json
import traceback

from app.llm import ask, _clean_json
from app.schemas import PatientState, Plan
from app.rules.engine import load_steps

SYSTEM = """Ты объясняешь пациенту уже определённые шаги маршрута обращения.
Ты НЕ ставишь диагнозы, НЕ назначаешь лечение и НЕ оцениваешь работу врачей.
Используй только переданные факты и переданную цель шага. Не добавляй новых медицинских утверждений:
объясняй цель шага близко к её тексту.
Пиши простым языком, спокойно, без запугивания. Верни только JSON."""

PROMPT = """Данные пациента:
{facts}

Шаги маршрута. Каждый шаг уже определён правилами, ты только объясняешь.
Для каждого шага указаны данные, которые к нему привели, и его цель. Называть можно только эту цель.
{steps}

Верни JSON такого вида (поле id копируй без изменений из списка шагов):
{{"items": [
  {{"id": "id шага",
    "why": "2-3 предложения: назови конкретный показатель пациента и его значение, затем цель шага. Больше ничего не объясняй",
    "questions": ["1-2 вопроса, которые ПАЦИЕНТ задаёт ВРАЧУ на приёме, от первого лица"]}}
]}}

Примеры хороших вопросов пациента врачу:
- Что означают мои результаты ферритина и гемоглобина?
- Какие обследования мне нужны, чтобы выяснить причину?
- Через какое время нужно повторить анализы?
Вопросы, которые врач задаёт пациенту, писать нельзя."""

BANNED = ["у вас анемия", "у вас диагноз", "принимайте", "вам нужно принимать",
          "врач ошибся", "неправильно", "должен был", "врач назначил"]

FALLBACK = "Этот шаг предусмотрен клинической рекомендацией при таких данных. Уточните детали у врача."


def _facts(state: PatientState) -> str:
    labs = "; ".join(f"{l.code} {l.value} {l.unit} ({l.taken_on or 'дата не указана'})"
                     for l in state.labs) or "анализов нет"
    return (f"пол: {state.sex}, возраст: {state.age}; "
            f"жалобы: {', '.join(state.complaints) or 'не указаны'}; анализы: {labs}")


def _ok(text: str) -> bool:
    t = text.lower()
    return bool(text.strip()) and not any(b in t for b in BANNED)


def _ask_items(prompt: str) -> list[dict]:
    """Вызывает модель. Печатает ответ и причину ошибки в терминал, повторяет один раз."""
    for attempt in (1, 2):
        try:
            raw = ask(prompt, SYSTEM)
            print(f"=== EXPLAIN RAW (попытка {attempt}) ===\n{raw[:2000]}")
            data = json.loads(_clean_json(raw))
            items = data if isinstance(data, list) else data.get("items", [])
            return [i for i in items if isinstance(i, dict)]
        except Exception:
            print(f"=== EXPLAIN ERROR (попытка {attempt}) ===\n{traceback.format_exc()}")
    return []


def explain_plan(state: PatientState, plan: Plan) -> Plan:
    catalog = load_steps()
    active = [s for s in plan.steps if not s.skipped_reason]
    if not active:
        return plan

    steps_txt = "\n".join(
        f"- id={s.id}; шаг: {s.title}; данные, которые привели к шагу: {s.trigger}; "
        f"цель шага: {catalog.get(s.id, {}).get('purpose', 'не указана')}"
        for s in active
    )
    items = _ask_items(PROMPT.format(facts=_facts(state), steps=steps_txt))

    by_id = {str(i.get("id")): i for i in items}
    # если модель перепутала id, но вернула столько же элементов, сопоставляем по порядку
    if not any(s.id in by_id for s in active) and len(items) == len(active):
        by_id = {s.id: it for s, it in zip(active, items)}

    for s in active:
        item = by_id.get(s.id, {})
        why = str(item.get("why", ""))
        if _ok(why):
            s.why = why
        else:
            if why:
                print(f"=== ОТКЛОНЕНО фильтром ({s.id}) ===\n{why}")
            s.why = FALLBACK
            s.confidence = "doctor_decides"
        questions = item.get("questions", [])
        if isinstance(questions, list):
            s.questions_for_doctor = [str(q) for q in questions if _ok(str(q))][:3]

    for s in plan.steps:
        if s.skipped_reason and not s.why:
            s.why = s.skipped_reason
    return plan