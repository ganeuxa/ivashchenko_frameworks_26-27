from collections.abc import Iterable
from datetime import datetime

DATE_FORMAT = "%Y-%m-%d %H:%M"


def input_int(prompt: str, min_value: int = 1) -> int:
    """Спрашивает целое число, пока не введут правильное."""
    while True:
        raw_value = input(prompt).strip()
        try:
            number = int(raw_value)
        except ValueError:
            print("Нужно ввести целое число")
            continue
        if number < min_value:
            print(f"Число должно быть не меньше {min_value}")
            continue
        return number


def input_text(prompt: str) -> str:
    """Спрашивает непустую строку."""
    while True:
        text = input(prompt).strip()
        if text:
            return text
        print("Строка не должна быть пустой")


def next_id(ids: Iterable[int]) -> int:
    """Возвращает следующий свободный номер."""
    return max(ids, default=0) + 1


def now_str() -> str:
    """Текущие дата и время строкой."""
    return datetime.now().strftime(DATE_FORMAT)
