from typing import Optional
from app.schemas import Finding, LabResult, PatientState


def _clean_list(items) -> list:
    """Вспомогательная функция: гарантирует, что на выходе будет список."""
    if items is None:
        return []
    if isinstance(items, list):
        return items
    return [items]


def merge_state(
    old_state: Optional[PatientState], new_state: PatientState
) -> PatientState:
    """Безопасно объединяет старое и новое состояние пациента,

    исключая появление None в списочных полях.
    """
    if not old_state:
        # Гарантируем чистый объект, если прошлого состояния не было
        return PatientState(
            patient_id=new_state.patient_id,
            sex=new_state.sex,
            age=new_state.age,
            complaints=_clean_list(new_state.complaints),
            labs=_clean_list(new_state.labs),
            findings=_clean_list(new_state.findings),
        )

    # 1. Объединяем жалобы (complaints) без дубликатов
    old_complaints = _clean_list(old_state.complaints)
    new_complaints = _clean_list(new_state.complaints)
    merged_complaints = list(
        dict.fromkeys([c for c in (old_complaints + new_complaints) if c])
    )

    # 2. Объединяем результаты анализов (labs)
    old_labs = _clean_list(old_state.labs)
    new_labs = _clean_list(new_state.labs)
    merged_labs = old_labs + new_labs

    # 3. Объединяем находки лучевой диагностики (findings)
    old_findings = _clean_list(old_state.findings)
    new_findings = _clean_list(new_state.findings)
    merged_findings = old_findings + new_findings

    # 4. Обновляем базовые атрибуты (пол, возраст), если они появились в новом документе
    sex = new_state.sex if new_state.sex is not None else old_state.sex
    age = new_state.age if new_state.age is not None else old_state.age
    patient_id = new_state.patient_id or old_state.patient_id

    return PatientState(
        patient_id=patient_id,
        sex=sex,
        age=age,
        complaints=merged_complaints,
        labs=merged_labs,
        findings=merged_findings,
    )