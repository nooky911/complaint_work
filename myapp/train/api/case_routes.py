import json

from typing import Annotated, Literal
from fastapi.responses import StreamingResponse
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select, func, String
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date

from myapp.auth.dependencies import get_current_user, require_can_edit_case
from myapp.database.base import get_db
from myapp.models.user import User
from myapp.models.product_passports import ProductPassport, ProductPassportNode
from myapp.models.repair_case_equipment import RepairCaseEquipment as Case
from myapp.train.models.case_details import TrainCaseDetails
from myapp.train.models.equipment import TrainEquipment, TrainEquipmentMalfunction
from myapp.train.models.train_models import TrainModel
from myapp.train.schemas.cases import TrainCaseInput, TrainReplacementPreview
from myapp.services import CaseValidationError
from myapp.services.omega_services.passport_case_service import PassportCaseService
from myapp.train.services.passport_selection_service import (
    train_passport_links,
    train_replacement_plan,
)
from myapp.train.services.export_service import export_train_cases
from myapp.train.services.case_service import TrainCaseService, wagon_nodes
from myapp.train.services.passport_selection_service import passport_selection
from myapp.services.reference_service import ReferenceService
from myapp.services.warranty_service import WarrantyService
from myapp.models.auxiliaries import FaultDiscoveryPlace
from myapp.services.case_service import CaseService
from myapp.loco.services.case_status_service import CaseStatusService
from myapp.database.query_builders.query_case_builders import load_detail_relations
from myapp.services.user_access_service import UserAccessService
from myapp.train.services.filter_service import (
    apply_train_filters,
    train_filter_options,
)

router = APIRouter(prefix="/train", tags=["Электропоезда"])
Session = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.get("/references")
async def references(session: Session, user: CurrentUser):
    """Возвращает общие справочники и отдельное поездное дерево оборудования"""
    result = WarrantyService.filter_train_references(dict(await ReferenceService.get_case_form_references()))
    result["repair_types"] = [item for item in result.get("repair_types", []) if item["id"] != 8]
    result.pop("locomotive_models", None)
    result["fault_discovered_at"] = [
        dict(id=e.id, name=e.name)
        for e in (await session.scalars(select(FaultDiscoveryPlace))).all()
        if ReferenceService.discovery_allowed(e.name, "train")
    ]
    result["train_models"] = [
        dict(id=m.id, name=m.train_model_name)
        for m in (await session.scalars(select(TrainModel))).all()
    ]
    result["equipment"] = [
        dict(
            id=e.id,
            name=e.equipment_name,
            parent_id=e.parent_id,
            level=e.level,
            supplier_id=e.supplier_id,
            designation=e.designation,
        )
        for e in (
            await session.scalars(select(TrainEquipment).order_by(TrainEquipment.id))
        ).all()
    ]
    result["equipment_malfunctions"] = [
        dict(equipment_id=e, malfunction_id=m)
        for e, m in (
            await session.execute(
                select(
                    TrainEquipmentMalfunction.equipment_id,
                    TrainEquipmentMalfunction.malfunction_id,
                )
            )
        ).all()
    ]
    return result


@router.get("/passports")
async def passports(session: Session, user: CurrentUser, model_id: int = Query(gt=0)):
    """Предлагает только номера поездов с уже загруженным паспортом"""
    return [
        dict(id=p.id, number=p.product_number, name=p.omega_name)
        for p in (
            await session.scalars(
                select(ProductPassport)
                .where(ProductPassport.train_model_id == model_id)
                .order_by(ProductPassport.product_number)
            )
        ).all()
    ]


@router.post("/passports/{passport_id}/replacement-preview")
async def replacement_preview(
    passport_id: int, data: TrainReplacementPreview, session: Session, user: CurrentUser
):
    """Показывает заменяемую ветку вместе с детьми через общий паспортный механизм"""
    if user.role not in ("editor", "superadmin"):
        raise HTTPException(403, "Недостаточно прав")
    try:
        passport, nodes, states, equipment, _, _ = await passport_selection(
            session,
            passport_id,
            data.train.wagon_node_ids,
            data.fault_date,
            data.case_id,
        )
        if passport.train_model_id != data.train.train_model_id:
            raise HTTPException(422, "Паспорт не соответствует модели поезда")
        by_code = {node.omega_code: node for node in nodes.values()}
        links = train_passport_links(
            data.train,
            nodes,
            states,
            by_code,
            (
                [link.model_dump() for link in data.passport_links]
                if data.passport_links is not None
                else None
            ),
        )
        return train_replacement_plan(
            nodes, states, equipment, by_code, data.train, data.repair_type_id, links
        )
    except CaseValidationError as exc:
        raise HTTPException(409 if exc.field == "revision" else 422, str(exc)) from exc


