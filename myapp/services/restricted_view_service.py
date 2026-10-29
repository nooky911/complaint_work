"""Разрешённые поля ограниченного просмотра без файлов и служебных данных"""

from sqlalchemy import select, func, cast, String, or_
from sqlalchemy.orm import aliased
from fastapi import HTTPException

from myapp.models.repair_case_equipment import RepairCaseEquipment as Case
from myapp.models.auxiliaries import RegionalCenter
from myapp.models.warranty_work import WarrantyWork
from myapp.services.case_filter_service import CaseFilterService

BASIC = {
    "fault_date": "Дата неисправности",
    "locomotive_number": "Номер локомотива",
    "section_mask": "Секции",
    "mileage": "Пробег",
    "component_quantity": "Количество",
    "element_quantity": "Количество элементов",
    "new_component_quantity": "Количество установленных компонентов",
    "new_element_quantity": "Количество установленных элементов",
    "element_manufacture_date_new": "Дата изготовления установленного элемента",
    "component_serial_number_old": "Заводской номер",
    "component_manufacture_date_old": "Дата изготовления",
    "element_serial_number_old": "Номер элемента",
    "element_manufacture_date_old": "Дата изготовления элемента",
    "notes": "Примечание",
    "component_serial_number_new": "Номер установленного компонента",
    "component_manufacture_date_new": "Дата изготовления установленного компонента",
    "element_serial_number_new": "Номер установленного элемента",
}
RELATIONS = {
    "supplier": "Поставщик",
    "regional_center": "РЦ",
    "locomotive_model": "Модель",
    "component_equipment": "Оборудование",
    "element_equipment": "Элемент",
    "malfunction": "Неисправность",
    "fault_discovered_at": "Выявлено при",
    "repair_type": "Тип ремонта",
    "performed_by": "Кем устранено",
    "equipment_owner": "Владелец оборудования",
    "destination": "Демонтированное оборудование подлежит",
    "new_component_equipment": "Установленный компонент",
    "new_element_equipment": "Установленный элемент",
}
WARRANTY = {
    "notification_number": "№ уведомления",
    "notification_date": "Дата уведомления",
    "re_notification_number": "№ повторного уведомления",
    "re_notification_date": "Дата повторного уведомления",
    "response_letter_number": "№ ответа",
    "response_letter_date": "Дата ответа",
    "claim_act_number": "№ РА",
    "claim_act_date": "Дата РА",
    "work_completion_act_number": "№ АВР",
    "work_completion_act_date": "Дата АВР",
    "research_document": "Акт исследования",
}
SUMMARIES = {
    "notification_summary": "Содержание уведомления",
    "response_summary": "Содержание ответа",
    "decision_summary": "Решение",
    "research_status": "Результат исследования",
    "investigation_reason": "Причина неисправности",
}
LABELS = {"display_number": "№", **RELATIONS, **BASIC, **WARRANTY, **SUMMARIES}


def join_named_relations(stmt, fields, source, keys):
    """Подключает справочники и добавляет их названия в разрешённые поля"""
    for key in keys:
        relation = getattr(source, key)
        model = relation.property.mapper.class_
        alias = aliased(model)
        name = next(c.key for c in model.__table__.columns if c.key.endswith("_name"))
        fields[key] = getattr(alias, name)
        fields[f"{key}_id"] = getattr(source, f"{key}_id")
        stmt = stmt.outerjoin(alias, relation)
    return stmt


def query_for(user):
    """Строит выборку только разрешённых колонок и РЦ"""
    numbered = CaseFilterService._numbered_cases()
    fields = {"id": Case.id, "display_number": numbered.c.display_number}
    fields.update({key: getattr(Case, key) for key in BASIC})
    stmt = select().select_from(Case).join(numbered, numbered.c.id == Case.id)
    stmt = join_named_relations(stmt, fields, Case, RELATIONS)
    stmt = stmt.outerjoin(WarrantyWork, WarrantyWork.case_id == Case.id)
    fields.update({key: getattr(WarrantyWork, key) for key in WARRANTY})
    stmt = join_named_relations(stmt, fields, WarrantyWork, SUMMARIES)
    stmt = stmt.where(
        Case.regional_center.has(
            func.regexp_replace(
                RegionalCenter.regional_center_name, r"^РЦ\s*([0-9]+).*$", r"\1"
            ).in_(user.allowed_rc_names)
        )
    )
    return (
        stmt.with_only_columns(*(value.label(key) for key, value in fields.items())),
        fields,
    )


def apply_filters(stmt, fields, filters):
    """Применяет разрешённые фильтры общего Dashboard внутри доступных РЦ"""
    for key, values in filters.items():
        if values in (None, "", 0, []):
            continue
        if key in ("date_from", "date_to"):
            from datetime import date

            try:
                value = date.fromisoformat(values)
            except (TypeError, ValueError):
                raise HTTPException(422, "Некорректная дата")
            stmt = stmt.where(
                Case.fault_date >= value
                if key == "date_from"
                else Case.fault_date <= value
            )
            continue
        if key == "section_mask":
            if not isinstance(values, int) or not 1 <= values <= 7:
                raise HTTPException(422, "Некорректные секции")
            stmt = stmt.where(Case.section_mask.op("&")(values) != 0)
            continue
        if key in ("id", "supplier", "supplier_id") or key not in fields:
            raise HTTPException(422, "Недопустимый фильтр")
        if key == "display_number" and isinstance(values, int):
            values = [values]
        if not isinstance(values, list) or len(values) > 500:
            raise HTTPException(422, "Недопустимый фильтр")
        empty = None in values or "__empty__" in values
        conditions = [
            cast(fields[key], String).in_(
                [str(v) for v in values if v not in (None, "__empty__")]
            )
        ]
        if empty:
            conditions.append(
                or_(fields[key].is_(None), cast(fields[key], String) == "")
            )
        stmt = stmt.where(or_(*conditions))
    return stmt


async def list_cases(session, user, filters, page, size, sort_order="desc"):
    """Фильтрует разрешённые записи до подсчёта и пагинации"""
    stmt, fields = query_for(user)
    stmt = apply_filters(stmt, fields, filters)
    total = await session.scalar(select(func.count()).select_from(stmt.subquery()))
    order = Case.id.asc() if sort_order == "asc" else Case.id.desc()
    items = (
        (
            await session.execute(
                stmt.order_by(order).offset((page - 1) * size).limit(size)
            )
        )
        .mappings()
        .all()
    )
    return {"items": [dict(row) for row in items], "total": total}
