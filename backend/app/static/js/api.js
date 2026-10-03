export async function routeStudy(payload) {
    const response =
        await fetch(
            "/api/v1/routing",
            {
                method: "POST",
                headers: {
                    "Content-Type":
                        "application/json"
                },
                body:
                    JSON.stringify(payload)
            }
        );

    let data = {};

    try {
        data =
            await response.json();
    } catch (_) {
        data = {};
    }

    if (!response.ok) {
        const detail =
            typeof data.detail === "string"
                ? data.detail
                : JSON.stringify(
                    data.detail ||
                    "Ошибка сервера"
                );

        throw new Error(detail);
    }

    return data;
}
