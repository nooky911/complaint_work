from datetime import date
from sqlalchemy import select, func, cast, exists
from sqlalchemy.dialects.postgresql import JSONB

from myapp.database.query_builders.filter_conditions import apply_filter_conditions
from myapp.models.repair_case_equipment import RepairCaseEquipment as Case
from myapp.models.warranty_work import WarrantyWork
from myapp.models.waybill_docs import WaybillDoc
from myapp.models.product_passports import ProductPassportNode
from myapp.models.user import User
from myapp.train.models.case_details import TrainCaseDetails
from myapp.train.models.equipment import TrainEquipment
from myapp.train.models.train_models import TrainModel
from myapp.services.reference_service import ReferenceService
from myapp.loco.services.case_status_service import CaseStatusService

# Фильтры поездных случаев
TRAIN_FILTER_COLUMNS = {
    **{
        column.key: column
        for column in Case.__table__.columns
        if column.key
        in {
            "regional_center_id",
            "malfunction_id",
            "repair_type_id",
            "supplier_id",
            "user_id",
            "equipment_owner_id",
            "performed_by_id",
            "destination_id",
            "component_serial_number_old",
            "element_serial_number_old",
            "component_serial_number_new",
            "element_serial_number_new",
        }
    },
    **{
        column.key: column
        for column in WarrantyWork.__table__.columns
        if column.key
        not in {
            "id",
            "case_id",
            "re_notification_number",
            "re_notification_date",
            "research_document",
            "research_status_id",
            "investigation_reason_id",
        }
    },
    **{
        column.key: column
        for column in WaybillDoc.__table__.columns
        if column.key not in {"id", "case_id"}
    },
    "locomotive_model_id": TrainCaseDetails.train_model_id,
    "locomotive_number": TrainCaseDetails.train_number,
    "component_equipment_id": TrainCaseDetails.component_id,
    "element_equipment_id": TrainCaseDetails.element_id,
    "new_component_equipment_id": TrainCaseDetails.new_component_id,
    "new_element_equipment_id": TrainCaseDetails.new_element_id,
}


def apply_train_filters(stmt, filters):
    """Применяет поездные фильтры до подсчёта и пагинации"""
    stmt = stmt.outerjoin(WarrantyWork, WarrantyWork.case_id == Case.id).outerjoin(
        WaybillDoc, WaybillDoc.case_id == Case.id
    )
    if filters.get("status"):
        stmt = stmt.where(CaseStatusService.build_status_subquery("train").in_(filters["status"]))
    conditions = []
    empty_fields = []
    fields = []
    for key, column in TRAIN_FILTER_COLUMNS.items():
        values = filters.get(key)
        if not isinstance(values, list) or not values:
            continue
        if "__empty__" in values:
            empty_fields.append(column.key)
        converter = column.type.python_type
        clean = [
            date.fromisoformat(value) if converter is date else converter(value)
            for value in values
            if value != "__empty__"
        ]
        fields.append((clean, column))
    apply_filter_conditions(conditions, fields, empty_fields)
    if conditions:
        stmt = stmt.where(*conditions)
    for key, operator in (
        ("date_from", Case.fault_date.__ge__),
        ("date_to", Case.fault_date.__le__),
    ):
        if filters.get(key):
            stmt = stmt.where(operator(date.fromisoformat(filters[key])))
    wagons = filters.get("wagon_number", [])
    if wagons:
        stmt = stmt.where(
            exists(
                select(ProductPassportNode.id).where(
                    ProductPassportNode.tree_name.in_(
                        [f"Вагон №{int(n)}" for n in wagons]
                    ),
                    cast(TrainCaseDetails.wagon_node_ids, JSONB).contains(
                        func.jsonb_build_array(ProductPassportNode.id)
                    ),
                )
            )
        )
    return stmt


