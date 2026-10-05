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

                    $("jsonFile").value = "";
                    $("fileName").textContent = "";

                    $("error").textContent =
                        "";

                } catch (error) {
                    selectedPayload = null;

                    $("runButton").disabled =
                        true;

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

        $("error").textContent =
            "";

    } catch (error) {
        selectedPayload = null;

        $("runButton").disabled =
            true;

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
            result,
            selectedPayload
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

$("runButton").addEventListener(
    "click",
    runRouting
);

$("resetButton").addEventListener(
    "click",
    resetApp
);



/* =========================================================
   RESULT VIEW TABS
   ========================================================= */

function switchResultView(view) {
    document
        .querySelectorAll(".view-tab")
        .forEach(tab => {
            const active = tab.dataset.view === view;
            tab.classList.toggle("is-active", active);
            tab.setAttribute("aria-selected", String(active));
        });

    document
        .querySelectorAll(".view-panel")
        .forEach(panel => {
            panel.hidden = panel.dataset.panel !== view;
        });
}

document
    .querySelectorAll(".view-tab")
    .forEach(tab => {
        tab.addEventListener("click", () => switchResultView(tab.dataset.view));
    });


/* =========================================================
   THEME
   ========================================================= */

function applyTheme(theme) {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem("kompas-theme", theme);

    const toggle = $("themeToggle");
    if (toggle) {
        toggle.textContent = theme === "dark" ? "Светлая тема" : "Тёмная тема";
    }
}

function initTheme() {
    const saved = localStorage.getItem("kompas-theme");
    const preferred = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    applyTheme(saved || preferred);

    $("themeToggle")?.addEventListener("click", () => {
        const current = document.documentElement.dataset.theme || "light";
        applyTheme(current === "dark" ? "light" : "dark");
    });
}

/* =========================================================
   INIT
   ========================================================= */

initTheme();
renderDemoGrid();
