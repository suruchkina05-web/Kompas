"""Быстрая проверка подключения backend к Qwen в Yandex AI Studio."""
from app.llm import ask

if __name__ == "__main__":
    print(ask("Ответь ровно одним словом: OK", system="Следуй инструкции пользователя."))
