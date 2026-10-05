export const DEMOS = [
    {
        key: "happy",
        icon: "🫁",
        title: "КТ лёгких — happy path",
        description:
            "Данные достаточны, формируется консультация специалиста.",
        file: "/static/mocks/happy.json"
    },
    {
        key: "conflict",
        icon: "⚠️",
        title: "Конфликт данных",
        description:
            "Размер находки отличается в report и conclusion.",
        file: "/static/mocks/conflict.json"
    },
    {
        key: "missing",
        icon: "🧩",
        title: "Недостаточно данных",
        description:
            "Не хватает обязательного контекста пациента.",
        file: "/static/mocks/missing-data.json"
    },
    {
        key: "no-guideline",
        icon: "📚",
        title: "Нет подходящего правила",
        description:
            "Для находки отсутствует релевантное правило.",
        file: "/static/mocks/no-guideline.json"
    },
    {
        key: "multiple",
        icon: "🧠",
        title: "Несколько находок",
        description:
            "Несколько независимых рекомендаций.",
        file: "/static/mocks/multiple.json"
    }
];


export async function loadDemoPayload(demo) {
    const response =
        await fetch(demo.file);

    if (!response.ok) {
        throw new Error(
            `Не удалось загрузить ${demo.file} (${response.status})`
        );
    }

    return await response.json();
}
