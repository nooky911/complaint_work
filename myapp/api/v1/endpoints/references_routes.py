from fastapi import APIRouter, Depends, Query, HTTPException, status, Path
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from myapp.database.base import get_db
from myapp.schemas.equipment import EquipmentWithPathResponse
from myapp.services.equipment_service import EquipmentService


router = APIRouter(prefix="/references", tags=["Выпадающие списки"])


# Получить оборудование для конкретного уровня иерархии
@router.get("/equipment-by-level", response_model=list[EquipmentWithPathResponse])
async def get_equipment_by_level(
    level: Annotated[int, Query(description="Уровень иерархии (0-4)", ge=0, le=4)],
    parent_id: Annotated[
        int | None, Query(description="ID родителя для фильтрации")
    ] = None,
    q: Annotated[str, Query(description="Поисковый запрос")] = "",
    session: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """Возможность начинать заполнение типа оборудования с любого места вложенности"""
    # Обязательное наличие parent_id для уровней > 0
    if level > 0 and not parent_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Для уровня > 0 необходим parent_id",
        )

    return await EquipmentService.get_equipment_by_level(session, level, parent_id, q)


# Получить полную цепочку от корня до выбранного оборудования
@router.get(
    "/equipment-chain/{equipment_id}", response_model=list[EquipmentWithPathResponse]
)
async def get_equipment_chain(
    equipment_id: Annotated[int, Path(description="ID оборудования", ge=1)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    """Автоматическое заполнение всех полей, которые находятся выше поля заполняемого пользователем"""
    return await EquipmentService.get_equipment_chain(session, equipment_id)
