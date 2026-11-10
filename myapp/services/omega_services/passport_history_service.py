from collections import defaultdict
from datetime import date, datetime, timezone
from typing import Any
from sqlalchemy import func, or_, select
from sqlalchemy.exc import DBAPIError

from myapp.constants.case_lock import is_case_lock_active
from myapp.loco.services.equipment_service import EquipmentService
from myapp.services.omega_services.passport_file_service import PassportFileService
from myapp.models.repair_case_equipment import RepairCaseEquipment
from myapp.database.transactional import transactional
from myapp.models.product_passports import (
    CasePassportLink,
    ProductPassport,
    ProductPassportEvent,
    ProductPassportEventItem,
    ProductPassportNode,
)
from myapp.loco.services.case_filter_service import CaseFilterService
from myapp.services.omega_services.passport_position_service import (
    PassportPositionService,
)


class PassportHistoryService:
    """История замен и ручных исправлений паспорта"""

    @classmethod
    async def close_event(cls, session, event, actor, status, reason):
        """Отменяет запись замены и возвращает затронутые позиции"""
        event.status = status
        event.closed_at = datetime.now(timezone.utc)
        event.closed_by_id = actor.id
        event.closed_by_name = actor.full_name or actor.login
        event.close_reason = reason
        return set(
            (
                await session.scalars(
                    select(ProductPassportEventItem.node_id).where(
                        ProductPassportEventItem.event_id == event.id
                    )
                )
            ).all()
        )

    @classmethod
    async def recalculate(cls, session, node_ids):
        """Обновляет позиции паспорта по действующим записям истории"""
        if not node_ids:
            return
        nodes = (
            await session.scalars(
                select(ProductPassportNode)
                .where(ProductPassportNode.id.in_(node_ids))
                .order_by(ProductPassportNode.id)
                .with_for_update()
            )
        ).all()
        changes = defaultdict(list)
        stmt = (
            select(ProductPassportEventItem)
            .join(ProductPassportEvent)
            .where(
                ProductPassportEventItem.node_id.in_(node_ids),
                ProductPassportEvent.status == "active",
            )
            .order_by(
                ProductPassportEvent.effective_date,
                ProductPassportEvent.day_order,
                ProductPassportEvent.id,
            )
        )
        await session.flush()
        for item in (await session.scalars(stmt)).all():
            changes[item.node_id].append(item)
        train_ids = set(
            (
                await session.scalars(
                    select(ProductPassport.id).where(
                        ProductPassport.train_model_id.is_not(None),
                        ProductPassport.id.in_({n.passport_id for n in nodes}),
                    )
                )
            ).all()
        )
        for n in nodes:
            state = PassportPositionService.compose(n.baseline_state, changes[n.id])
            for field in PassportPositionService.INSTANCE_FIELDS + ("is_present",):
                if field == "equipment_name":
                    continue
                value = state.get(field)
                if field in ("manufacture_date", "install_date") and value:
                    value = date.fromisoformat(value)
                setattr(
                    n,
                    (
                        "train_equipment_id"
                        if field == "equipment_id" and n.passport_id in train_ids
                        else field
                    ),
                    value,
                )
            n.version += 1
        await session.flush()

    @classmethod
    async def history(cls, session, passport_id, node_id, include_inactive=False):
        """Возвращает историю выбранной позиции паспорта"""
        node = await session.get(ProductPassportNode, node_id)
        if not node or node.passport_id != passport_id:
            PassportPositionService.fail("Позиция не найдена")
        passport = await session.get(ProductPassport, passport_id)
        numbered = (
            select(
                RepairCaseEquipment.id,
                func.row_number()
                .over(order_by=RepairCaseEquipment.id)
                .label("display_number"),
            )
            .where(RepairCaseEquipment.direction == "train")
            .cte("train_history_numbers")
            if passport.train_model_id is not None
            else CaseFilterService._numbered_cases()
        )
        stmt = (
            select(
                ProductPassportEvent,
                ProductPassportEventItem,
                numbered.c.display_number,
            )
            .join(ProductPassportEventItem)
            .outerjoin(numbered, numbered.c.id == ProductPassportEvent.case_id)
            .where(
                ProductPassportEvent.passport_id == passport_id,
                ProductPassportEventItem.node_id == node_id,
            )
            .order_by(
                ProductPassportEvent.effective_date.desc(),
                ProductPassportEvent.day_order.desc(),
                ProductPassportEvent.id.desc(),
            )
        )
        if not include_inactive:
            stmt = stmt.where(ProductPassportEvent.status == "active")
        result = []
        for event, item, number in (await session.execute(stmt)).all():
            result.append(
                dict(
                    id=event.id,
                    kind=event.kind,
                    status=event.status,
                    date=(
                        None
                        if event.kind == "historical_replacement"
                        else event.effective_date
                    ),
                    recorded_at=event.recorded_at,
                    case_id=event.case_id,
                    source_case_id=event.source_case_id,
                    display_number=number,
                    case_snapshot=event.case_snapshot,
                    actor_name=event.actor_name,
                    reason=event.reason,
                    before=item.before_state,
                    after=item.after_state,
                    changed_fields=item.changed_fields,
                    revision=event.revision,
                    close_reason=event.close_reason,
                )
            )
        return result

    @classmethod
    async def _sync_case_types(
        cls, session, passport_id, node_id, old, new, *, train_equipment=None
    ):
        """Исправляет тип в случаях, связанных с тем же экземпляром паспорта"""
        link_model = CasePassportLink
        case_model = RepairCaseEquipment
        old_id = old["equipment_id"]
        new_id = new["equipment_id"]
        candidates = select(link_model.case_id).where(
            link_model.node_id == node_id,
            link_model.selected_state["equipment_id"].as_integer() == old_id,
        )
        statement = (
            select(case_model, link_model)
            .join(link_model, link_model.case_id == case_model.id)
            .where(
                case_model.passport_id == passport_id,
                case_model.direction
                == ("train" if train_equipment is not None else "loco"),
                case_model.id.in_(candidates),
            )
            .order_by(case_model.id, link_model.id)
            .with_for_update(of=case_model, nowait=True)
        )
        # Редактирование случая блокирует его раньше паспорта
        try:
            rows = (await session.execute(statement)).all()
        except DBAPIError as exc:
            if getattr(exc.orig, "sqlstate", None) == "55P03":
                PassportPositionService.fail(
                    "Связанный случай сейчас сохраняется. Повторите исправление.",
                    "revision",
                )
            raise
        if not rows:
            return

        # В старых снимках замены без случая не имеют ключа установки
        historical_cutoff = await session.scalar(
            select(func.max(ProductPassportEvent.effective_date))
            .join(ProductPassportEventItem)
            .where(
                ProductPassportEvent.passport_id == passport_id,
                ProductPassportEventItem.node_id == node_id,
                ProductPassportEvent.kind == "historical_replacement",
                ProductPassportEvent.status == "active",
            )
        )
        by_case = defaultdict(list)
        for case, link in rows:
            by_case[case].append(link)

        for case, links in by_case.items():
            if historical_cutoff and case.fault_date <= historical_cutoff:
                continue
            changed = False
            for link in links:
                if (
                    link.node_id != node_id
                    or link.selected_state.get("equipment_id") != old_id
                    or not PassportPositionService.same_instance(
                        link.selected_state, old
                    )
                ):
                    continue
                # Общий тип случая должен подходить ко всем экземплярам этой роли
                if any(
                    other.id != link.id
                    and other.role == link.role
                    and other.selected_state.get("equipment_id") != new_id
                    for other in links
                ):
                    continue
                if train_equipment is None:
                    field = f"{link.role}_equipment_id"
                    if getattr(case, field) != old_id:
                        continue
                    setattr(case, field, new_id)
                else:
                    from myapp.train.services.case_service import TrainCaseService

                    if not await TrainCaseService.apply_passport_type_correction(
                        session, case, link.role, old_id, new_id, train_equipment
                    ):
                        continue
                link.selected_state = PassportPositionService.with_corrected_type(
                    link.selected_state, new
                )
                changed = True
            if changed and train_equipment is None:
                case.supplier_id = await EquipmentService.resolve_supplier(
                    session,
                    equipment_id=(
                        case.element_equipment_id or case.component_equipment_id
                    ),
                    locomotive_number=case.locomotive_number,
                    locomotive_model_id=case.locomotive_model_id,
                )
            if changed:
                case.revision += 1

    @classmethod
    async def _retry_case_type_correction(
        cls, session, passport_id, node_id, current, *, train_equipment=None
    ):
        """Доводит ранее сохранённое исправление до случаев при повторном сохранении"""
        statement = (
            select(ProductPassportEventItem, ProductPassportEvent.kind)
            .join(ProductPassportEvent)
            .where(
                ProductPassportEvent.passport_id == passport_id,
                ProductPassportEventItem.node_id == node_id,
                ProductPassportEvent.status == "active",
            )
            .order_by(
                ProductPassportEvent.effective_date.desc(),
                ProductPassportEvent.day_order.desc(),
                ProductPassportEvent.id.desc(),
            )
            .limit(1)
        )
        row = (await session.execute(statement)).first()
        if row is None or row[1] != "manual_correction":
            return
        item = row[0]
        if (
            PassportPositionService.is_type_only_change(item.changed_fields)
            and item.after_state.get("equipment_id") == current.get("equipment_id")
            and PassportPositionService.same_instance(item.after_state, current)
        ):
            await cls._sync_case_types(
                session,
                passport_id,
                node_id,
                {**current, "equipment_id": item.before_state["equipment_id"]},
                current,
                train_equipment=train_equipment,
            )

    @staticmethod
    async def correction_date(session, passport_id, node_id, fault_date, case_id):
        """Проверяет, что исправление из случая относится к текущему экземпляру"""
        today = datetime.now().date()
        if fault_date is None and case_id is None:
            return today
        effective = fault_date or today
        if effective > today:
            PassportPositionService.fail("Дата случая не может быть позже сегодняшней")
        later = ProductPassportEvent.effective_date > effective
        if case_id is not None:
            later = or_(
                later,
                (ProductPassportEvent.case_id == case_id)
                & (ProductPassportEvent.kind == "case_replacement"),
            )
        event = await session.scalar(
            select(ProductPassportEvent.id)
            .join(ProductPassportEventItem)
            .where(
                ProductPassportEvent.passport_id == passport_id,
                ProductPassportEventItem.node_id == node_id,
                ProductPassportEvent.status == "active",
                later,
            )
            .limit(1)
        )
        if event is not None:
            PassportPositionService.fail(
                "У позиции есть более позднее изменение или замена по этому случаю. "
                "Проверьте её историю в паспорте."
            )
        return effective

    @classmethod
    @transactional
    async def correct(cls, session, passport_id, node_id, data, actor):
        """Сохраняет ручное исправление позиции с причиной и автором"""
        await session.execute(
            select(ProductPassport.id)
            .where(ProductPassport.id == passport_id)
            .with_for_update()
        )
        passport, nodes, states, equipment, by_code = (
            await PassportPositionService.load(session, passport_id)
        )
        if node_id not in nodes:
            PassportPositionService.fail("Позиция не найдена")
        node = nodes[node_id]
        await session.execute(
            select(ProductPassportNode.id)
            .where(ProductPassportNode.id == node_id)
            .with_for_update()
        )
        if data["expected_version"] != node.version:
            PassportPositionService.fail(
                "Позиция изменена. Обновите паспорт.", "revision"
            )
        if not data.get("reason", "").strip():
            PassportPositionService.fail("Укажите причину исправления")
        effective = await cls.correction_date(
            session,
            passport_id,
            node_id,
            data.get("case_fault_date"),
            data.get("case_id"),
        )
        case = None
        if data.get("case_id") is not None:
            try:
                case = await session.get(
                    RepairCaseEquipment,
                    data["case_id"],
                    with_for_update={"nowait": True},
                    populate_existing=True,
                )
            except DBAPIError as exc:
                if getattr(exc.orig, "sqlstate", None) == "55P03":
                    PassportPositionService.fail(
                        "Случай сейчас сохраняется", "revision"
                    )
                raise
            if (
                case is None
                or case.direction
                != ("train" if passport.train_model_id is not None else "loco")
                or case.locked_by_id != actor.id
                or not is_case_lock_active(case)
                or case.revision != data.get("expected_case_revision")
            ):
                PassportPositionService.fail(
                    "Редакция случая изменилась. Откройте актуальную карточку.",
                    "revision",
                )
        old = states[node_id]
        new: dict[str, Any] = dict(old)
        changed = []
        for field in ("serial_number", "manufacture_date_text", "equipment_id"):
            if field not in data:
                continue
            value = PassportPositionService.clean(data[field])
            if (
                field == "manufacture_date_text"
                and value
                and any(c.isalpha() for c in value)
            ):
                PassportPositionService.fail(
                    "Дата изготовления не должна содержать буквы"
                )
            if old.get(field) == value:
                continue
            if field == "equipment_id":
                if value not in {
                    x["id"]
                    for x in PassportPositionService.allowed_types(
                        old.get("equipment_id"), equipment
                    )
                }:
                    PassportPositionService.fail(
                        "Новый тип относится к другому семейству"
                    )
                if len(PassportPositionService.descendants(node, nodes, by_code)) > 1:
                    PassportPositionService.fail(
                        "Перед сменой типа с детьми требуется согласовать их состав"
                    )
                new["equipment_name"] = equipment[value]["name"]
                new["supplier_id"] = equipment[value]["supplier_id"]
                ctx = PassportPositionService.context(node, by_code)
                new["tree_name"] = PassportPositionService.equipment_tree_name(
                    old, equipment[value]["name"], ctx
                )
                new["designation"] = None
                new["full_name"] = None
                changed.extend(
                    type_field
                    for type_field in PassportPositionService.TYPE_FIELDS
                    if type_field != field
                )
            if field == "manufacture_date_text":
                new["manufacture_date"] = None
                for fmt in ("%d.%m.%Y", "%Y-%m-%d"):
                    try:
                        new["manufacture_date"] = (
                            datetime.strptime(value or "", fmt).date().isoformat()
                        )
                        break
                    except ValueError:
                        pass
                changed.append("manufacture_date")
            new[field] = value
            changed.append(field)
        train_equipment = equipment if passport.train_model_id is not None else None
        result = {
            "position": {
                "equipment_id": new.get("equipment_id"),
                "equipment_name": new.get("equipment_name"),
                "serial_number": new.get("serial_number"),
                "manufacture_date_text": new.get("manufacture_date_text"),
                "version": node.version + int(bool(changed)),
            }
        }
        if not changed:
            if data.get("equipment_id") is not None:
                await cls._retry_case_type_correction(
                    session, passport_id, node_id, old, train_equipment=train_equipment
                )
            return {
                **result,
                "case_revision": case.revision if case is not None else None,
            }
        if PassportPositionService.is_type_only_change(changed):
            await cls._sync_case_types(
                session, passport_id, node_id, old, new, train_equipment=train_equipment
            )
        preserve_files = data.get("preserve_existing_files")
        compatible = PassportFileService.can_preserve_files(old, new)
        if preserve_files is True and not compatible:
            PassportPositionService.fail(
                "Номер или дата изменены: нельзя перенести сканы прежнего экземпляра"
            )
        if node.baseline_state is None:
            node.baseline_state = PassportPositionService.snapshot(node, equipment)
            node.baseline_source = "reviewed_import"
        order = (
            await session.scalar(
                select(func.max(ProductPassportEvent.day_order)).where(
                    ProductPassportEvent.passport_id == passport_id,
                    ProductPassportEvent.effective_date == effective,
                )
            )
            or 0
        ) + 1
        event = ProductPassportEvent(
            passport_id=passport_id,
            kind="manual_correction",
            effective_date=effective,
            day_order=order,
            actor_id=actor.id,
            actor_name=actor.full_name or actor.login,
            reason=data["reason"].strip(),
            revision=1,
            status="active",
        )
        session.add(event)
        await session.flush()
        if preserve_files is False or not compatible:
            new["passport_files_instance_key"] = f"event:{event.id}"
        session.add(
            ProductPassportEventItem(
                event_id=event.id,
                node_id=node_id,
                scope="component",
                position_context=PassportPositionService.context(node, by_code),
                before_state=old,
                after_state=new,
                changed_fields=changed,
            )
        )
        await cls.recalculate(session, {node_id})
        return {**result, "case_revision": case.revision if case is not None else None}
