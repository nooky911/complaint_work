from typing import Any
from sqlalchemy import select, distinct, and_, asc
from myapp.models.repair_case_equipment import RepairCaseEquipment
from myapp.models.warranty_work import WarrantyWork
from myapp.models.waybill_docs import WaybillDoc


def _add_case_document_joins(stmt):
    """Связывает запрос опций с обоими блоками документов по одному случаю"""
    return (
        stmt.outerjoin(WarrantyWork, RepairCaseEquipment.id == WarrantyWork.case_id)
        .outerjoin(WaybillDoc, RepairCaseEquipment.id == WaybillDoc.case_id)
    )


def process_query_results(result) -> list[Any]:
    """Универсальная обработка результатов запроса в список"""
    return [
        val
        for val in result.scalars().all()
        if val is not None and str(val).strip() != ""
    ]


async def execute_query_and_format_results(session, stmt) -> list[dict]:
    """Выполнить запрос и вернуть список id/name"""
    res = await session.execute(stmt)
    return [{"id": row[0], "name": row[1]} for row in res.all()]


async def get_distinct_values_with_join(
    session,
    column,
    join_model,
    join_condition,
    filtered_conditions=None,
) -> list[Any]:
    """Базовый метод для получения уникальных значений через JOIN"""
    stmt = (
        select(distinct(column))
        .select_from(join_model)
        .join(column.parent.class_, join_condition)
    )

    if join_model is WarrantyWork:
        stmt = stmt.outerjoin(WaybillDoc, RepairCaseEquipment.id == WaybillDoc.case_id)
    elif join_model is WaybillDoc:
        stmt = stmt.outerjoin(WarrantyWork, RepairCaseEquipment.id == WarrantyWork.case_id)
    elif join_model is RepairCaseEquipment:
        if column.parent.class_ is WarrantyWork:
            stmt = stmt.outerjoin(WaybillDoc, RepairCaseEquipment.id == WaybillDoc.case_id)
        elif column.parent.class_ is WaybillDoc:
            stmt = stmt.outerjoin(WarrantyWork, RepairCaseEquipment.id == WarrantyWork.case_id)
        else:
            stmt = _add_case_document_joins(stmt)

    if filtered_conditions:
        stmt = stmt.where(and_(*filtered_conditions))

    stmt = stmt.order_by(asc(column))
    res = await session.execute(stmt)
    return process_query_results(res)


async def get_distinct_values(
    session,
    column,
    filtered_conditions=None,
) -> list[Any]:
    """Получить уникальные значения колонки (без JOIN)"""
    if column.table is RepairCaseEquipment.__table__:
        stmt = _add_case_document_joins(
            select(distinct(column)).select_from(RepairCaseEquipment)
        ).where(column.isnot(None))
    else:
        stmt = select(distinct(column)).where(column.isnot(None))

    if filtered_conditions:
        stmt = stmt.where(and_(*filtered_conditions))

    stmt = stmt.order_by(asc(column))
    res = await session.execute(stmt)
    return process_query_results(res)


async def get_used_items_with_base_join(
    session,
    model,
    fk_column,
    name_column,
    base_model,
    filtered_conditions=None,
    additional_joins=None,
):
    """Базовый метод для получения используемых элементов справочника с JOIN"""
    stmt = select(model.id, name_column).join(base_model, fk_column == model.id)

    if base_model is RepairCaseEquipment:
        stmt = _add_case_document_joins(stmt)

    if additional_joins:
        for join_clause in additional_joins:
            stmt = stmt.join(*join_clause)

    stmt = stmt.distinct()

    if filtered_conditions:
        stmt = stmt.where(and_(*filtered_conditions))

    stmt = stmt.order_by(asc(name_column))
    return await execute_query_and_format_results(session, stmt)


async def get_used_items_with_intermediate_join(
    session,
    model,
    fk_column,
    name_column,
    intermediate_model,
    intermediate_case_id_field,
    base_model,
    filtered_conditions=None,
):
    """Получить используемые элементы справочника через промежуточную таблицу с JOIN к базовой модели"""
    stmt = (
        select(model.id, name_column)
        .join(intermediate_model, fk_column == model.id)
        .join(
            base_model,
            intermediate_case_id_field == base_model.id,
        )
        .distinct()
    )

    if base_model is RepairCaseEquipment:
        if intermediate_model is WarrantyWork:
            stmt = stmt.outerjoin(WaybillDoc, RepairCaseEquipment.id == WaybillDoc.case_id)
        elif intermediate_model is WaybillDoc:
            stmt = stmt.outerjoin(WarrantyWork, RepairCaseEquipment.id == WarrantyWork.case_id)

    if filtered_conditions:
        stmt = stmt.where(and_(*filtered_conditions))

    stmt = stmt.order_by(asc(name_column))
    return await execute_query_and_format_results(session, stmt)
