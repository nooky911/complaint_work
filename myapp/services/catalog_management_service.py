from sqlalchemy.dialects.postgresql import JSONPATH, insert
from fastapi import HTTPException
from sqlalchemy import select, delete, func, or_, cast, Table

from myapp.database.base import Base
from myapp.database.transactional import transactional
from myapp.loco.models.equipment import Equipment, EquipmentMalfunction
from myapp.train.models.equipment import TrainEquipment, TrainEquipmentMalfunction
from myapp.models.auxiliaries import Supplier
from myapp.models.malfunctions import Malfunction
from myapp.models.product_passports import (
    ProductPassportEventItem,
    ProductPassportNode,
    CasePassportLink,
    ProductPassportEvent,
)
from myapp.train.models.case_details import TrainCaseDetails
from myapp.models.repair_case_equipment import RepairCaseEquipment as Case
from myapp.utils.equipment_hierarchy import inherited_equipment_value
from myapp.services.reference_service import ReferenceService
from myapp.services.cache_service import cache


def authorize_catalog(user, direction):
    """Разрешает редактору только свой справочник при выданном администратором доступе"""
    if (
        not user.is_active
        or user.restricted_access
        or not (
            user.role == "superadmin"
            or user.role == "editor"
            and user.direction == direction
            and user.can_manage_equipment
        )
    ):
        raise HTTPException(
            403, "Нет разрешения на управление оборудованием этого раздела"
        )


def catalog_models(direction):
    """Выбирает раздельные таблицы оборудования и связей"""
    return (
        (TrainEquipment, TrainEquipmentMalfunction)
        if direction == "train"
        else (Equipment, EquipmentMalfunction)
    )


async def catalog_data(session, direction):
    """Возвращает дерево и общие справочники для единого редактора"""
    model, link = catalog_models(direction)
    columns = Base.metadata.tables[model.__tablename__].c
    link_columns = Base.metadata.tables[link.__tablename__].c
    items = (await session.scalars(select(model).order_by(columns.id))).all()
    by_id = {item.id: item for item in items}
    references = await ReferenceService.get_case_form_references()
    links = (
        await session.execute(
            select(link_columns.equipment_id, link_columns.malfunction_id)
        )
    ).all()
    return dict(
        equipment=[
            dict(
                id=item.id,
                name=item.equipment_name,
                parent_id=item.parent_id,
                supplier_id=item.supplier_id,
                effective_supplier_id=inherited_equipment_value(
                    item.id, by_id, "supplier_id"
                ),
            )
            for item in items
        ],
        suppliers=references["suppliers"],
        malfunctions=references["malfunctions"],
        links=[dict(equipment_id=e, malfunction_id=m) for e, m in links],
    )


