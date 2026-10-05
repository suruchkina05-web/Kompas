export const ACTION_LABELS = {
    specialist_consultation: "Консультация специалиста",
    additional_diagnostic_exam: "Дополнительное обследование",
    repeat_exam: "Повторное исследование",
    follow_up: "Наблюдение",
    physician_review: "Рассмотрение врачом",
    no_automatic_recommendation: "Автоматическая рекомендация не сформирована"
};


export const STATUS_LABELS = {
    ok: "Маршрут сформирован",
    insufficient_data: "Недостаточно данных",
    insufficient_guideline_context: "Недостаточно данных базы знаний",
    conflict_requires_review: "Требуется проверка из-за конфликта данных"
};

export const PRIORITY_LABELS = {
    urgent: "Срочный",
    high: "Высокий",
    medium: "Средний",
    low: "Низкий"
};

export const PATIENT_PRIORITY_LABELS = {
    urgent: "Как можно скорее",
    high: "Высокий приоритет",
    medium: "Планово",
    low: "Можно запланировать"
};

export const EVIDENCE_LABELS = {
    "findings[0].type": "Тип находки",
    "findings[0].size_mm": "Размер",
    "findings[0].volume_ml": "Объём",
    "findings[0].side": "Сторона",
    "findings[1].type": "Тип второй находки",
    "findings[1].size_mm": "Размер второй находки",
    "findings[1].volume_ml": "Объём второй находки",
    "findings[1].side": "Сторона второй находки",
    "patientContext.age": "Возраст",
    "patientContext.smokingHistory": "Статус курения",
    "patientContext.previousStudiesAvailable": "Предыдущие исследования",
    "patientContext.oncologicalHistory": "Онкологический анамнез"
};

export const VALUE_LABELS = {
    solid_pulmonary_nodule: "солидный лёгочный узел",
    pleural_effusion: "плевральный выпот",
    current_smoker: "текущий курильщик",
    former_smoker: "бывший курильщик",
    never_smoker: "никогда не курил",
    right: "справа",
    left: "слева",
    true: "доступны",
    false: "недоступны"
};

export const TEXT_REPLACEMENTS = {
    solid_pulmonary_nodule: "солидный лёгочный узел",
    pleural_effusion: "плевральный выпот",
    current_smoker: "текущий курильщик",
    former_smoker: "бывший курильщик",
    never_smoker: "никогда не курил",
    smokingHistory: "статус курения",
    previousStudiesAvailable: "наличие предыдущих исследований",
    oncologicalHistory: "онкологический анамнез",
    specialist_consultation: "консультация специалиста",
    physician_review: "рассмотрение врачом",
    additional_diagnostic_exam: "дополнительное диагностическое обследование",
    repeat_exam: "повторное исследование",
    follow_up: "наблюдение",
    no_automatic_recommendation: "автоматическая рекомендация не сформирована"
};
