import json
from pathlib import Path
from typing import Any

from app.schemas import PatientState

BASE_DIR = Path(__file__).parent
STEPS_FILE = BASE_DIR / "steps.json"
RULES_FILE = BASE_DIR / "mammography_rules.json"
SOURCES_FILE = BASE_DIR / "clinical_sources.json"


def _load_json(path: Path, default):
    if not path.exists():
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_steps() -> dict:
    return _load_json(STEPS_FILE, {})


def load_rules() -> list[dict]:
    data = _load_json(RULES_FILE, [])
    return data if isinstance(data, list) else []


def load_sources() -> dict:
    return _load_json(SOURCES_FILE, {})


def _latest_mammography(state: PatientState):
    return state.mammography[-1] if state.mammography else None


def _breasts(state: PatientState):
    exam = _latest_mammography(state)
    if not exam:
        return []
    return [exam.right_breast, exam.left_breast]


def _all_birads(state: PatientState) -> list[int]:
    return [b.birads for b in _breasts(state) if b.birads is not None]


def _all_acr(state: PatientState) -> list[str]:
    return [b.acr_density for b in _breasts(state) if b.acr_density]


def _all_findings_text(state: PatientState) -> str:
    values: list[str] = []
    for breast in _breasts(state):
        values.extend(breast.findings)
        values.extend(breast.locations)
    exam = _latest_mammography(state)
    if exam:
        if exam.comparison_with_previous:
            values.append(exam.comparison_with_previous)
        if exam.recommendation:
            values.append(exam.recommendation)
    return " ".join(values).lower()


def _match_conditions(state: PatientState, cond: dict[str, Any]) -> bool:
    if not isinstance(cond, dict):
        return False

    any_of = cond.get("any_of")
    if any_of is not None:
        if not isinstance(any_of, list) or not any(_match_conditions(state, x) for x in any_of if isinstance(x, dict)):
            return False

    all_of = cond.get("all_of")
    if all_of is not None:
        if not isinstance(all_of, list) or not all(_match_conditions(state, x) for x in all_of if isinstance(x, dict)):
            return False

    if "clinical_context_in" in cond and state.clinical_context not in cond["clinical_context_in"]:
        return False
    if "sex_in" in cond and state.sex not in cond["sex_in"]:
        return False
    if "age_gte" in cond and (state.age is None or state.age < int(cond["age_gte"])):
        return False
    if "age_lt" in cond and (state.age is None or state.age >= int(cond["age_lt"])):
        return False
    if "has_mammography" in cond and bool(state.mammography) is not bool(cond["has_mammography"]):
        return False

    birads = _all_birads(state)
    if "any_birads_in" in cond and not any(x in cond["any_birads_in"] for x in birads):
        return False
    if "any_birads_not_in" in cond:
        allowed = set(cond["any_birads_not_in"])
        if not birads or not any(x not in allowed for x in birads):
            return False
    if "all_birads_in" in cond:
        allowed = set(cond["all_birads_in"])
        if not birads or not all(x in allowed for x in birads):
            return False

    acr = _all_acr(state)
    if "any_acr_in" in cond and not any(x in cond["any_acr_in"] for x in acr):
        return False

    if cond.get("has_any_breast_finding") is True:
        if not any(b.findings for b in _breasts(state)):
            return False

    if "finding_keywords_any" in cond:
        text = _all_findings_text(state)
        if not any(str(k).lower() in text for k in cond["finding_keywords_any"]):
            return False

    if "no_response_to_antiinflammatory_treatment_is" in cond:
        expected = bool(cond["no_response_to_antiinflammatory_treatment_is"])
        if state.no_response_to_antiinflammatory_treatment is not expected:
            return False

    if "metastatic_sites_intersect" in cond:
        sites = " ".join(state.metastatic_sites).lower()
        if not any(str(site).lower() in sites for site in cond["metastatic_sites_intersect"]):
            return False

    return True


def evaluate_rules(state: PatientState) -> list[str]:
    """Возвращает только шаги, подтвержденные активными JSON-правилами маммографии."""
    triggered: list[str] = []
    for rule in load_rules():
        if not rule.get("enabled", False):
            continue
        conditions = rule.get("conditions") or {}
        if _match_conditions(state, conditions):
            step_id = str(rule.get("step_id") or "").strip()
            if step_id and step_id not in triggered:
                triggered.append(step_id)
    return triggered