@transactional
async def save_catalog_item(session, direction, equipment_id, data):
    """Создаёт или изменяет позицию и её явного поставщика без перемещения ветки"""
    model, _ = catalog_models(direction)
    columns = Base.metadata.tables[model.__tablename__].c
    name = data.name.strip()
    if not name:
        raise HTTPException(422, "Введите наименование")
    if data.supplier_id and not await session.get(Supplier, data.supplier_id):
        raise HTTPException(422, "Поставщик не найден")
    if equipment_id:
        item = await session.scalar(
            select(model).where(columns.id == equipment_id).with_for_update()
        )
        if not item:
            raise HTTPException(404, "Оборудование не найдено")
    else:
        parent = await session.get(model, data.parent_id) if data.parent_id else None
        if data.parent_id and not parent:
            raise HTTPException(404, "Родитель не найден")
        item = model(parent_id=data.parent_id)
        if direction == "train":
            item.level = parent.level + 1 if parent else 1
            if item.level > 4:
                raise HTTPException(422, "Допустимо не более четырёх уровней")
        else:
            depth = 0
            current = parent
            while current:
                depth += 1
                current = (
                    await session.get(model, current.parent_id)
                    if current.parent_id
                    else None
                )
            if depth > 4:
                raise HTTPException(422, "Допустимо не более пяти уровней")
    duplicate = await session.scalar(
        select(columns.id).where(
            columns.parent_id == item.parent_id,
            func.lower(columns.equipment_name) == name.lower(),
            columns.id != equipment_id,
        )
    )
    if duplicate:
        raise HTTPException(409, "Такое оборудование уже есть у этого родителя")
    previous_supplier = item.supplier_id
    item.equipment_name = name
    item.supplier_id = data.supplier_id
    if not equipment_id:
        session.add(item)
    await session.flush()
    if previous_supplier != item.supplier_id:
        if direction == "loco":
            from myapp.loco.services.equipment_service import EquipmentService

            await EquipmentService.refresh_case_suppliers(session, item.id)
        else:
            equipment = {
                entry.id: entry
                for entry in (await session.scalars(select(model))).all()
            }
            affected = {item.id}
            pending = [item.id]
            while pending:
                parent_id = pending.pop()
                for entry in equipment.values():
                    if (
                        entry.parent_id == parent_id
                        and entry.supplier_id is None
                        and entry.id not in affected
                    ):
                        affected.add(entry.id)
                        pending.append(entry.id)
            rows = (
                await session.execute(
                    select(Case, TrainCaseDetails)
                    .join(TrainCaseDetails, TrainCaseDetails.case_id == Case.id)
                    .where(Case.direction == "train")
                    .with_for_update()
                    .execution_options(populate_existing=True)
                )
            ).all()
            for case, details in rows:
                changed = False
                for fields, supplier_field in (
                    (("element_id", "component_id", "equipment_id"), "supplier_id"),
                    (
                        ("new_element_id", "new_component_id", "new_equipment_id"),
                        "new_supplier_id",
                    ),
                ):
                    leaf = next(
                        (
                            getattr(details, key)
                            for key in fields
                            if getattr(details, key)
                        ),
                        None,
                    )
                    if leaf in affected:
                        supplier_id = inherited_equipment_value(
                            leaf, equipment, "supplier_id"
                        )
                        if getattr(case, supplier_field) != supplier_id:
                            setattr(case, supplier_field, supplier_id)
                            changed = True
                if changed:
                    case.revision += 1
    cache.clear_after_commit(session)
    return dict(id=item.id)


@transactional
async def delete_catalog_reference(session, kind, reference_id):
    """Запрещает удаление используемых записей и возвращает случаи обоих разделов"""
    model = Supplier if kind == "suppliers" else Malfunction
    columns = Base.metadata.tables[model.__tablename__].c
    item = await session.scalar(
        select(model).where(columns.id == reference_id).with_for_update()
    )
    if not item:
        raise HTTPException(404, "Запись не найдена")
    condition = (
        or_(Case.supplier_id == reference_id, Case.new_supplier_id == reference_id)
        if kind == "suppliers"
        else Case.malfunction_id == reference_id
    )
    numbered = select(
        Case.id,
        Case.direction,
        func.row_number()
        .over(partition_by=Case.direction, order_by=Case.id)
        .label("number"),
    ).subquery()
    cases = (
        await session.execute(
            select(numbered.c.direction, numbered.c.number)
            .join(Case, Case.id == numbered.c.id)
            .where(condition)
            .order_by(numbered.c.direction, numbered.c.number)
        )
    ).all()
    if cases:
        raise HTTPException(
            409,
            dict(
                message="Удаление запрещено: запись используется в случаях",
                cases=[dict(direction=d, number=n) for d, n in cases],
            ),
        )
    if kind == "suppliers" and await session.scalar(
        select(ProductPassportEventItem.id)
        .where(
            or_(
                ProductPassportEventItem.before_state["supplier_id"].astext
                == str(reference_id),
                ProductPassportEventItem.after_state["supplier_id"].astext
                == str(reference_id),
            )
        )
        .limit(1)
    ):
        raise HTTPException(
            409,
            dict(
                message="Удаление запрещено: поставщик используется в истории паспортов",
                cases=[],
            ),
        )
    if kind == "suppliers":
        for owner, column in (
            (ProductPassportNode, ProductPassportNode.baseline_state),
            (CasePassportLink, CasePassportLink.selected_state),
            (ProductPassportEvent, ProductPassportEvent.case_snapshot),
        ):
            if await session.scalar(
                select(Base.metadata.tables[owner.__tablename__].c.id)
                .where(
                    func.jsonb_path_exists(
                        column,
                        cast("$.**.supplier_id ? (@ == $id)", JSONPATH),
                        func.jsonb_build_object("id", reference_id),
                    )
                )
                .limit(1)
            ):
                raise HTTPException(
                    409,
                    dict(
                        message="Удаление запрещено: поставщик сохранён в истории паспортов",
                        cases=[],
                    ),
                )
    target = model.__tablename__
    removable = []
    table: Table
    for table in Base.metadata.sorted_tables:
        for column in table.columns:
            if not any(fk.column.table.name == target for fk in column.foreign_keys):
                continue
            if kind == "malfunctions" and table.name in (
                "loco_equipment_malfunctions",
                "train_equipment_malfunctions",
            ):
                removable.append((table, column))
                continue
            if (
                await session.scalar(
                    select(column).where(column == reference_id).limit(1)
                )
                is not None
            ):
                raise HTTPException(
                    409,
                    dict(
                        message="Удаление запрещено: запись используется в оборудовании, паспортах или правилах связи",
                        cases=[],
                    ),
                )
    for table, column in removable:
        await session.execute(delete(table).where(column == reference_id))
    await session.delete(item)
    await session.flush()
    cache.clear_after_commit(session)
    return dict(deleted=True)


