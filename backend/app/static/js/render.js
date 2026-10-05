import {
    ACTION_LABELS,
    STATUS_LABELS,
    PRIORITY_LABELS,
    PATIENT_PRIORITY_LABELS,
    EVIDENCE_LABELS,
    VALUE_LABELS,
    TEXT_REPLACEMENTS
} from "./labels.js";

const $ = id => document.getElementById(id);

function humanizeText(text) {
    if (!text) return text;
    let result = String(text);
    for (const [machineValue, humanValue] of Object.entries(TEXT_REPLACEMENTS)) {
        result = result.replaceAll(machineValue, humanValue);
    }
    return result
        .replaceAll("(true)", "(да)")
        .replaceAll("(false)", "(нет)");
}

function humanizeMissingField(field) {
    return EVIDENCE_LABELS[field] || humanizeText(field);
}

function humanizeEvidence(raw) {
    const separator = raw.indexOf("=");
    if (separator === -1) return humanizeText(raw);

    const path = raw.slice(0, separator).trim();
    const originalValue = raw.slice(separator + 1).trim();
    const label = EVIDENCE_LABELS[path] || humanizeText(path);

    let value = Object.prototype.hasOwnProperty.call(VALUE_LABELS, originalValue)
        ? VALUE_LABELS[originalValue]
        : humanizeText(originalValue);

    if (path.endsWith(".size_mm")) value += " мм";
    if (path.endsWith(".volume_ml")) value += " мл";
    if (path === "patientContext.age") value += " лет";

    return `${label}: ${value}`;
}

function renderListAlert(containerId, title, items, kind, itemFormatter = humanizeText) {
    const root = $(containerId);
    root.innerHTML = "";
    if (!Array.isArray(items) || !items.length) return;

    const box = document.createElement("div");
    box.className = "alert alert--" + kind;

    const heading = document.createElement("strong");
    heading.textContent = title;

    const ul = document.createElement("ul");
    items.forEach(item => {
        const li = document.createElement("li");
        li.textContent = itemFormatter(item);
        ul.appendChild(li);
    });

    box.append(heading, ul);
    root.appendChild(box);
}

function recommendationTitle(rec) {
    return ACTION_LABELS[rec.action_type] || humanizeText(rec.action_type);
}


function patientSafeReason(rec) {
    const safeReasons = {
        specialist_consultation: "По результатам исследования рекомендуется консультация профильного специалиста. Врач оценит результаты в клиническом контексте и определит дальнейшие шаги.",
        additional_diagnostic_exam: "Для уточнения результатов рекомендуется пройти дополнительное обследование. Конкретный объём обследования определит врач.",
        repeat_exam: "Рекомендуется повторное исследование в указанный срок, чтобы врач мог оценить изменения в динамике.",
        follow_up: "Рекомендуется плановое наблюдение. Врач определит подходящий график контроля.",
        physician_review: "Результат исследования рекомендуется обсудить с врачом. Он сопоставит его с вашими данными и определит, нужны ли дополнительные действия.",
        no_automatic_recommendation: "Автоматический маршрут не сформирован. Результат рекомендуется обсудить с врачом."
    };

    return safeReasons[rec.action_type] ||
        "Результат исследования рекомендуется обсудить с врачом для определения дальнейших действий.";
}

function patientDoctorTarget(rec) {
    if (rec.target) return humanizeText(rec.target);
    if (rec.action_type === "physician_review") return "Лечащий врач";
    return null;
}

