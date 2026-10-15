import hashlib
import json
from collections import defaultdict
from sqlalchemy import delete, func, select

from myapp.models.equipment_malfunctions import Malfunction
from myapp.models.product_passports import (
    CasePassportLink,
    ProductPassport,
    ProductPassportEvent,
    ProductPassportEventItem,
    ProductPassportNode,
)
from myapp.services.case_filter_service import CaseFilterService
from myapp.services.equipment_service import EquipmentService
from myapp.services.omega_services.passport_history_service import (
    PassportHistoryService,
)
from myapp.services.omega_services.passport_position_service import (
    PassportPositionService,
)


class PassportCaseService:
    """Связь случая с выбранными позициями паспорта"""

    @staticmethod
    def selection_key(links, states):
        """Считает ключ выбранных экземпляров для проверки дубликатов"""
        if not links:
            return None
        canonical = []
        for link in links:
            row = (link["role"], link["node_id"], link.get("parent_node_id"))
            installation = states[link["node_id"]].get("_installation_case_id")
            # Сохраняем прежний ключ для заводского оборудования в уже перенесённых случаях
            if installation is not None:
                row += (installation,)
            canonical.append(row)
        return hashlib.sha256(json.dumps(sorted(canonical)).encode()).hexdigest()

    @classmethod
    async def sync_case(
        cls,
        session,
        case,
        actor,
        links=None,
        installed=None,
        expected_revision=None,
        force=False,
    ):
        """Сохраняет выбранные экземпляры и изменения паспорта по случаю"""
        existing = (
            await session.scalars(
                select(CasePassportLink).where(CasePassportLink.case_id == case.id)
            )
        ).all()
        previous = await session.scalar(
            select(ProductPassportEvent).where(
                ProductPassportEvent.case_id == case.id,
                ProductPassportEvent.status == "active",
            )
        )
        if expected_revision is not None and expected_revision != case.revision:
            PassportPositionService.fail(
                "Случай изменён другим пользователем. Обновите карточку.", "revision"
            )
        selection_from_record = links is None
        if links is None:
            if not force:
                return
            links = [
                dict(
                    node_id=x.node_id,
                    role=x.role,
                    version=None,
                    parent_node_id=next(
                        (v.node_id for v in existing if v.id == x.parent_link_id), None
                    ),
                )
                for x in existing
            ]
        if not case.passport_id:
            if links:
                PassportPositionService.fail("Для выбора экземпляров нужен паспорт")
            return
        await session.execute(
            select(ProductPassport.id)
            .where(ProductPassport.id == case.passport_id)
            .with_for_update()
        )
        _, nodes, states, equipment, by_code = await PassportPositionService.load(
            session, case.passport_id, case.fault_date, case.id
        )
        same_selection = {(x.node_id, x.role) for x in existing} == {
            (x["node_id"], x["role"]) for x in links
        }
        if same_selection and (
            (previous and previous.effective_date == case.fault_date)
            or (previous is None and selection_from_record)
        ):
            # Сохраняем снятые номера этого случая, даже если предыдущую замену удалили
            for old_link in existing:
                states[old_link.node_id] = old_link.selected_state
            old_items = (
                (
                    await session.scalars(
                        select(ProductPassportEventItem).where(
                            ProductPassportEventItem.event_id == previous.id
                        )
                    )
                ).all()
                if previous
                else []
            )
            for old_item in old_items:
                states[old_item.node_id] = old_item.before_state
        PassportPositionService.validate_links(
            nodes,
            states,
            by_code,
            links,
            case.component_equipment_id,
            case.element_equipment_id,
            case.section_mask,
        )
        for link in links:
            if (
                link.get("version") is not None
                and link["version"] != nodes[link["node_id"]].version
            ):
                PassportPositionService.fail(
                    "Состав паспорта изменился. Обновите выбор оборудования.",
                    "revision",
                )
        plan = PassportPositionService.plan(
            nodes, states, equipment, by_code, links, case.repair_type_id
        )
        if installed is None:
            if plan:
                old_items = (
                    (
                        await session.scalars(
                            select(ProductPassportEventItem).where(
                                ProductPassportEventItem.event_id == previous.id
                            )
                        )
                    ).all()
                    if previous
                    else []
                )
                installed = [{"node_id": i.node_id, **i.after_state} for i in old_items]
            else:
                installed = []
        supplied = {x["node_id"]: x for x in installed}
        if len(supplied) != len(installed) or set(supplied) != set(
            x["node_id"] for x in plan
        ):
            PassportPositionService.fail(
                "Установленный состав не соответствует рассчитанной замене. Обновите строки замены."
            )
        old_node_ids = {x.node_id for x in existing}
        if old_node_ids and not old_node_ids <= set(nodes):
            PassportPositionService.fail(
                "Для изменения локомотива сначала необходимо согласовать прежние паспортные связи"
            )
        # Блокируем выбранные позиции и проверяем, что их состав не изменился
        ids = sorted(
            {x["node_id"] for x in links} | {x["node_id"] for x in plan} | old_node_ids
        )
        locked = (
            (
                await session.scalars(
                    select(ProductPassportNode)
                    .where(ProductPassportNode.id.in_(ids))
                    .order_by(ProductPassportNode.id)
                    .with_for_update()
                )
            ).all()
            if ids
            else []
        )
        for n in locked:
            if n.baseline_state is None:
                n.baseline_state = PassportPositionService.snapshot(n, equipment)
                n.baseline_source = "reviewed_import"
        for value in installed:
            n = nodes[value["node_id"]]
            if value.get("version") is not None and value["version"] != n.version:
                PassportPositionService.fail(
                    "Установленный состав изменился. Обновите строки замены.",
                    "revision",
                )
        selected_by_role = {}
        for role in ("component", "element"):
            selected_by_role[role] = [
                states[x["node_id"]] for x in links if x["role"] == role
            ]
            selected = selected_by_role[role]
            if selected:
                setattr(case, role + "_quantity", len(selected))
                setattr(
                    case,
                    role + "_serial_number_old",
                    ", ".join(s.get("serial_number") or "б/н" for s in selected),
                )
                setattr(
                    case,
                    role + "_manufacture_date_old",
                    ", ".join(s.get("manufacture_date_text") or "—" for s in selected),
                )
        case.passport_selection_key = cls.selection_key(links, states)
        # Сначала удаляем связи элементов, затем их родительских компонентов
        await session.execute(
            delete(CasePassportLink).where(
                CasePassportLink.case_id == case.id,
                CasePassportLink.parent_link_id.is_not(None),
            )
        )
        await session.execute(
            delete(CasePassportLink).where(CasePassportLink.case_id == case.id)
        )
        parent_links = {}
        for role in ("component", "element"):
            for order, link in enumerate(x for x in links if x["role"] == role):
                nid = link["node_id"]
                row = CasePassportLink(
                    case_id=case.id,
                    node_id=nid,
                    role=role,
                    parent_link_id=parent_links.get(link.get("parent_node_id")),
                    selected_state=states[nid],
                    position_context=PassportPositionService.context(
                        nodes[nid], by_code
                    ),
                    sort_order=order,
                )
                session.add(row)
                await session.flush()
                if role == "component":
                    parent_links[nid] = row.id
        affected = set()
        if previous:
            affected |= await PassportHistoryService.close_event(
                session, previous, actor, "superseded", "Редактирование случая"
            )
        if plan:
            revision = (
                await session.scalar(
                    select(func.max(ProductPassportEvent.revision)).where(
                        ProductPassportEvent.source_case_id == case.id
                    )
                )
                or 0
            ) + 1
            order = (
                previous.day_order
                if previous and previous.effective_date == case.fault_date
                else (
                    await session.scalar(
                        select(func.max(ProductPassportEvent.day_order)).where(
                            ProductPassportEvent.passport_id == case.passport_id,
                            ProductPassportEvent.effective_date == case.fault_date,
                        )
                    )
                    or 0
                )
                + 1
            )
            malfunction = await session.get(Malfunction, case.malfunction_id)
            display = await CaseFilterService.get_display_number(session, case.id)
            event = ProductPassportEvent(
                passport_id=case.passport_id,
                case_id=case.id,
                source_case_id=case.id,
                kind="case_replacement",
                effective_date=case.fault_date,
                day_order=order,
                revision=revision,
                actor_id=actor.id,
                actor_name=actor.full_name or actor.login,
                status="active",
                supersedes_id=previous.id if previous else None,
                case_snapshot={
                    "display_number": display,
                    "creator_id": case.created_by_id,
                    "creator_name": case.created_by_name,
                    "creator_source": case.creator_source,
                    "malfunction_id": case.malfunction_id,
                    "malfunction": malfunction.defect_name if malfunction else None,
                    "repair_type_id": case.repair_type_id,
                    "fault_date": case.fault_date.isoformat(),
                },
            )
            session.add(event)
            await session.flush()
            suppliers = {}
            for eid in {v.get("equipment_id") for v in supplied.values()}:
                suppliers[eid] = (
                    await EquipmentService.resolve_supplier(
                        session,
                        equipment_id=eid,
                        locomotive_number=case.locomotive_number,
                        locomotive_model_id=case.locomotive_model_id,
                    )
                    if eid
                    else None
                )
            for item in plan:
                value = supplied[item["node_id"]]
                old = item["before_state"]
                new = PassportPositionService.replacement_state(
                    item,
                    value,
                    equipment,
                    has_children=len(
                        PassportPositionService.descendants(
                            nodes[item["node_id"]], nodes, by_code
                        )
                    )
                    > 1,
                )
                new["supplier_id"] = suppliers.get(new["equipment_id"])
                session.add(
                    ProductPassportEventItem(
                        event_id=event.id,
                        node_id=item["node_id"],
                        scope=item["scope"],
                        group_key=item["group_key"],
                        position_context=item["context"],
                        before_state=old,
                        after_state=new,
                        changed_fields=list(PassportPositionService.INSTANCE_FIELDS),
                    )
                )
                affected.add(item["node_id"])
            # В общие поля случая записываем выбранное оборудование без остальных детей КМБ
            for role in ("component", "element"):
                values = [
                    supplied[x["node_id"]]
                    for x in links
                    if x["role"] == role and x["node_id"] in supplied
                ]
                if values:
                    setattr(case, "new_" + role + "_quantity", len(values))
                    setattr(
                        case,
                        role + "_serial_number_new",
                        ", ".join(
                            PassportPositionService.clean(x.get("serial_number"))
                            or "б/н"
                            for x in values
                        ),
                    )
                    setattr(
                        case,
                        role + "_manufacture_date_new",
                        ", ".join(
                            PassportPositionService.clean(
                                x.get("manufacture_date_text")
                            )
                            or "—"
                            for x in values
                        ),
                    )
                    types = {x.get("equipment_id") for x in values}
                    setattr(
                        case,
                        "new_" + role + "_equipment_id",
                        next(iter(types)) if len(types) == 1 else None,
                    )
            case.new_supplier_id = suppliers.get(
                case.new_element_equipment_id or case.new_component_equipment_id
            )
        await session.flush()
        await PassportHistoryService.recalculate(session, affected)

    @classmethod
    async def case_details(cls, session, case):
        """Добавляет выбранные экземпляры в подробности случая"""
        links = (
            await session.scalars(
                select(CasePassportLink)
                .where(CasePassportLink.case_id == case.id)
                .order_by(CasePassportLink.sort_order, CasePassportLink.id)
            )
        ).all()
        ids = {x.node_id for x in links}
        versions = (
            dict(
                (
                    await session.execute(
                        select(
                            ProductPassportNode.id, ProductPassportNode.version
                        ).where(ProductPassportNode.id.in_(ids))
                    )
                ).all()
            )
            if ids
            else {}
        )
        by_id = {x.id: x for x in links}
        case.passport_links = [
            dict(
                node_id=x.node_id,
                role=x.role,
                version=versions[x.node_id],
                parent_node_id=(
                    by_id[x.parent_link_id].node_id
                    if x.parent_link_id in by_id
                    else None
                ),
                state=x.selected_state,
                context=x.position_context,
            )
            for x in links
        ]
        await cls.attach_replacements(session, [case])
        return case

    @staticmethod
    async def attach_replacements(session, cases):
        """Добавляет установленное оборудование к списку случаев"""
        grouped = defaultdict(list)
        stmt = (
            select(ProductPassportEvent.case_id, ProductPassportEventItem)
            .join(ProductPassportEventItem)
            .where(
                ProductPassportEvent.case_id.in_([c.id for c in cases]),
                ProductPassportEvent.status == "active",
            )
            .order_by(ProductPassportEventItem.id)
        )
        for case_id, item in (await session.execute(stmt)).all():
            grouped[case_id].append(
                dict(
                    node_id=item.node_id,
                    **item.after_state,
                    context=item.position_context,
                    scope=item.scope,
                    group_key=item.group_key,
                )
            )
        for case in cases:
            case.replacement_items = grouped[case.id]

    @classmethod
    async def delete_case(cls, session, case, actor):
        """Отменяет замену и удаляет паспортные связи случая"""
        await session.execute(
            select(ProductPassport.id)
            .where(ProductPassport.id == case.passport_id)
            .with_for_update()
        )
        event = await session.scalar(
            select(ProductPassportEvent).where(
                ProductPassportEvent.case_id == case.id,
                ProductPassportEvent.status == "active",
            )
        )
        if event:
            affected = await PassportHistoryService.close_event(
                session, event, actor, "voided", "Удаление случая"
            )
            await PassportHistoryService.recalculate(session, affected)
        await session.execute(
            delete(CasePassportLink).where(
                CasePassportLink.case_id == case.id,
                CasePassportLink.parent_link_id.is_not(None),
            )
        )
        await session.execute(
            delete(CasePassportLink).where(CasePassportLink.case_id == case.id)
        )