@transactional
async def copy_equipment_malfunctions(session, direction, target_id, source_id):
    """Добавляет связи другого оборудования своего раздела без дублей и замены имеющихся"""
    model, link = catalog_models(direction)
    columns = Base.metadata.tables[model.__tablename__].c
    link_columns = Base.metadata.tables[link.__tablename__].c
    if source_id == target_id:
        raise HTTPException(422, "Выберите другое оборудование")
    items = (
        await session.scalars(
            select(model)
            .where(columns.id.in_([target_id, source_id]))
            .order_by(columns.id)
            .with_for_update()
        )
    ).all()
    if {item.id for item in items} != {target_id, source_id}:
        raise HTTPException(404, "Оборудование не найдено в этом разделе")
    source_ids = sorted(
        set(
            (
                await session.scalars(
                    select(link_columns.malfunction_id).where(
                        link_columns.equipment_id == source_id
                    )
                )
            ).all()
        )
    )
    if not source_ids:
        return dict(added=0, skipped=0)
    added = await _insert_malfunction_links(session, link, target_id, source_ids)
    cache.clear_after_commit(session)
    return dict(added=added, skipped=len(source_ids) - added)


async def _insert_malfunction_links(session, link, equipment_id, ids):
    """Добавляет связи одним запросом и пропускает уже существующие"""

    if not ids:
        return 0
    link_columns = Base.metadata.tables[link.__tablename__].c
    statement = insert(link).values(
        [dict(equipment_id=equipment_id, malfunction_id=value) for value in ids]
    )
    return len(
        (
            await session.scalars(
                statement.on_conflict_do_nothing(
                    index_elements=["equipment_id", "malfunction_id"]
                ).returning(link_columns.malfunction_id)
            )
        ).all()
    )


@transactional
async def attach_catalog_malfunctions(session, direction, equipment_id, ids):
    """Проверяет весь набор неисправностей перед атомарной привязкой"""
    model, link = catalog_models(direction)
    columns = Base.metadata.tables[model.__tablename__].c
    if not await session.scalar(
        select(columns.id).where(columns.id == equipment_id).with_for_update()
    ):
        raise HTTPException(404, "Оборудование не найдено")
    ids = sorted(set(ids))
    existing = set(
        (
            await session.scalars(select(Malfunction.id).where(Malfunction.id.in_(ids)))
        ).all()
    )
    if existing != set(ids):
        raise HTTPException(
            422, "Одна из выбранных неисправностей больше не существует"
        )
    added = await _insert_malfunction_links(session, link, equipment_id, ids)
    cache.clear_after_commit(session)
    return dict(added=added, skipped=len(ids) - added)
