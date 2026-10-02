# app/state.py
from typing import Optional
from app.schemas import PatientState


def merge_state(old: Optional[PatientState], new: PatientState) -> PatientState:
    """Второй документ дополняет карточку, а не затирает её."""
    if old is None:
        return new
    labs = {(l.code, l.taken_on): l for l in old.labs}
    for lab in new.labs:
        labs[(lab.code, lab.taken_on)] = lab
    complaints = list(dict.fromkeys(old.complaints + new.complaints))
    return PatientState(
        patient_id=old.patient_id,
        sex=old.sex,
        age=old.age,
        complaints=complaints,
        labs=list(labs.values()),
    )