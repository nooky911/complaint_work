from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from myapp.database.base import get_db
from myapp.schemas.equipment import EquipmentWithPathResponse
from myapp.services.equipment_service import EquipmentService


router = APIRouter(prefix="/references", tags=["Выпадающие списки"])


# Получить оборудование для конкретного уровня иерархии
@router.get("/equipment-by-level", response_model=list[EquipmentWithPathResponse])
async def get_equipment_by_level(
    level: int = Query(..., description="Уровень иерархии (0-4)"),
    parent_id: int | None = Query(None, description="ID родителя для фильтрации"),
    q: str = Query("", description="Поисковый запрос"),
    session: AsyncSession = Depends(get_db),
):
    """Возможность начинать заполнение типа оборудования с любого места вложенности"""
    # 1. Валидация входных данных
    if level < 0 or level > 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Уровень должен быть в диапазоне 0-4",
        )

    # 2. Обязательное наличие parent_id для уровней > 0
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
    equipment_id: int, session: AsyncSession = Depends(get_db)
):
    """Автоматическое заполнение всех полей, которые находятся выше поля заполняемого пользователем"""
    return await EquipmentService.get_equipment_chain(session, equipment_id)
