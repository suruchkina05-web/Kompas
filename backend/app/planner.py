# app/planner.py
from datetime import date
from .schemas import PatientState, Plan, Step, Source
from .rules.engine import evaluate, load_steps, _latest

ZONE_ORDER = {"now": 0, "two_weeks": 1, "planned": 2}

def build_plan(state: PatientState, version: int = 1) -> Plan:
    catalog = load_steps()
    steps: dict[str, Step] = {}
    red_flags: list[str] = []

    for c in evaluate(state):
        sid = c["step"]
        if sid in steps:                       # дедупликация
            continue
        meta = catalog[sid]
        skipped = None
        code = meta.get("lab_code")
        if meta["kind"] == "lab" and code:     # «не сдавайте повторно»
            lab = _latest(state, code)
            days = c["validity_days"].get(code)
            if lab and lab.taken_on and days and (date.today() - lab.taken_on).days <= days:
                skipped = f"Уже сдан {lab.taken_on}, результат ещё актуален"
        steps[sid] = Step(
            id=sid,
            title=meta["title"],
            kind=meta["kind"],
            zone=c["zone"],
            why="",
            confidence="medium",
            trigger=c["note"],
            sources=[Source(document=c["source"]["document"],
                            section=c["source"]["section"], quote="")],
            skipped_reason=skipped,
        )
        for rf in c["red_flags"]:
            if rf not in red_flags:
                red_flags.append(rf)

    ordered = sorted(steps.values(), key=lambda s: ZONE_ORDER[s.zone])
    return Plan(version=version, steps=ordered, red_flags=red_flags)