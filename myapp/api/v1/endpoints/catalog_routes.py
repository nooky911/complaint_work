from functools import wraps
from typing import Annotated, Literal
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from myapp.auth.dependencies import get_current_user
from myapp.database.base import get_db
from myapp.models.user import User
from myapp.models.malfunctions import Malfunction
from myapp.loco.services.equipment_service import EquipmentService
from myapp.schemas.catalogs import SupplierUpdate, MalfunctionUpdate, EquipmentName
from myapp.services.catalog_management_service import (
    authorize_catalog,
    catalog_models,
    catalog_data,
    save_catalog_item,
    delete_catalog_reference,
    copy_equipment_malfunctions,
    attach_catalog_malfunctions,
)
from myapp.database.transactional import transactional
from myapp.services.cache_service import cache

router = APIRouter(prefix="/catalog", tags=["Редактор оборудования"])
Session = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]
Direction = Literal["loco", "train"]


def catalog_errors(func):
    """Преобразует ошибки справочника и конкурентных изменений в ответ API"""

    @wraps(func)
    async def wrapped(*args, **kwargs):
        """Сохраняет понятную причину отказа при конфликте справочных данных"""
        try:
            return await func(*args, **kwargs)
        except IntegrityError as error:
            raise HTTPException(
                409, "Запись уже существует или используется; обновите справочник"
            ) from error
        except ValueError as error:
            raise HTTPException(422, str(error)) from error

    return wrapped


class CatalogItemData(BaseModel):
    """Наименование, родитель и явный поставщик позиции"""

    name: EquipmentName = Field(min_length=1, max_length=1000)
    parent_id: int | None = None
    supplier_id: int | None = None


class CatalogNameData(BaseModel):
    """Название создаваемой или переименовываемой записи"""

    name: str = Field(min_length=1, max_length=255)


@router.get("/{direction}")
async def get_catalog(direction: Direction, session: Session, user: CurrentUser):
    """Возвращает данные доступного редактору направления"""
    authorize_catalog(user, direction)
    return await catalog_data(session, direction)


@router.post("/{direction}/equipment")
@router.put("/{direction}/equipment/{equipment_id}")
async def save_equipment(
    direction: Direction,
    data: CatalogItemData,
    session: Session,
    user: CurrentUser,
    equipment_id: int = 0,
):
    """Сохраняет позицию без возможности удаления оборудования"""
    authorize_catalog(user, direction)
    try:
        return await save_catalog_item(session, direction, equipment_id, data)
    except IntegrityError:
        raise HTTPException(409, "Запись уже существует или используется")


@router.post("/{direction}/{kind}")
@router.put("/{direction}/{kind}/{reference_id}")
@catalog_errors
@transactional
async def save_reference(
    direction: Direction,
    kind: Literal["suppliers", "malfunctions"],
    data: CatalogNameData,
    session: Session,
    user: CurrentUser,
    reference_id: int = 0,
):
    """Создаёт или переименовывает общий справочник независимо от выбора оборудования"""
    authorize_catalog(user, direction)
    name = data.name.strip()
    if not name:
        raise HTTPException(422, "Введите название")
    if kind == "suppliers":
        if reference_id:
            item = await EquipmentService.update_supplier(
                session, reference_id, SupplierUpdate(supplier_name=name)
            )
        else:
            item, _ = await EquipmentService.get_or_create_supplier(session, name)
    else:
        if reference_id:
            item = await EquipmentService.update_malfunction(
                session, reference_id, MalfunctionUpdate(defect_name=name)
            )
        else:
            item = await session.scalar(
                select(Malfunction).where(Malfunction.defect_name == name)
            )
            if item is None:
                item = Malfunction(defect_name=name)
                session.add(item)
                await session.flush()
    cache.clear_after_commit(session)
    return dict(id=item.id)


@router.put("/{direction}/equipment/{equipment_id}/malfunctions/{malfunction_id}")
@router.delete("/{direction}/equipment/{equipment_id}/malfunctions/{malfunction_id}")
@catalog_errors
@transactional
async def link_malfunction(
    direction: Direction,
    equipment_id: int,
    malfunction_id: int,
    session: Session,
    user: CurrentUser,
    request: Request,
):
    """Добавляет или удаляет только связь неисправности с выбранной позицией"""
    authorize_catalog(user, direction)
    model, link = catalog_models(direction)
    if not await session.get(model, equipment_id) or not await session.get(
        Malfunction, malfunction_id
    ):
        raise HTTPException(404, "Запись не найдена")
    row = await session.scalar(
        select(link).where(
            link.equipment_id == equipment_id, link.malfunction_id == malfunction_id
        )
    )
    if request.method == "DELETE":
        if row:
            await session.delete(row)
    elif row is None:
        session.add(link(equipment_id=equipment_id, malfunction_id=malfunction_id))
    await session.flush()
    cache.clear_after_commit(session)
    return dict(saved=True)


@router.delete("/{direction}/{kind}/{reference_id}")
async def delete_reference(
    direction: Direction,
    kind: Literal["suppliers", "malfunctions"],
    reference_id: int,
    session: Session,
    user: CurrentUser,
):
    """Удаляет неиспользуемый справочник исключительно по правам администратора"""
    authorize_catalog(user, direction)
    if user.role != "superadmin":
        raise HTTPException(403, "Удаление доступно только администратору")
    try:
        return await delete_catalog_reference(session, kind, reference_id)
    except IntegrityError:
        raise HTTPException(409, "Запись используется, удаление отменено")


class CopyMalfunctionsData(BaseModel):
    """Источник связей из оборудования того же направления"""

    source_equipment_id: int = Field(gt=0)


@router.post("/{direction}/equipment/{equipment_id}/copy-malfunctions")
@catalog_errors
async def copy_malfunctions(
    direction: Direction,
    equipment_id: int,
    data: CopyMalfunctionsData,
    session: Session,
    user: CurrentUser,
):
    """Привязывает неисправности другого оборудования своего направления одним действием"""
    authorize_catalog(user, direction)
    return await copy_equipment_malfunctions(
        session, direction, equipment_id, data.source_equipment_id
    )


class AttachMalfunctionsData(BaseModel):
    """Набор существующих неисправностей для одной операции привязки"""

    malfunction_ids: list[int] = Field(min_length=1, max_length=1000)


@router.post("/{direction}/equipment/{equipment_id}/malfunctions")
@catalog_errors
async def attach_malfunctions(
    direction: Direction,
    equipment_id: int,
    data: AttachMalfunctionsData,
    session: Session,
    user: CurrentUser,
):
    """Привязывает несколько выбранных неисправностей одной транзакцией"""
    authorize_catalog(user, direction)
    return await attach_catalog_malfunctions(
        session, direction, equipment_id, data.malfunction_ids
    )