async def train_filter_options(session, filters=None):
    """Возвращает варианты фильтров исключительно из поездных случаев"""
    result = dict(await ReferenceService.get_case_form_references())
    aliases = {
        "locomotive_model_id": "locomotive_models",
        "locomotive_number": "locomotive_numbers",
        "component_equipment_id": "components",
        "element_equipment_id": "elements",
        "new_component_equipment_id": "new_components",
        "new_element_equipment_id": "new_elements",
        "ttn_replacement_date": "ttn_replacement_dates",
        "ttn_from_rc_date": "ttn_from_rc_dates",
        "ttn_to_supplier_date": "ttn_to_supplier_dates",
        "ttn_from_supplier_date": "ttn_from_supplier_dates",
        "component_serial_number_old": "component_serial_numbers",
        "element_serial_number_old": "element_serial_numbers",
        "component_serial_number_new": "component_serial_numbers_new",
        "element_serial_number_new": "element_serial_numbers_new",
    }
    reference_options = {
        key: list(value) for key, value in result.items() if isinstance(value, list)
    }
    reference_keys = {
        "regional_center_id": "regional_centers",
        "malfunction_id": "malfunctions",
        "repair_type_id": "repair_types",
        "supplier_id": "suppliers",
        "equipment_owner_id": "equipment_owners",
        "performed_by_id": "performed_by",
        "destination_id": "destinations",
        "notification_summary_id": "notification_summaries",
        "response_summary_id": "response_summaries",
        "decision_summary_id": "decision_summaries",
        "to_supplier_provider_id": "shipping_providers",
        "from_supplier_provider_id": "from_shipping_providers",
    }
    base = (
        select(Case.id)
        .select_from(Case)
        .join(TrainCaseDetails, TrainCaseDetails.case_id == Case.id)
        .where(Case.direction == "train")
    )
    equipment = {
        e.id: e.equipment_name.replace("_", " ")
        for e in (await session.scalars(select(TrainEquipment))).all()
    }
    models = {
        m.id: m.train_model_name
        for m in (await session.scalars(select(TrainModel))).all()
    }
    columns = list(TRAIN_FILTER_COLUMNS.items())
    option_stmt = base.with_only_columns(*(column for _, column in columns))
    rows = (
        await session.execute(apply_train_filters(option_stmt, filters or {}))
    ).all()
    for index, (key, column) in enumerate(columns):
        if key.endswith("_id") and key not in aliases and key not in reference_keys:
            continue
        values = {row[index] for row in rows}
        values = sorted(
            (v for v in values if v is not None and str(v).strip()), key=str
        )
        option_key = reference_keys.get(
            key,
            aliases.get(key, key + "s" if key.endswith(("_number", "_date")) else key),
        )
        if key in reference_keys:
            source_key = (
                "shipping_providers"
                if key == "from_supplier_provider_id"
                else option_key
            )
            used_ids = set(values)
            result[option_key] = [
                option
                for option in reference_options.get(source_key, [])
                if option["id"] in used_ids
            ]
            continue
        if key.endswith("_date"):
            result[option_key] = [str(v) for v in values]
        else:
            names = (
                models
                if key == "locomotive_model_id"
                else equipment if "equipment_id" in key else {}
            )
            result[option_key] = [dict(id=v, name=names.get(v, str(v))) for v in values]
    filtered_case_ids = apply_train_filters(base, filters or {}).subquery()
    result["users"] = [
        dict(id=user_id, name=full_name or login)
        for user_id, full_name, login in (
            await session.execute(
                select(User.id, User.full_name, User.login)
                .join(Case, Case.user_id == User.id)
                .where(Case.id.in_(select(filtered_case_ids.c.id)))
                .distinct()
                .order_by(User.full_name, User.id)
            )
        ).all()
    ]
    wagon_names = (
        await session.scalars(
            select(ProductPassportNode.tree_name)
            .where(
                exists(
                    select(Case.id)
                    .join(TrainCaseDetails, TrainCaseDetails.case_id == Case.id)
                    .where(
                        Case.id.in_(select(filtered_case_ids.c.id)),
                        cast(TrainCaseDetails.wagon_node_ids, JSONB).contains(
                            func.jsonb_build_array(ProductPassportNode.id)
                        ),
                    )
                )
            )
            .distinct()
        )
    ).all()
    wagon_numbers = sorted(
        {
            int(name.split("№")[-1].strip())
            for name in wagon_names
            if name and "№" in name and name.split("№")[-1].strip().isdigit()
        }
    )
    result["wagons"] = [dict(id=i, name=str(i)) for i in wagon_numbers]
    result["statuses"] = list((await session.scalars(
        apply_train_filters(select(CaseStatusService.build_status_subquery("train"))
            .select_from(Case).join(TrainCaseDetails, TrainCaseDetails.case_id == Case.id)
            .where(Case.direction == "train"), filters or {}).distinct()
    )).all())
    return result
