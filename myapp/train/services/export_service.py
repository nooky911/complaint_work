import asyncio
import urllib.parse
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from sqlalchemy import select, func

from myapp.database.query_builders.query_case_builders import load_detail_relations
from myapp.loco.services.export_service import ExportService
from myapp.services.omega_services.passport_case_service import PassportCaseService
from myapp.models.repair_case_equipment import RepairCaseEquipment as Case
from myapp.models.product_passports import ProductPassportNode
from myapp.train.models.case_details import TrainCaseDetails
from myapp.train.models.train_models import TrainModel
from myapp.train.models.equipment import TrainEquipment
from myapp.train.services.filter_service import apply_train_filters


async def export_train_cases(session, filters, sort_order="desc", search=""):
    """Выгружает все отфильтрованные поездные случаи в поездной шаблон"""
    numbered = (
        select(Case.id, func.row_number().over(order_by=Case.id).label("number"))
        .where(Case.direction == "train")
        .cte("export_train_numbers")
    )
    stmt = (
        select(Case, TrainCaseDetails, numbered.c.number)
        .join(TrainCaseDetails, TrainCaseDetails.case_id == Case.id)
        .join(numbered, numbered.c.id == Case.id)
    )
    stmt = apply_train_filters(stmt, filters)
    if search:
        stmt = stmt.where(numbered.c.number == int(search))
    rows = (
        (
            await session.execute(
                stmt.options(*load_detail_relations()).order_by(
                    Case.id.asc() if sort_order == "asc" else Case.id.desc()
                )
            )
        )
        .unique()
        .all()
    )
    if not rows:
        raise ValueError("Нет данных для экспорта")
    await PassportCaseService.attach_replacements(
        session, [case for case, _, _ in rows]
    )
    equipment = {e.id: e for e in (await session.scalars(select(TrainEquipment))).all()}
    models = {
        m.id: m.train_model_name
        for m in (await session.scalars(select(TrainModel))).all()
    }
    wagon_ids = {node for _, details, _ in rows for node in details.wagon_node_ids}
    wagons = dict(
        (
            await session.execute(
                select(ProductPassportNode.id, ProductPassportNode.tree_name).where(
                    ProductPassportNode.id.in_(wagon_ids)
                )
            )
        ).all()
    )

    def equipment_view(equipment_id):
        """Подготавливает поездное имя для общего построителя строк"""
        equipment_item = equipment.get(equipment_id)
        if not equipment_item:
            return None
        name = equipment_item.equipment_name.replace("_", " ")
        return SimpleNamespace(name=name, equipment_name=name, parent=None)

    cases = []
    for case, details, number in rows:
        values = dict(case.__dict__)
        values.update(
            display_number=number,
            locomotive_number=details.train_number,
            locomotive_model=SimpleNamespace(name=models[details.train_model_id]),
            component_equipment=equipment_view(
                details.component_id or details.equipment_id
            ),
            element_equipment=equipment_view(details.element_id),
            new_component_equipment=equipment_view(
                details.new_component_id or details.new_equipment_id
            ),
            new_element_equipment=equipment_view(details.new_element_id),
        )
        values["export_wagons"] = ", ".join(
            sorted(
                {
                    wagons[node].split("№")[-1].strip()
                    for node in details.wagon_node_ids
                    if node in wagons
                },
                key=lambda value: int(value) if value.isdigit() else 0,
            )
        )
        cases.append(SimpleNamespace(**values))
    template = (
        Path(__file__).resolve().parents[3] / "template_excel/template_train.xlsx"
    )
    stream = await asyncio.to_thread(
        ExportService.generate_cases_excel, cases, template
    )
    return stream, urllib.parse.quote(
        f"Выгрузка_поездов_{datetime.now():%d_%m_%Y}.xlsx"
    )
