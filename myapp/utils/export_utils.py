from datetime import date

from myapp.constants.filter_constants import SECTION_MASKS


def format_serial_and_date(
    quantity: int | None, serials_str: str | None, dates_str: str | None
) -> str:
    """
    Форматирует серийные номера и даты в строку вида:
    '123 (01.01.2023)' или '2 шт. - 123 (01.01.23), 456 (02.01.23)'
    """
    if not serials_str and not dates_str:
        return ""

    # Разбиваем строки в списки, очищая от лишних пробелов
    serials = [s.strip() for s in str(serials_str).split(",")] if serials_str else []
    dates = [d.strip() for d in str(dates_str).split(",")] if dates_str else []

    # На случай, если массивы разной длины (одна дата забыта и т.д.)
    max_len = max(len(serials), len(dates))
    serials += [""] * (max_len - len(serials))
    dates += [""] * (max_len - len(dates))

    pairs = []
    for s, d in zip(serials, dates):
        if s and d:
            pairs.append(f"{s} ({d})")
        elif s:
            pairs.append(s)
        elif d:
            pairs.append(f"({d})")

    combined_str = ", ".join(pairs)

    # Если количество явно не передано, считаем по факту
    actual_qty = int(quantity) if quantity else len(pairs)

    if actual_qty >= 2:
        return f"{actual_qty} шт. - {combined_str}"

    return combined_str


def format_doc_number_and_date(doc_number: str | None, doc_date: date | None) -> str:
    """
    Форматирует документ в строку вида: '№123 от 01.01.2024'.
    Если чего-то не хватает, выводит только то, что есть.
    """
    if not doc_number and not doc_date:
        return ""

    d_str = doc_date.strftime("%d.%m.%Y") if doc_date else ""

    if doc_number and d_str:
        return f"№{doc_number} от {d_str}"

    return f"№{doc_number}" if doc_number else f"от {d_str}"


def format_section_mask(mask: int | None) -> str:
    """Преобразование битовой маски в буквенное обозначение секций"""

    if mask is None or not isinstance(mask, int):
        return "—"

    active_labels = [s["name"] for s in SECTION_MASKS if mask & s["bit"]]

    return ", ".join(active_labels) if active_labels else "—"
