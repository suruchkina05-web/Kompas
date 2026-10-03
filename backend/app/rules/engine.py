import json
import re
from pathlib import Path

from app.schemas import PatientState

STEPS_FILE = Path(__file__).parent / "steps.json"


def load_steps() -> dict:
    """Загружает базу шагов маршрутизации из JSON-файла."""
    if not STEPS_FILE.exists():
        return {}
    with open(STEPS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _extract_nodule_size(text: str) -> float | None:
    """Извлекает размер очага в мм из текста (например, 'очаг 8 мм' или '8.5мм')."""
    match = re.search(r"(\d+(?:[\.,]\d+)?)\s*мм", text.lower())
    if match:
        return float(match.group(1).replace(",", "."))
    return None


def evaluate_rules(state: PatientState) -> list[str]:
    """Анализирует findings пациента и возвращает список сработавших step_id."""
    triggered = []

    for f in state.findings:
        finding_text = (f.finding or "").lower()
        bi_rads = (f.bi_rads or "").upper().strip()
        modality = (f.modality or "").strip()

        # --- 1. Маммография (BI-RADS) ---
        if modality == "Mammography" or "маммогр" in finding_text:
            if "BI-RADS 4" in bi_rads or "BI-RADS 5" in bi_rads or "bi-rads 4" in finding_text or "bi-rads 5" in finding_text:
                if "mammography_bi_rads_4_5" not in triggered:
                    triggered.append("mammography_bi_rads_4_5")
            elif "BI-RADS 3" in bi_rads or "bi-rads 3" in finding_text:
                if "mammography_bi_rads_3" not in triggered:
                    triggered.append("mammography_bi_rads_3")

        # --- 2. Компьютерная томография (КТ ОГК / очаги) ---
        if modality == "CT" or "кт" in finding_text or "томограф" in finding_text:
            if "очаг" in finding_text or "образование" in finding_text or "узел" in finding_text:
                size_mm = _extract_nodule_size(finding_text)
                if size_mm is not None:
                    if size_mm > 6.0:
                        if "ct_lung_nodule_gt_6mm" not in triggered:
                            triggered.append("ct_lung_nodule_gt_6mm")
                    else:
                        if "ct_lung_nodule_lt_6mm" not in triggered:
                            triggered.append("ct_lung_nodule_lt_6mm")
                else:
                    if "> 6" in finding_text or "более 6" in finding_text:
                        if "ct_lung_nodule_gt_6mm" not in triggered:
                            triggered.append("ct_lung_nodule_gt_6mm")
                    else:
                        if "ct_lung_nodule_lt_6mm" not in triggered:
                            triggered.append("ct_lung_nodule_lt_6mm")

        # --- 3. Рентгенография (X-ray / инфильтрация / пневмония) ---
        if modality == "X-ray" or "рентген" in finding_text or "инфильтрат" in finding_text:
            if "инфильтрат" in finding_text or "пневмон" in finding_text or "затенение" in finding_text:
                if "xray_pneumonia_infiltrate" not in triggered:
                    triggered.append("xray_pneumonia_infiltrate")

    return triggered