function renderPatientRecommendation(rec) {
    const card = document.createElement("article");
    card.className = "recommendation recommendation--patient";

    const body = document.createElement("div");
    body.className = "recommendation__main";

    const title = document.createElement("strong");
    title.className = "recommendation__title recommendation__title--patient";
    title.textContent = recommendationTitle(rec);
    body.appendChild(title);

    const doctorTarget = patientDoctorTarget(rec);
    if (doctorTarget) {
        const doctorBox = document.createElement("div");
        doctorBox.className = "patient-doctor-box";

        const doctorLabel = document.createElement("span");
        doctorLabel.className = "patient-doctor-box__label";
        doctorLabel.textContent = "К кому обратиться";

        const doctorValue = document.createElement("span");
        doctorValue.className = "patient-doctor-box__value";
        doctorValue.textContent = doctorTarget;

        doctorBox.append(doctorLabel, doctorValue);
        body.appendChild(doctorBox);
    }

    if (rec.priority) {
        const meta = document.createElement("div");
        meta.className = "meta";

        const priority = document.createElement("span");
        priority.className = `badge badge--patient-priority badge--${rec.priority}`;
        priority.textContent = PATIENT_PRIORITY_LABELS[rec.priority] || PRIORITY_LABELS[rec.priority] || humanizeText(rec.priority);
        meta.appendChild(priority);
        body.appendChild(meta);
    }

    const reason = document.createElement("p");
    reason.className = "reason reason--patient";
    reason.textContent = patientSafeReason(rec);
    body.appendChild(reason);

    card.appendChild(body);
    return card;
}
function cleanDoctorReason(text) {
    if (!text) return "";

    return humanizeText(text)
        .replace(/\btarget\b/gi, "профильного специалиста")
        .replace(/\bpriority\b/gi, "приоритета")
        .replace(/с указанным профильного специалиста и приоритета/gi, "с указанными специалистом и приоритетом")
        .replace(/с указанным специалистом и приоритетом/gi, "с указанными специалистом и приоритетом")
        .replace(/\s+/g, " ")
        .trim();
}

function doctorActionSummary(rec) {
    const target = rec.target ? humanizeText(rec.target) : null;
    const priority = rec.priority
        ? (PRIORITY_LABELS[rec.priority] || humanizeText(rec.priority))
        : null;

    if (rec.action_type === "specialist_consultation") {
        return target
            ? `Рекомендуется консультация: ${target}.`
            : "Рекомендуется консультация профильного специалиста.";
    }

    if (rec.action_type === "physician_review") {
        return "Рекомендуется клиническая оценка результата лечащим врачом.";
    }

    if (rec.action_type === "additional_diagnostic_exam") {
        return "Рекомендуется дополнительное диагностическое обследование.";
    }

    if (rec.action_type === "repeat_exam") {
        return "Рекомендуется повторное исследование в установленный срок.";
    }

    if (rec.action_type === "follow_up") {
        return "Рекомендуется динамическое наблюдение.";
    }

    return "Рекомендуется оценить результат в клиническом контексте.";
}

