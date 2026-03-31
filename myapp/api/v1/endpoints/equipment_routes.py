from fastapi import APIRouter, Depends, HTTPException, status, Path, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from myapp.database.base import get_db
from myapp.models.user import User
from myapp.schemas.equipment import (
    EquipmentCreate,
    EquipmentResponse,
    EquipmentUpdate,
    EquipmentWithPathResponse,
    MalfunctionResponse,
    MalfunctionUpdate,
    SupplierUpdate,
    SupplierResponse,
    SupplierCreate,
    EquipmentShortResponse,
    MalfunctionAttachRequest,
)
from myapp.services.equipment_service import EquipmentService
from myapp.auth.dependencies import (
    require_viewer_or_higher,
    require_superadmin,
)

router = APIRouter(prefix="/equipment", tags=["Оборудование"])


# ----------------------
# CRUD для оборудования


@router.get("/equipment-by-level", response_model=list[EquipmentShortResponse])
async def get_equipment_by_level(
    session: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(require_viewer_or_higher)],
    level: Annotated[int, Query(description="Уровень иерархии (0-4)", ge=0, le=4)],
    parent_id: Annotated[
        int | None, Query(description="ID родителя для фильтрации")
    ] = None,
    q: Annotated[str, Query(description="Поисковый запрос")] = "",
):
    """Возможность начинать заполнение типа оборудования с любого места вложенности"""

    if level > 0 and not parent_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Для уровня > 0 необходим parent_id",
        )

    return await EquipmentService.get_equipment_by_level(session, level, parent_id, q)


@router.get(
    "/equipment-chain/{equipment_id}",
    response_model=list[EquipmentWithPathResponse],
    summary="Получить цепочку оборудования",
)
async def get_equipment_chain(
    equipment_id: Annotated[int, Path(description="ID оборудования", ge=1)],
    session: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(require_viewer_or_higher)],
):
    """Автоматическое заполнение всех полей, которые находятся выше поля заполняемого пользователем"""
    return await EquipmentService.get_equipment_chain(session, equipment_id)


@router.get(
    "/equipment-all-flat",
    response_model=list[EquipmentWithPathResponse],
    summary="Получить всё оборудование плоским списком с путями иерархии",
)
async def get_all_equipment_flat(
    session: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(require_viewer_or_higher)],
):
    """Возвращает всё оборудование в плоском виде с полным путем иерархии"""

    return await EquipmentService.get_all_equipment_flat(session)


@router.post(
    "/",
    response_model=EquipmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новое оборудование",
)
async def create_equipment(
    data: Annotated[EquipmentCreate, Body(description="Данные для создания")],
    session: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[User, Depends(require_superadmin)],
):
    """Создать новое оборудование и привязать к нему неисправность, и Поставщика"""

    try:
        return await EquipmentService.create_equipment(session, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch(
    "/{equipment_id}",
    response_model=EquipmentResponse,
    summary="Редактировать оборудование",
)
async def update_equipment(
    equipment_id: Annotated[int, Path(ge=1)],
    data: Annotated[EquipmentUpdate, Body()],
    session: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[User, Depends(require_superadmin)],
):
    """Изменение названия оборудования или привязанного Поставщика"""

    try:
        return await EquipmentService.update_equipment(session, equipment_id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/{equipment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить оборудование",
)
async def delete_equipment(
    equipment_id: Annotated[int, Path(ge=1)],
    session: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[User, Depends(require_superadmin)],
):
    """Удаляет оборудование, если оно не содержит дочерних элементов и не используется в ремонтах"""

    try:
        success = await EquipmentService.delete_equipment(session, equipment_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Оборудование не найдено"
            )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return None


# ------------------------
# CRUD для неисправностей


@router.post(
    "/{equipment_id}/malfunctions",
    response_model=list[MalfunctionResponse],
    status_code=status.HTTP_200_OK,
    summary="Добавить неисправности к оборудованию",
)
async def add_malfunctions_to_equipment(
    equipment_id: Annotated[int, Path(ge=1)],
    data: MalfunctionAttachRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[User, Depends(require_superadmin)],
):
    """
    Привязывает существующие неисправности (по ID) или создает новые (по названию)
    и связывает их с конкретным оборудованием
    """
    return await EquipmentService.add_malfunctions_to_equipment(
        session,
        eq_id=equipment_id,
        malf_ids=data.malfunction_ids,
        new_names=data.new_names,
    )


@router.delete(
    "/{equipment_id}/malfunctions/{malf_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Отвязать неисправность от оборудования",
)
async def detach_malfunction_from_equipment(
    equipment_id: Annotated[int, Path(ge=1)],
    malf_id: Annotated[int, Path(ge=1)],
    session: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[User, Depends(require_superadmin)],
):
    """Удаляет связь между оборудованием и неисправностью."""

    success = await EquipmentService.detach_malfunction(session, equipment_id, malf_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Связь не найдена"
        )
    return None


@router.patch(
    "/malfunctions/{malf_id}",
    response_model=MalfunctionResponse,
    summary="Редактировать имя неисправности в справочнике",
)
async def update_malfunction_text(
    malf_id: Annotated[int, Path(ge=1)],
    data: Annotated[MalfunctionUpdate, Body()],
    session: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[User, Depends(require_superadmin)],
):
    """Меняет название неисправности"""

    try:
        return await EquipmentService.update_malfunction(session, malf_id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/malfunctions/{malf_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить неисправность из базы",
)
async def delete_malfunction(
    malf_id: Annotated[int, Path(ge=1)],
    session: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[User, Depends(require_superadmin)],
):
    """Полное удаление неисправности (запрещено, если она есть в истории ремонтов)"""
    try:
        success = await EquipmentService.delete_malfunction(session, malf_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Неисправность не найдена"
            )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return None


# ---------------------
# CRUD для Поставщиков


@router.post(
    "/suppliers",
    response_model=SupplierResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать нового Поставщика",
)
async def create_supplier(
    data: Annotated[SupplierCreate, Body()],
    session: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[User, Depends(require_superadmin)],
):
    """Создает нового поставщика в справочнике"""

    try:
        supp, was_created = await EquipmentService.get_or_create_supplier(
            session, data.supplier_name
        )
        
        if was_created:
            # Новый поставщик - возвращаем 201
            return supp
        else:
            # Существующий поставщик - возвращаем 200 с информацией
            raise HTTPException(
                status_code=status.HTTP_200_OK,
                detail=f"Поставщик '{data.supplier_name}' уже существует в справочнике"
            )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch(
    "/suppliers/{supplier_id}",
    response_model=SupplierResponse,
    summary="Редактировать название Поставщика",
)
async def update_supplier(
    supplier_id: Annotated[int, Path(ge=1)],
    data: Annotated[SupplierUpdate, Body()],
    session: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[User, Depends(require_superadmin)],
):
    """Меняет название Поставщика"""

    try:
        return await EquipmentService.update_supplier(session, supplier_id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/suppliers/{supplier_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить Поставщика",
)
async def delete_supplier(
    supplier_id: Annotated[int, Path(ge=1)],
    session: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[User, Depends(require_superadmin)],
):
    """Удаление Поставщика (запрещено, если к нему привязано оборудование)"""
    try:
        success = await EquipmentService.delete_supplier(session, supplier_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Поставщик не найден"
            )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return None
