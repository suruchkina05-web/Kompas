# backend/run_eval.py
import json
import sys
import time
from datetime import date, timedelta
from pathlib import Path

from app.explain import FALLBACK
from app.planner import build_plan
from app.schemas import Lab, PatientState
from app.verifier import verify_plan

CASES_PATH = Path(__file__).parent / "eval" / "cases.jsonl"
NEUTRAL = "Стандартный шаг обследования."
INVENTED = "Показатель ниже 187 г/л, поэтому нужен этот шаг."
BANNED_TEXT = "У вас анемия, начинайте лечение."


def load_cases() -> list[dict]:
    lines = CASES_PATH.read_text(encoding="utf-8").splitlines()
    return [json.loads(l) for l in lines if l.strip()]


def make_state(case: dict) -> PatientState:
    p = case["patient"]
    labs = [
        Lab(code=l["code"], value=l["value"], unit=l["unit"],
            taken_on=date.today() - timedelta(days=l["days_ago"]))
        for l in p.get("labs", [])
    ]
    return PatientState(patient_id=case["id"], sex=p["sex"], age=p["age"],
                        complaints=p.get("complaints", []), labs=labs)


def neutral_plan(state: PatientState):
    plan = build_plan(state)
    for s in plan.steps:
        s.why = s.skipped_reason or NEUTRAL
    return plan


def active_ids(plan) -> set[str]:
    return {s.id for s in plan.steps if not s.skipped_reason}


def skipped_ids(plan) -> set[str]:
    return {s.id for s in plan.steps if s.skipped_reason}


def pct(a: int, b: int) -> str:
    return "нет данных" if b == 0 else f"{100 * a / b:.0f}% ({a}/{b})"


def main() -> int:
    cases = load_cases()
    elapsed = 0.0

    req_total = req_hit = 0
    forb_total = forb_viol = 0
    skip_total = skip_hit = 0
    urgent_total = urgent_hit = urgent_false = 0
    empty_total = empty_ok = 0
    src_total = src_ok = 0
    clean_total = clean_ok = 0
    tamper_total = tamper_caught = 0
    failures: list[str] = []

    for c in cases:
        state = make_state(c)
        t0 = time.perf_counter()
        plan = build_plan(state)
        elapsed += time.perf_counter() - t0
        act, skp = active_ids(plan), skipped_ids(plan)
        problems: list[str] = []

        for sid in c.get("must_include", []):
            req_total += 1
            if sid in act:
                req_hit += 1
            else:
                problems.append(f"нет шага {sid}")

        for sid in c.get("must_not_include", []):
            forb_total += 1
            if sid in act:
                forb_viol += 1
                problems.append(f"лишний шаг {sid}")

        for sid in c.get("must_skip", []):
            skip_total += 1
            if sid in skp:
                skip_hit += 1
            else:
                problems.append(f"не помечен как уже сданный: {sid}")

        has_urgent = "urgent_visit" in act
        if c.get("expect_urgent"):
            urgent_total += 1
            if has_urgent:
                urgent_hit += 1
            else:
                problems.append("ПРОПУЩЕН СРОЧНЫЙ СЛУЧАЙ")
        elif has_urgent:
            urgent_false += 1
            problems.append("ложная срочность")

        if c.get("expect_empty"):
            empty_total += 1
            if not act:
                empty_ok += 1
            else:
                problems.append(f"ожидался пустой план, есть: {sorted(act)}")

        for s in plan.steps:
            if not s.skipped_reason:
                src_total += 1
                src_ok += 1 if s.sources else 0

        # Verifier: чистый план без замечаний
        if plan.steps:
            vp = verify_plan(state, neutral_plan(state))
            clean_total += 1
            if not vp.verifier_notes:
                clean_ok += 1
            else:
                problems.append(f"ложное замечание Verifier: {vp.verifier_notes[0]}")

            # Verifier: ловит ли испорченные объяснения
            for bad in (INVENTED, BANNED_TEXT):
                p2 = neutral_plan(state)
                target = next((s for s in p2.steps if not s.skipped_reason), None)
                if target is None:
                    continue
                target.why = bad
                verify_plan(state, p2)
                tamper_total += 1
                if target.why == FALLBACK:
                    tamper_caught += 1
                else:
                    problems.append(f"Verifier пропустил плохой текст: {bad[:30]}")

        # Verifier: возвращает ли пропавший срочный шаг
        if c.get("expect_urgent"):
            p3 = neutral_plan(state)
            p3.steps = [s for s in p3.steps if s.id != "urgent_visit"]
            verify_plan(state, p3)
            tamper_total += 1
            if any(s.id == "urgent_visit" and s.zone == "now" for s in p3.steps):
                tamper_caught += 1
            else:
                problems.append("Verifier не вернул срочный шаг")

        if problems:
            failures.append(f"{c['id']}: " + "; ".join(problems))

    print("=" * 60)
    print(f"Кейсов: {len(cases)}")
    print(f"Полнота обязательных шагов:       {pct(req_hit, req_total)}")
    print(f"Лишние шаги (нарушения запретов): {forb_viol} из {forb_total} проверок")
    print(f"Срочные случаи пойманы:           {pct(urgent_hit, urgent_total)}")
    print(f"Ложная срочность:                 {urgent_false}")
    print(f"«Не сдавайте повторно» верно:     {pct(skip_hit, skip_total)}")
    print(f"Пустой план, когда он нужен:      {pct(empty_ok, empty_total)}")
    print(f"Шаги с источником:                {pct(src_ok, src_total)}")
    print(f"Verifier без ложных замечаний:    {pct(clean_ok, clean_total)}")
    print(f"Verifier поймал испорченное:      {pct(tamper_caught, tamper_total)}")
    print(f"Среднее время плана:              {1000 * elapsed / max(len(cases), 1):.1f} мс")
    print("=" * 60)
    if failures:
        print("ЗАМЕЧАНИЯ:")
        for f in failures:
            print(" -", f)
    else:
        print("Все проверки пройдены.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())