@router.get("/passports/{passport_id}")
async def passport_nodes(
    passport_id: int,
    session: Session,
    user: CurrentUser,
    wagon_node_ids: Annotated[str, Query(pattern=r"^([0-9]+(,[0-9]+)*)?$")] = "",
    fault_date: date | None = None,
    case_id: int | None = None,
):
    """Возвращает вагоны и экземпляры оборудования выбранного поездного паспорта"""
    p = await session.get(ProductPassport, passport_id)
    if not p or p.train_model_id is None:
        raise HTTPException(404, "Поездной паспорт не найден")
    _, node_map, states, catalogue, owners, allowed = await passport_selection(
        session,
        passport_id,
        [int(value) for value in wagon_node_ids.split(",") if value],
        fault_date,
        case_id,
    )
    nodes = list(node_map.values())
    return dict(
        allowed_equipment_ids=allowed,
        wagons=[
            dict(id=n.id, name=n.tree_name, omega_code=n.omega_code)
            for n in wagon_nodes(nodes)
        ],
        nodes=[
            dict(
                id=n.id,
                name=states[n.id].get("full_name")
                or states[n.id].get("tree_name")
                or n.tree_name,
                tree_name=n.tree_name,
                omega_code=n.omega_code,
                parent_omega_code=n.parent_omega_code,
                wagon_id=owners.get(n.id),
                version=n.version,
                serial_number=states[n.id].get("serial_number"),
                manufacture_date=states[n.id].get("manufacture_date_text")
                or states[n.id].get("manufacture_date"),
                designation=n.designation,
                equipment_id=states[n.id].get("equipment_id"),
                supplier_id=(
                    catalogue[states[n.id].get("equipment_id")]["supplier_id"]
                    if states[n.id].get("equipment_id") in catalogue
                    else n.supplier_id
                ),
                manufacturer=(
                    catalogue[states[n.id].get("equipment_id")]["manufacturer"]
                    if states[n.id].get("equipment_id") in catalogue
                    else n.manufacturer
                ),
            )
            for n in nodes
            if states[n.id].get("is_present", True)
        ],
    )


