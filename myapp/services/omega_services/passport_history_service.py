from collections import defaultdict
from datetime import date, datetime, timezone
from typing import Any
from sqlalchemy import func, select

from myapp.database.transactional import transactional
from myapp.models.product_passports import (
    ProductPassport,
    ProductPassportEvent,
    ProductPassportEventItem,
    ProductPassportNode,
)
from myapp.services.case_filter_service import CaseFilterService
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
        for n in nodes:
            state = PassportPositionService.compose(n.baseline_state, changes[n.id])
            for field in PassportPositionService.INSTANCE_FIELDS + ("is_present",):
                if field == "equipment_name":
                    continue
                value = state.get(field)
                if field in ("manufacture_date", "install_date") and value:
                    value = date.fromisoformat(value)
                setattr(n, field, value)
            n.version += 1
        await session.flush()

    @classmethod
    async def history(cls, session, passport_id, node_id, include_inactive=False):
        """Возвращает историю выбранной позиции паспорта"""
        node = await session.get(ProductPassportNode, node_id)
        if not node or node.passport_id != passport_id:
            PassportPositionService.fail("Позиция не найдена")
        numbered = CaseFilterService._numbered_cases()
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
                    date=(None if event.kind == "historical_replacement" else event.effective_date),
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
    @transactional
    async def correct(cls, session, passport_id, node_id, data, actor):
        """Сохраняет ручное исправление позиции с причиной и автором"""
        await session.execute(
            select(ProductPassport.id)
            .where(ProductPassport.id == passport_id)
            .with_for_update()
        )
        _, nodes, states, equipment, by_code = await PassportPositionService.load(
            session, passport_id
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
                new["tree_name"] = (
                    ctx.get("position") + " " if ctx.get("position") else ""
                ) + equipment[value]["name"].replace("_", " ")
                new["designation"] = None
                new["full_name"] = None
                changed += [
                    "equipment_name",
                    "supplier_id",
                    "tree_name",
                    "designation",
                    "full_name",
                ]
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
        if not changed:
            return
        if node.baseline_state is None:
            node.baseline_state = PassportPositionService.snapshot(node, equipment)
            node.baseline_source = "reviewed_import"
        # Ручное исправление действует с сегодняшнего дня после уже записанных замен
        today = datetime.now().date()
        order = (
            await session.scalar(
                select(func.max(ProductPassportEvent.day_order)).where(
                    ProductPassportEvent.passport_id == passport_id,
                    ProductPassportEvent.effective_date == today,
                )
            )
            or 0
        ) + 1
        event = ProductPassportEvent(
            passport_id=passport_id,
            kind="manual_correction",
            effective_date=today,
            day_order=order,
            actor_id=actor.id,
            actor_name=actor.full_name or actor.login,
            reason=data["reason"].strip(),
            revision=1,
            status="active",
        )
        session.add(event)
        await session.flush()
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
