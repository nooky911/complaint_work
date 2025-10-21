from datetime import date


def calculate_status(
        n_id: int | None = None,
        r_id: int | None = None,
        d_id: int | None = None,
        comp_act_number: str | None = None,
        claim_act_number: str | None = None,
        re_n_number: str | None = None,
        re_n_date: date | None = None,
        n_date: date | None = None
) -> str:
    """Вычисление статуса рекламационной работы"""
    today = date.today()

    if not n_id and not r_id and not d_id and not re_n_number:
        return "Ожидает уведомление поставщика"

    if (d_id == 9 or
            n_id in [1, 2, 3, 5, 6, 9, 10, 11, 13, 14] and d_id or
            n_id in [4, 8, 12, 13] or
            r_id == 14 and d_id or
            r_id == 13 and d_id == 9):
        return "Завершено"

    if (r_id in [6, 7, 11] and not comp_act_number or
            d_id in [3, 4, 5] and not comp_act_number):
        return "Ожидает АВР"

    # Проверки на None для дат
    days_since_notification = (today - n_date).days if n_date else None
    days_since_re_notification = (today - re_n_date).days if re_n_date else None

    if (r_id in [1, 2, 3, 4, 8, 9, 10, 12] and not d_id or
            n_id in [2, 3, 5, 9,
                     11] and not r_id and days_since_notification and days_since_notification >= 4 and not d_id or
            re_n_number and not r_id and days_since_re_notification and days_since_re_notification >= 4 and not d_id or
            n_id == 13 and r_id == 2 and not claim_act_number):
        return "Ожидает рекламационный акт"

    if (n_id in [2, 3, 5, 9, 11] and not r_id and not d_id or
            re_n_number and not r_id and days_since_re_notification and days_since_re_notification < 4 and not d_id):
        return "Ожидает ответа поставщика"

    if n_id in [1, 6, 10] and not re_n_number and not r_id:
        return "Ожидает повторного уведомления поставщика"

    if d_id:
        return "Решение принято"
    if r_id:
        return "Ответ получен"
    if n_id:
        return "Уведомление отправлено"

    return "Другое"