@router.get("/cases")
async def list_cases(
    session: Session,
    user: CurrentUser,
    page: int = Query(1, ge=1),
    search: str = Query("", max_length=10, pattern=r"^[0-9]*$"),
    limit: int = Query(25, ge=1, le=100),
    sort_order: Literal["asc", "desc"] = "desc",
    filters: Annotated[str, Query(max_length=20000)] = "{}",
):
    """Показывает поездные случаи с поиском по отображаемому номеру случая"""
    numbered = (
        select(Case.id, func.row_number().over(order_by=Case.id).label("number"))
        .where(Case.direction == "train")
        .cte("train_numbered_cases")
    )
    stmt = (
        select(Case, TrainCaseDetails, numbered.c.number, CaseStatusService.build_status_subquery("train"))
        .join(TrainCaseDetails, TrainCaseDetails.case_id == Case.id)
        .join(numbered, numbered.c.id == Case.id)
    )
    try:
        selected_filters = json.loads(filters)
        if not isinstance(selected_filters, dict):
            raise ValueError
        stmt = apply_train_filters(stmt, selected_filters)
    except (ValueError, TypeError):
        raise HTTPException(422, "Некорректные фильтры")
    if search.strip():
        stmt = stmt.where(numbered.c.number == int(search))
    total = await session.scalar(
        select(func.count()).select_from(stmt.with_only_columns(Case.id).subquery())
    )
    rows = (
        await session.execute(
            stmt.options(*load_detail_relations())
            .order_by(Case.id.asc() if sort_order == "asc" else Case.id.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )
    ).all()
    rows = [(CaseStatusService.enrich_case_with_status_and_creator(case, status), extension, number)
            for case, extension, number, status in rows]
    wagon_ids = {i for _, extension, _ in rows for i in extension.wagon_node_ids}
    names = dict(
        (
            await session.execute(
                select(ProductPassportNode.id, ProductPassportNode.tree_name).where(
                    ProductPassportNode.id.in_(wagon_ids)
                )
            )
        ).all()
    )
    partner_ids = (
        set((await session.scalars(UserAccessService.partner_ids(user.id))).all())
        if user.role == "editor" and user.direction == "train"
        else set()
    )
    await PassportCaseService.attach_replacements(
        session, [case for case, _, _ in rows]
    )
    return dict(
        items=[
            TrainCaseService.serialize(
                case,
                extension,
                user.role == "superadmin"
                or (
                    user.role == "editor"
                    and user.direction == "train"
                    and (case.user_id == user.id or case.user_id in partner_ids)
                ),
                names,
                number,
            )
            for case, extension, number in rows
        ],
        total=total,
    )


@router.get("/case-numbers")
async def case_numbers(
    session: Session,
    user: CurrentUser,
    search: str = Query("", max_length=10, pattern=r"^[0-9]*$"),
    limit: int = Query(50, ge=1, le=100),
):
    """Возвращает отображаемые номера поездных случаев для общего выпадающего поиска"""
    numbered = (
        select(func.row_number().over(order_by=Case.id).label("number"))
        .where(Case.direction == "train")
        .subquery()
    )
    stmt = select(numbered.c.number)
    if search:
        stmt = stmt.where(
            numbered.c.number.cast(String).startswith(search, autoescape=True)
        ).order_by(numbered.c.number.asc())
    else:
        stmt = stmt.order_by(numbered.c.number.desc())
    return list((await session.scalars(stmt.limit(limit))).all())


# Экспорт поездных случаев
@router.get("/export")
async def export_cases(
    session: Session,
    user: CurrentUser,
    filters: Annotated[str, Query(max_length=20000)] = "{}",
    sort_order: Literal["asc", "desc"] = "desc",
    search: str = Query("", max_length=10, pattern=r"^[0-9]*$"),
):
    """Скачивает поездной Excel по тем же фильтрам, что применены в списке"""
    try:
        values = json.loads(filters)
        if not isinstance(values, dict):
            raise ValueError("Некорректные фильтры")
        stream, filename = await export_train_cases(session, values, sort_order, search)
    except (ValueError, TypeError) as error:
        raise HTTPException(
            404 if str(error) == "Нет данных для экспорта" else 422, str(error)
        )
    return StreamingResponse(
        stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=utf-8''{filename}"},
    )


@router.get("/cases/{case_id}")
async def detail(case_id: int, session: Session, user: CurrentUser):
    """Открывает общую карточку с поездным расширением"""
    return await TrainCaseService.get(session, case_id, user)


@router.post("/cases", status_code=201)
async def create(data: TrainCaseInput, session: Session, user: CurrentUser):
    """Создаёт поездной случай с общими документами"""
    return await save_case(session, data, user)


@router.put("/cases/{case_id}")
async def update(
    case_id: int, data: TrainCaseInput, session: Session, user: CurrentUser
):
    """Сохраняет полный поездной случай независимо от открытой вкладки"""
    return await save_case(session, data, user, case_id)


@router.post("/cases/{case_id}/lock")
async def lock(case_id: int, session: Session, user: CurrentUser):
    """Использует существующую блокировку общей записи случая"""
    case = await TrainCaseService.get(session, case_id, user)
    if not case["can_edit"]:
        raise HTTPException(403, "Недостаточно прав")
    try:
        await CaseService.lock_case(session, case_id, user.id)
    except ValueError as exc:
        raise HTTPException(423, str(exc)) from exc
    return await TrainCaseService.get(session, case_id, user)


@router.post("/cases/{case_id}/heartbeat")
async def heartbeat(case_id: int, session: Session, user: CurrentUser):
    """Поддерживает блокировку только во время открытого редактирования"""
    case = await TrainCaseService.get(session, case_id, user)
    if not case["can_edit"]:
        raise HTTPException(403, "Недостаточно прав")
    try:
        await CaseService.heartbeat_case(session, case_id, user.id)
    except ValueError as exc:
        raise HTTPException(423, str(exc)) from exc
    return {"ok": True}


@router.post("/cases/{case_id}/unlock")
async def unlock(case_id: int, session: Session, user: CurrentUser):
    """Снимает собственную блокировку при отмене или закрытии карточки"""
    await TrainCaseService.get(session, case_id, user)
    return {"ok": await CaseService.unlock_case(session, case_id, user.id)}


async def save_case(session, data, user, case_id=None):
    """Преобразует нарушение ссылок справочников в понятную ошибку формы"""
    try:
        return await TrainCaseService.save(session, data, user, case_id)
    except CaseValidationError as exc:
        raise HTTPException(409 if exc.field == "revision" else 422, str(exc)) from exc
    except IntegrityError as exc:
        raise HTTPException(
            422, "Проверьте значения справочников и обязательные поля"
        ) from exc


# Удаление поездного случая
@router.delete("/cases/{case_id}", status_code=204)
async def delete_case(
    case_id: int,
    session: Session,
    user_and_case: Annotated[tuple[User, Case | None], Depends(require_can_edit_case)],
):
    """Удаляет поездной случай через общую очистку файлов и истории паспорта"""
    user, case = user_and_case
    if case is not None and case.direction != "train":
        raise HTTPException(404, "Поездной случай не найден")
    await CaseService.delete_case(session, case_id, user.id, direction="train")


# Варианты фильтров поездных случаев
@router.get("/filter-options")
async def filter_options(
    session: Session,
    user: CurrentUser,
    filters: Annotated[str, Query(max_length=20000)] = "{}",
):
    """Возвращает варианты поездных фильтров с учётом выбранных условий"""
    try:
        values = json.loads(filters)
        if not isinstance(values, dict):
            raise ValueError
        return await train_filter_options(session, values)
    except (ValueError, TypeError):
        raise HTTPException(422, "Некорректные фильтры")