function renderDoctorRecommendation(rec) {
    const card = document.createElement("article");
    card.className = "recommendation recommendation--doctor";

    const main = document.createElement("div");
    main.className = "recommendation__main";

    const title = document.createElement("strong");
    title.className = "recommendation__title";
    title.textContent = recommendationTitle(rec);

    const meta = document.createElement("div");
    meta.className = "meta";

    if (rec.target) {
        const badge = document.createElement("span");
        badge.className = "badge";
        badge.textContent = humanizeText(rec.target);
        meta.appendChild(badge);
    }

    if (rec.priority) {
        const badge = document.createElement("span");
        badge.className = "badge badge--priority badge--" + rec.priority;
        badge.textContent = "Приоритет: " + (PRIORITY_LABELS[rec.priority] || humanizeText(rec.priority));
        meta.appendChild(badge);
    }

    main.append(title, meta);
    card.appendChild(main);

    const analysis = document.createElement("div");
    analysis.className = "doctor-analysis";

    const actionBlock = document.createElement("section");
    actionBlock.className = "doctor-analysis__block";

    const actionTitle = document.createElement("strong");
    actionTitle.className = "doctor-analysis__label";
    actionTitle.textContent = "Рекомендуемое действие";

    const actionText = document.createElement("p");
    actionText.className = "doctor-analysis__text";
    actionText.textContent = doctorActionSummary(rec);

    actionBlock.append(actionTitle, actionText);
    analysis.appendChild(actionBlock);

    if (rec.reason) {
        const reasonBlock = document.createElement("section");
        reasonBlock.className = "doctor-analysis__block";

        const reasonTitle = document.createElement("strong");
        reasonTitle.className = "doctor-analysis__label";
        reasonTitle.textContent = "Клиническое обоснование";

        const reason = document.createElement("p");
        reason.className = "doctor-analysis__text";
        reason.textContent = cleanDoctorReason(rec.reason);

        reasonBlock.append(reasonTitle, reason);
        analysis.appendChild(reasonBlock);
    }

    if (Array.isArray(rec.evidence) && rec.evidence.length) {
        const evidenceBlock = document.createElement("section");
        evidenceBlock.className = "doctor-analysis__block doctor-analysis__block--evidence";

        const heading = document.createElement("strong");
        heading.className = "doctor-analysis__label";
        heading.textContent = "Ключевые данные, повлиявшие на маршрут";

        const grid = document.createElement("div");
        grid.className = "doctor-evidence-grid";

        rec.evidence.forEach(item => {
            const row = document.createElement("div");
            row.className = "doctor-evidence-item";

            const text = humanizeEvidence(item);
            const separator = text.indexOf(":");

            if (separator !== -1) {
                const key = document.createElement("span");
                key.className = "doctor-evidence-item__key";
                key.textContent = text.slice(0, separator).trim();

                const value = document.createElement("span");
                value.className = "doctor-evidence-item__value";
                value.textContent = text.slice(separator + 1).trim();

                row.append(key, value);
            } else {
                row.textContent = text;
            }

            grid.appendChild(row);
        });

        evidenceBlock.append(heading, grid);
        analysis.appendChild(evidenceBlock);
    }

    if (rec.source) {
        const sourceBlock = document.createElement("section");
        sourceBlock.className = "doctor-analysis__source";

        const label = document.createElement("span");
        label.textContent = "Источник правила";

        const value = document.createElement("code");
        value.textContent = rec.source;

        sourceBlock.append(label, value);
        analysis.appendChild(sourceBlock);
    }

    card.appendChild(analysis);
    return card;
}
function renderRecommendations(rootId, recommendations, renderer) {
    const root = $(rootId);
    root.innerHTML = "";

    if (!recommendations.length) {
        const empty = document.createElement("div");
        empty.className = "empty";
        empty.textContent = "Автоматические рекомендации отсутствуют.";
        root.appendChild(empty);
        return;
    }

    recommendations.forEach(rec => root.appendChild(renderer(rec)));
}

function renderSystemSources(recommendations) {
    const root = $("systemSources");
    root.innerHTML = "";

    const sources = [...new Set(
        recommendations
            .map(rec => rec.source)
            .filter(Boolean)
    )];

    if (!sources.length) return;

    const box = document.createElement("div");
    box.className = "system-source-box";
    const label = document.createElement("strong");
    label.textContent = "Сработавшие источники правил";
    const list = document.createElement("div");
    list.className = "source-chips";

    sources.forEach(source => {
        const chip = document.createElement("span");
        chip.className = "source-chip";
        chip.textContent = source;
        list.appendChild(chip);
    });

    box.append(label, list);
    root.appendChild(box);
}

export function renderResult(data, inputPayload = null) {
    $("result").hidden = false;

    const status = $("status");
    status.className = "status status--" + data.status;
    status.textContent = STATUS_LABELS[data.status] || humanizeText(data.status);

    renderListAlert("warnings", "Требуется внимание", data.warnings, "bad", humanizeText);
    renderListAlert("missing", "Не хватает данных", data.missing_data, "warn", humanizeMissingField);

    const recommendations = Array.isArray(data.recommendations) ? data.recommendations : [];

    renderRecommendations("patientRecommendations", recommendations, renderPatientRecommendation);
    renderRecommendations("doctorRecommendations", recommendations, renderDoctorRecommendation);

    const patientWarnings = [];
    if (Array.isArray(data.warnings) && data.warnings.length) {
        patientWarnings.push("Маршрут требует дополнительной проверки врачом.");
    }
    if (Array.isArray(data.missing_data) && data.missing_data.length) {
        patientWarnings.push("Для окончательного маршрута врачу могут понадобиться дополнительные данные.");
    }
    renderListAlert("patientWarnings", "Обратите внимание", patientWarnings, "warn", humanizeText);

    $("rawInput").textContent = inputPayload ? JSON.stringify(inputPayload, null, 2) : "Входной JSON недоступен.";
    $("rawResponse").textContent = JSON.stringify(data, null, 2);
    renderSystemSources(recommendations);

    $("result").scrollIntoView({ behavior: "smooth", block: "start" });
}
