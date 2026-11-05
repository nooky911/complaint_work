import json
import re
from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy import select, func, text

from myapp.utils.equipment_hierarchy import inherited_equipment_value
from myapp.train.services.passport_selection_service import passport_selection
from myapp.services.omega_services.passport_position_service import (
    PassportPositionService,
)
from myapp.models.auxiliaries import FaultDiscoveryPlace
from myapp.database.transactional import transactional
from myapp.database.query_builders.query_case_builders import load_detail_relations
from myapp.models.repair_case_equipment import RepairCaseEquipment as Case
from myapp.models.product_passports import ProductPassport, ProductPassportNode
from myapp.models.warranty_work import WarrantyWork
from myapp.models.user import User
from myapp.models.waybill_docs import WaybillDoc
from myapp.schemas.cases import CaseDetail
from myapp.train.models.case_details import TrainCaseDetails
from myapp.train.models.equipment import TrainEquipment, TrainEquipmentMalfunction
from myapp.services.reference_service import ReferenceService
from myapp.services.warranty_service import WarrantyService
from myapp.services.omega_services.passport_case_service import PassportCaseService
from myapp.services.user_access_service import UserAccessService
from myapp.constants.case_lock import is_case_lock_active
from myapp.loco.services.case_status_service import CaseStatusService


COMMON_EXCLUDE = {
    "user_id",
    "train",
    "warranty_work",
    "waybill_doc",
    "expected_revision",
    "passport_links",
    "replacement_items",
    "locomotive_model_id",
    "locomotive_number",
    "section_mask",
    "component_equipment_id",
    "element_equipment_id",
    "new_component_equipment_id",
    "new_element_equipment_id",
}


def wagon_nodes(nodes):
    """Находит вагоны по именам узлов без предположений об их количестве"""
    return sorted(
        [
            n
            for n in nodes
            if re.fullmatch(r"Вагон\s*(?:№\s*)?\d+", n.tree_name.strip(), re.I)
        ],
        key=lambda n: int(re.search(r"\d+", n.tree_name).group()),
    )


