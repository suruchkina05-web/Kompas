import {
    ACTION_LABELS,
    ACTION_ICONS,
    STATUS_LABELS,
    PRIORITY_LABELS,
    EVIDENCE_LABELS,
    VALUE_LABELS,
    TEXT_REPLACEMENTS
} from "./labels.js";


const $ = id => document.getElementById(id);


/* =========================================================
   HUMANIZATION
   ========================================================= */

function humanizeText(text) {
    if (!text) {
        return text;
    }

    let result =
        String(text);

    for (
        const [machineValue, humanValue]
        of Object.entries(TEXT_REPLACEMENTS)
    ) {
        result =
            result.replaceAll(
                machineValue,
                humanValue
            );
    }

    result = result
        .replaceAll("(true)", "(да)")
        .replaceAll("(false)", "(нет)");

    return result;
}


function humanizeMissingField(field) {
    const direct =
        EVIDENCE_LABELS[field];

    if (direct) {
        return direct;
    }

    return humanizeText(field);
}


function humanizeEvidence(raw) {
    const separator =
        raw.indexOf("=");

    if (separator === -1) {
        return humanizeText(raw);
    }

    const path =
        raw
            .slice(0, separator)
            .trim();

    const originalValue =
        raw
            .slice(separator + 1)
            .trim();

    const label =
        EVIDENCE_LABELS[path] ||
        humanizeText(path);

    let value =
        Object.prototype.hasOwnProperty.call(
            VALUE_LABELS,
            originalValue
        )
            ? VALUE_LABELS[originalValue]
            : humanizeText(originalValue);

    if (path.endsWith(".size_mm")) {
        value += " мм";
    }

    if (path.endsWith(".volume_ml")) {
        value += " мл";
    }

    if (path === "patientContext.age") {
        value += " лет";
    }

    return `${label}: ${value}`;
}


/* =========================================================
   ALERTS
   ========================================================= */

function renderListAlert(
    containerId,
    title,
    items,
    kind,
    itemFormatter = humanizeText
) {
    const root =
        $(containerId);

    root.innerHTML =
        "";

    if (
        !Array.isArray(items) ||
        !items.length
    ) {
        return;
    }

    const box =
        document.createElement("div");

    box.className =
        "alert alert--" + kind;

    const heading =
        document.createElement("strong");

    heading.textContent =
        title;

    const ul =
        document.createElement("ul");

    items.forEach(item => {
        const li =
            document.createElement("li");

        li.textContent =
            itemFormatter(item);

        ul.appendChild(li);
    });

    box.append(
        heading,
        ul
    );

    root.appendChild(box);
}


/* =========================================================
   RECOMMENDATION
   ========================================================= */

function renderRecommendation(rec) {
    const card =
        document.createElement("article");

    card.className =
        "recommendation";

    const head =
        document.createElement("div");

    head.className =
        "recommendation__head";

    const icon =
        document.createElement("div");

    icon.className =
        "recommendation__icon";

    icon.textContent =
        ACTION_ICONS[
            rec.action_type
        ] || "📌";

    const main =
        document.createElement("div");

    main.className =
        "recommendation__main";

    const title =
        document.createElement("strong");

    title.className =
        "recommendation__title";

    title.textContent =
        ACTION_LABELS[
            rec.action_type
        ] ||
        humanizeText(
            rec.action_type
        );

    const meta =
        document.createElement("div");

    meta.className =
        "meta";

    if (rec.target) {
        const badge =
            document.createElement("span");

        badge.className =
            "badge";

        badge.textContent =
            humanizeText(
                rec.target
            );

        meta.appendChild(
            badge
        );
    }

    if (rec.priority) {
        const badge =
            document.createElement("span");

        badge.className =
            "badge badge--priority badge--" +
            rec.priority;

        badge.textContent =
            "Приоритет: " +
            (
                PRIORITY_LABELS[
                    rec.priority
                ] ||
                humanizeText(
                    rec.priority
                )
            );

        meta.appendChild(
            badge
        );
    }

    main.append(
        title,
        meta
    );

    head.append(
        icon,
        main
    );

    card.appendChild(
        head
    );

    if (rec.reason) {
        const reason =
            document.createElement("p");

        reason.className =
            "reason";

        reason.textContent =
            humanizeText(
                rec.reason
            );

        card.appendChild(
            reason
        );
    }

    if (
        Array.isArray(rec.evidence) &&
        rec.evidence.length
    ) {
        const evidence =
            document.createElement("div");

        evidence.className =
            "evidence";

        const heading =
            document.createElement("strong");

        heading.textContent =
            "На основании данных";

        const ul =
            document.createElement("ul");

        rec.evidence.forEach(
            item => {
                const li =
                    document.createElement("li");

                li.textContent =
                    humanizeEvidence(
                        item
                    );

                ul.appendChild(
                    li
                );
            }
        );

        evidence.append(
            heading,
            ul
        );

        card.appendChild(
            evidence
        );
    }

    if (rec.source) {
        const source =
            document.createElement("div");

        source.className =
            "source";

        source.textContent =
            "Источник правила: " +
            rec.source;

        card.appendChild(
            source
        );
    }

    return card;
}


/* =========================================================
   RESULT
   ========================================================= */

export function renderResult(data) {
    $("result").hidden =
        false;

    const status =
        $("status");

    status.className =
        "status status--" +
        data.status;

    status.textContent =
        STATUS_LABELS[
            data.status
        ] ||
        humanizeText(
            data.status
        );

    renderListAlert(
        "warnings",
        "⚠️ Требуется внимание",
        data.warnings,
        "bad",
        humanizeText
    );

    renderListAlert(
        "missing",
        "Не хватает данных",
        data.missing_data,
        "warn",
        humanizeMissingField
    );

    const root =
        $("recommendations");

    root.innerHTML =
        "";

    const recommendations =
        Array.isArray(
            data.recommendations
        )
            ? data.recommendations
            : [];

    if (
        !recommendations.length
    ) {
        const empty =
            document.createElement("div");

        empty.className =
            "empty";

        empty.textContent =
            "Автоматические рекомендации отсутствуют.";

        root.appendChild(
            empty
        );

    } else {
        recommendations.forEach(
            rec =>
                root.appendChild(
                    renderRecommendation(
                        rec
                    )
                )
        );
    }

    /*
     * Технический JSON ответа намеренно
     * НЕ humanize'им.
     * Здесь остаётся исходный машинный ответ.
     */
    $("rawResponse").textContent =
        JSON.stringify(
            data,
            null,
            2
        );

    $("result").scrollIntoView({
        behavior: "smooth",
        block: "start"
    });
}
