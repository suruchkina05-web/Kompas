# app/rules/engine.py
import json
from pathlib import Path
from ..schemas import PatientState

DIR = Path(__file__).parent


def load_graphs() -> list[dict]:
    return [json.loads(p.read_text(encoding="utf-8"))
            for p in DIR.glob("*.json") if p.name != "steps.json"]


def load_steps() -> dict:
    return json.loads((DIR / "steps.json").read_text(encoding="utf-8"))


def _latest(state: PatientState, code: str):
    labs = [l for l in state.labs if l.code == code]
    if not labs:
        return None
    return max(labs, key=lambda l: l.taken_on.toordinal() if l.taken_on else 0)


def matches(when: dict, state: PatientState) -> bool:
    if "all" in when:
        return all(matches(c, state) for c in when["all"])
    if "sex" in when and state.sex != when["sex"]:
        return False
    if "lab" in when:
        lab = _latest(state, when["lab"])
        if lab is None:
            return False
        if "lt" in when and not lab.value < when["lt"]:
            return False
        if "gt" in when and not lab.value > when["gt"]:
            return False
    if "missing_lab" in when and _latest(state, when["missing_lab"]) is not None:
        return False
    return True


def evaluate(state: PatientState) -> list[dict]:
    out = []
    for g in load_graphs():
        for node in g["nodes"]:
            if matches(node["when"], state):
                source = {**g["source"],
                          "section": node.get("section", g["source"]["section"])}
                for t in node["then"]:
                    out.append({
                        **t,
                        "pathway": g["pathway"],
                        "node": node["id"],
                        "note": node.get("note", ""),
                        "source": source,
                        "red_flags": g.get("red_flags", []),
                        "validity_days": g.get("validity_days", {}),
                    })
    return out