class TrainCaseService:
    """Общие записи случаев с поездной идентификацией и классификатором"""

    @staticmethod
    async def can_edit(session, user, owner_id):
        """Разрешает запись только своему направлению и владельцу либо напарнику"""
        return (
            user.role == "superadmin" or user.direction == "train"
        ) and await UserAccessService.can_edit_owner(session, user, owner_id)

    @staticmethod
    async def get(session, case_id, user):
        """Собирает поездную карточку из общих отношений и расширения"""
        case = await CaseStatusService.get_case_with_status(
            session, case_id, load_detail_relations, direction="train"
        )
        if not case:
            raise HTTPException(404, "Поездной случай не найден")
        extension = await session.get(TrainCaseDetails, case_id)
        if extension is None:
            raise HTTPException(409, "Отсутствуют поездные данные случая")
        names = dict(
            (
                await session.execute(
                    select(ProductPassportNode.id, ProductPassportNode.tree_name).where(
                        ProductPassportNode.id.in_(extension.wagon_node_ids)
                    )
                )
            ).all()
        )
        number = await session.scalar(
            select(func.count())
            .select_from(Case)
            .where(Case.direction == "train", Case.id <= case.id)
        )
        await PassportCaseService.case_details(session, case)
        return TrainCaseService.serialize(
            case,
            extension,
            await TrainCaseService.can_edit(session, user, case.user_id),
            names,
            number,
        )

    @staticmethod
    def serialize(case, extension, can_edit, wagon_names, number):
        """Представляет общую запись с поездными данными для списка и карточки"""
        result = CaseDetail.model_validate(case).model_dump(mode="json")
        result["direction"] = "train"
        result["status"] = getattr(case, "status", None) or "Ожидает отправки уведомления поставщику"
        result["display_number"] = number
        result["train"] = {
            c.name: getattr(extension, c.name)
            for c in TrainCaseDetails.__table__.columns
            if c.name != "case_id"
        }
        result["train"]["wagon_names"] = [
            wagon_names.get(i, str(i)) for i in extension.wagon_node_ids
        ]
        result["can_edit"] = can_edit
        return result

    @staticmethod
    async def validate(session, data, existing=None):
        """Проверяет паспорт, принадлежность вагонов, иерархию и неисправность"""
        data.validate_write()
        if data.repair_type_id == 8:
            raise HTTPException(422, "Тип ремонта Другое недоступен для поездов")
        await WarrantyService.validate_train_summaries(session, data.warranty_work)
        for field in (
            "locomotive_model_id",
            "locomotive_number",
            "section_mask",
            "component_equipment_id",
            "element_equipment_id",
            "new_component_equipment_id",
            "new_element_equipment_id",
        ):
            if getattr(data, field) is not None:
                raise HTTPException(
                    422, "Поездная форма не принимает локомотивные поля"
                )
        if (
            data.warranty_work.re_notification_number
            or data.warranty_work.re_notification_date
            or data.warranty_work.research_document
            or data.warranty_work.research_status_id
            or data.warranty_work.investigation_reason_id
        ):
            raise HTTPException(
                422,
                "Повторное уведомление и акт исследования для поездов не используются",
            )
        discovery = await session.get(FaultDiscoveryPlace, data.fault_discovered_at_id)
        if not discovery or not ReferenceService.discovery_allowed(
            discovery.name, "train"
        ):
            raise HTTPException(
                422, "Выберите поездной вариант выявления неисправности"
            )
        passport = await session.get(ProductPassport, data.passport_id)
        if not passport or passport.train_model_id != data.train.train_model_id:
            raise HTTPException(422, "Паспорт не соответствует модели поезда")
        _, node_map, states, _, owners, available_ids = await passport_selection(
            session,
            data.passport_id,
            data.train.wagon_node_ids,
            data.fault_date,
            existing[0].id if existing else None,
        )
        nodes = list(node_map.values())
        wagons = {n.id: n for n in wagon_nodes(nodes)}
        if not set(data.train.wagon_node_ids) <= wagons.keys():
            raise HTTPException(422, "Выбранный вагон отсутствует в паспорте")
        by_id = {n.id: n for n in nodes}
        by_code = {n.omega_code: n for n in nodes}
        for node_id in data.train.passport_node_ids:
            node = by_id.get(node_id)
            seen = set()
            while node and node.id not in wagons and node.id not in seen:
                seen.add(node.id)
                node = by_code.get(node.parent_omega_code)
            if not node or node.id not in data.train.wagon_node_ids:
                raise HTTPException(
                    422, "Оборудование паспорта не принадлежит выбранным вагонам"
                )
        equipment = {
            e.id: e for e in (await session.scalars(select(TrainEquipment))).all()
        }
        old = []
        for level, field in enumerate(
            ("equipment_id", "component_id", "element_id"), 2
        ):
            value = getattr(data.train, field)
            if value is None:
                if level == 3 and data.train.element_id:
                    raise HTTPException(422, "Выберите компонент перед элементом")
                continue
            item = equipment.get(value)
            if (
                not item
                or item.level != level
                or (old and item.parent_id != old[-1].id)
            ):
                raise HTTPException(422, "Нарушена иерархия поездного оборудования")
            old.append(item)
        leaf = old[-1]
        legacy = bool(
            existing
            and existing[0].passport_id == data.passport_id
            and existing[0].fault_date == data.fault_date
            and set(existing[1].wagon_node_ids) == set(data.train.wagon_node_ids)
            and set(existing[1].passport_node_ids) == set(data.train.passport_node_ids)
            and all(
                getattr(existing[1], field) == getattr(data.train, field)
                for field in ("equipment_id", "component_id", "element_id")
            )
        )
        if leaf.id not in available_ids and not legacy:
            raise HTTPException(422, "Оборудование отсутствует в выбранных вагонах")
        selected_ids = set(data.train.passport_node_ids)
        component_nodes = {
            node_id
            for node_id in owners
            if states[node_id].get("is_present", True)
            and states[node_id].get("equipment_id")
            == (data.train.component_id or data.train.equipment_id)
        }
        element_nodes = {
            node_id
            for node_id in owners
            if states[node_id].get("is_present", True)
            and data.train.element_id
            and states[node_id].get("equipment_id") == data.train.element_id
        }
        if selected_ids - component_nodes - element_nodes:
            raise HTTPException(
                422,
                "Экземпляр паспорта не соответствует выбранному компоненту или элементу",
            )
        selected_components = selected_ids & component_nodes
        selected_elements = selected_ids & element_nodes
        if not legacy and (
            (component_nodes and not selected_components)
            or (element_nodes and not selected_elements)
        ):
            raise HTTPException(
                422,
                "Выберите неисправные экземпляры согласно паспорту: сначала компонент, затем его элементы",
            )
        if (
            component_nodes
            and selected_elements
            and (selected_components or not legacy)
        ):
            for node_id in selected_elements:
                ancestors = PassportPositionService.ancestors(by_id[node_id], by_code)
                if not any(parent.id in selected_components for parent in ancestors):
                    raise HTTPException(
                        422, "Элемент паспорта не принадлежит выбранному компоненту"
                    )
        linked = await session.scalar(
            select(TrainEquipmentMalfunction.equipment_id).where(
                TrainEquipmentMalfunction.equipment_id == leaf.id,
                TrainEquipmentMalfunction.malfunction_id == data.malfunction_id,
            )
        )
        if not linked:
            raise HTTPException(
                422, "Неисправность не привязана к выбранному оборудованию"
            )
        # В существующем справочнике 1 — оборудование, 2 — компонент, 3 — элемент
        target = {1: 2, 2: 3, 3: 4}.get(data.repair_type_id)
        replacements = [
            getattr(data.train, f)
            for f in ("new_equipment_id", "new_component_id", "new_element_id")
        ]
        if target:
            replacement = equipment.get(replacements[target - 2])
            source = next((e for e in old if e.level == target), None)
            if (
                not source
                or not replacement
                or replacement.level != target
                or replacement.parent_id != source.parent_id
            ):
                raise HTTPException(
                    422, "Выберите установленную замену на соответствующем уровне"
                )
        elif any(replacements):
            raise HTTPException(422, "Выбранный тип ремонта не предполагает замену")
        if any(v is not None and i + 2 != target for i, v in enumerate(replacements)):
            raise HTTPException(422, "Замена указана на неверном уровне")

        installed = next(
            (equipment[v] for v in reversed(replacements) if v in equipment), None
        )
        return (
            passport,
            inherited_equipment_value(leaf.id, equipment, "supplier_id"),
            inherited_equipment_value(
                installed.id if installed else None, equipment, "supplier_id"
            ),
        )

    @staticmethod
    def duplicate_equipment_identity(data, train):
        """Сравнивает вагоны, экземпляры и ручные номера независимо от порядка выбора"""

        def numbers(value):
            """Сохраняет значимые символы номера и уравнивает пустое значение с б/н"""
            parts = (part.strip().casefold() for part in (value or "").split(","))
            return tuple(
                sorted({part for part in parts if part not in ("", "б/н", "—", "-")})
            )

        return (
            train.equipment_id,
            train.component_id,
            train.element_id,
            tuple(sorted(set(train.wagon_node_ids or []))),
            tuple(sorted(set(train.passport_node_ids or []))),
            numbers(data.component_serial_number_old),
            numbers(data.element_serial_number_old),
        )

    @staticmethod
    async def check_duplicate(session, data, case_id=None):
        """Не допускает повторный поездной случай, включая одновременное сохранение"""
        key = json.dumps(
            [
                "train-duplicate",
                str(data.fault_date),
                data.passport_id,
                data.mileage,
                data.malfunction_id,
            ],
            ensure_ascii=False,
        )
        await session.execute(
            text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"),
            {"key": key},
        )
        statement = (
            select(Case, TrainCaseDetails)
            .join(
                TrainCaseDetails,
                TrainCaseDetails.case_id == Case.id,
            )
            .where(
                Case.direction == "train",
                Case.passport_id == data.passport_id,
                Case.fault_date == data.fault_date,
                Case.malfunction_id == data.malfunction_id,
                Case.mileage.is_not_distinct_from(data.mileage),
            )
        )
        if case_id is not None:
            statement = statement.where(Case.id != case_id)
        identity = TrainCaseService.duplicate_equipment_identity(data, data.train)
        for existing, train in (await session.execute(statement)).all():
            if (
                TrainCaseService.duplicate_equipment_identity(existing, train)
                == identity
            ):
                raise HTTPException(409, "Такой поездной случай уже существует")

    @staticmethod
    @transactional
    async def save(session, data, user, case_id=None):
        """Атомарно сохраняет общую запись, поездные поля и документы с проверкой версии"""
        case = None
        if case_id:
            case = await session.scalar(
                select(Case)
                .where(Case.id == case_id, Case.direction == "train")
                .with_for_update()
            )
            if not case:
                raise HTTPException(404, "Случай не найден")
            if not await TrainCaseService.can_edit(session, user, case.user_id):
                raise HTTPException(403, "Недостаточно прав")
            if data.expected_revision != case.revision:
                raise HTTPException(
                    409, "Случай уже изменён. Откройте актуальную версию"
                )
            if is_case_lock_active(case) and case.locked_by_id != user.id:
                raise HTTPException(423, "Случай редактирует другой пользователь")
        elif not await TrainCaseService.can_edit(session, user, user.id):
            raise HTTPException(403, "Недостаточно прав")
        target_user_id = data.user_id or (case.user_id if case else user.id)
        if (
            target_user_id != (case.user_id if case else user.id)
            and user.role != "superadmin"
        ):
            raise HTTPException(403, "Только администратор может менять ответственного")
        if case is None or target_user_id != case.user_id:
            try:
                await UserAccessService.validate_case_owner(
                    session, target_user_id, "train"
                )
            except ValueError as error:
                raise HTTPException(422, str(error)) from error
        target_user = await session.get(User, target_user_id)
        if not target_user or not target_user.is_active:
            raise HTTPException(422, "Выберите действующего пользователя")
        await session.execute(
            select(ProductPassport.id)
            .where(ProductPassport.id == data.passport_id)
            .with_for_update()
        )
        previous = await session.get(TrainCaseDetails, case.id) if case else None
        passport, supplier, new_supplier = await TrainCaseService.validate(
            session, data, (case, previous) if case and previous else None
        )
        await TrainCaseService.check_duplicate(session, data, case_id)
        values = data.model_dump(exclude=COMMON_EXCLUDE)
        for quantity, selected in (
            ("element_quantity", data.train.element_id),
            (
                "new_component_quantity",
                data.train.new_equipment_id or data.train.new_component_id,
            ),
            ("new_element_quantity", data.train.new_element_id),
        ):
            if not selected:
                values[quantity] = None
        if case is None:
            case = Case(
                direction="train",
                user_id=target_user_id,
                created_by_id=user.id,
                created_by_name=user.full_name,
                creator_source="created",
                date_recorded=datetime.now(timezone.utc),
                revision=1,
                warranty_work=WarrantyWork(),
                waybill_doc=WaybillDoc(),
                **values
            )
            session.add(case)
            await session.flush()
            extension = TrainCaseDetails(case_id=case.id)
            session.add(extension)
        else:
            for k, v in values.items():
                setattr(case, k, v)
            extension = await session.get(TrainCaseDetails, case.id)
        case.user_id = target_user_id
        case.supplier_id = supplier
        case.new_supplier_id = new_supplier
        for k, v in data.train.model_dump().items():
            setattr(extension, k, v)
        extension.train_number = passport.product_number
        warranty = await session.scalar(
            select(WarrantyWork).where(WarrantyWork.case_id == case.id)
        )
        waybill = await session.scalar(
            select(WaybillDoc).where(WaybillDoc.case_id == case.id)
        )
        for obj, source in (
            (warranty, data.warranty_work),
            (waybill, data.waybill_doc),
        ):
            for k, v in source.model_dump().items():
                setattr(obj, k, v)
        await PassportCaseService.sync_case(
            session,
            case,
            user,
            links=(
                [link.model_dump() for link in data.passport_links]
                if data.passport_links is not None
                else None
            ),
            installed=(
                [item.model_dump() for item in data.replacement_items]
                if data.replacement_items is not None
                else None
            ),
            expected_revision=data.expected_revision if case_id else None,
            train_details=extension,
        )
        if case_id:
            case.revision += 1
        case.locked_by_id = None
        case.locked_at = None
        await session.flush()
        return await TrainCaseService.get(session, case.id, user)
