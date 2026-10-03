import {
    DEMOS,
    loadDemoPayload
} from "./js/demos.js";

import {
    routeStudy
} from "./js/api.js";

import {
    renderResult
} from "./js/render.js";


const $ = id => document.getElementById(id);

let selectedPayload = null;


/* =========================================================
   DEMO GRID
   ========================================================= */

function renderDemoGrid() {
    const root = $("demoGrid");

    DEMOS.forEach(demo => {
        const button =
            document.createElement("button");

        button.type = "button";
        button.className = "demo-card";
        button.dataset.key = demo.key;

        const icon =
            document.createElement("span");

        icon.className =
            "demo-card__icon";

        icon.textContent =
            demo.icon;

        const title =
            document.createElement("strong");

        title.textContent =
            demo.title;

        const desc =
            document.createElement("span");

        desc.className =
            "demo-card__desc";

        desc.textContent =
            demo.description;

        button.append(
            icon,
            title,
            desc
        );

        button.addEventListener(
            "click",
            async () => {
                try {
                    document
                        .querySelectorAll(".demo-card")
                        .forEach(item =>
                            item.classList.remove("selected")
                        );

                    button.classList.add("selected");

                    selectedPayload =
                        await loadDemoPayload(demo);

                    $("selectedCase").hidden =
                        false;

                    $("selectedCase").textContent =
                        "Выбран сценарий: " +
                        demo.title;

                    $("runButton").disabled =
                        false;

                    $("showInputButton").hidden =
                        false;

                    $("jsonFile").value = "";
                    $("fileName").textContent = "";

                    $("inputJsonBox").hidden =
                        true;

                    $("rawInput").textContent =
                        "";

                    $("error").textContent =
                        "";

                } catch (error) {
                    selectedPayload = null;

                    $("runButton").disabled =
                        true;

                    $("showInputButton").hidden =
                        true;

                    $("inputJsonBox").hidden =
                        true;

                    $("rawInput").textContent =
                        "";

                    $("error").textContent =
                        "Не удалось загрузить сценарий: " +
                        error.message;
                }
            }
        );

        root.appendChild(button);
    });
}


/* =========================================================
   INPUT JSON VIEW
   ========================================================= */

function toggleInputJson() {
    if (!selectedPayload) {
        return;
    }

    $("rawInput").textContent =
        JSON.stringify(
            selectedPayload,
            null,
            2
        );

    $("inputJsonBox").hidden =
        !$("inputJsonBox").hidden;
}


/* =========================================================
   FILE UPLOAD
   ========================================================= */

async function handleFileUpload(event) {
    const file =
        event.target.files?.[0];

    if (!file) {
        return;
    }

    try {
        const payload =
            JSON.parse(
                await file.text()
            );

        if (
            typeof payload !== "object" ||
            payload === null ||
            Array.isArray(payload)
        ) {
            throw new Error(
                "Корневой элемент JSON должен быть объектом."
            );
        }

        selectedPayload = payload;

        document
            .querySelectorAll(".demo-card")
            .forEach(item =>
                item.classList.remove("selected")
            );

        $("selectedCase").hidden =
            false;

        $("selectedCase").textContent =
            "Загружен файл: " +
            file.name;

        $("fileName").textContent =
            file.name;

        $("runButton").disabled =
            false;

        $("showInputButton").hidden =
            false;

        $("inputJsonBox").hidden =
            true;

        $("rawInput").textContent =
            "";

        $("error").textContent =
            "";

    } catch (error) {
        selectedPayload = null;

        $("runButton").disabled =
            true;

        $("showInputButton").hidden =
            true;

        $("inputJsonBox").hidden =
            true;

        $("rawInput").textContent =
            "";

        $("error").textContent =
            "Не удалось загрузить JSON: " +
            error.message;
    }
}


/* =========================================================
   RUN
   ========================================================= */

async function runRouting() {
    if (!selectedPayload) {
        return;
    }

    $("runButton").disabled =
        true;

    $("busy").textContent =
        "Анализируем исследование и строим маршрут…";

    $("error").textContent =
        "";

    try {
        const result =
            await routeStudy(
                selectedPayload
            );

        renderResult(
            result
        );

    } catch (error) {
        $("error").textContent =
            "Не получилось: " +
            error.message;

    } finally {
        $("runButton").disabled =
            false;

        $("busy").textContent =
            "";
    }
}


/* =========================================================
   RESET
   ========================================================= */

function resetApp() {
    selectedPayload = null;

    $("runButton").disabled =
        true;

    $("jsonFile").value =
        "";

    $("fileName").textContent =
        "";

    $("selectedCase").hidden =
        true;

    $("selectedCase").textContent =
        "";

    $("showInputButton").hidden =
        true;

    $("inputJsonBox").hidden =
        true;

    $("rawInput").textContent =
        "";

    $("result").hidden =
        true;

    $("error").textContent =
        "";

    $("busy").textContent =
        "";

    document
        .querySelectorAll(".demo-card")
        .forEach(item =>
            item.classList.remove("selected")
        );
}


/* =========================================================
   EVENTS
   ========================================================= */

$("uploadButton").addEventListener(
    "click",
    () => $("jsonFile").click()
);

$("jsonFile").addEventListener(
    "change",
    handleFileUpload
);

$("showInputButton").addEventListener(
    "click",
    toggleInputJson
);

$("runButton").addEventListener(
    "click",
    runRouting
);

$("resetButton").addEventListener(
    "click",
    resetApp
);


/* =========================================================
   INIT
   ========================================================= */

renderDemoGrid();
