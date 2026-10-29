"""Отдельные маршруты ограниченного просмотра"""

import json
from typing import Literal
from sqlalchemy import cast, String
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from myapp.auth.dependencies import get_current_user
from myapp.database.base import get_db
from myapp.models.user import User
from myapp.models.repair_case_equipment import RepairCaseEquipment as Case
from myapp.services.restricted_view_service import (
    query_for,
    list_cases,
    LABELS,
    RELATIONS,
    SUMMARIES,
    apply_filters,
)

router = APIRouter(prefix="/restricted/cases", tags=["Ограниченный просмотр"])


async def restricted_user(user: User = Depends(get_current_user)):
    """Разрешает только профиль ограниченного просмотра"""
    if not user.restricted_access or user.role != "viewer":
        raise HTTPException(403, "Недостаточно прав")
    return user


@router.get("")
async def cases(
    session: AsyncSession = Depends(get_db),
    user: User = Depends(restricted_user),
    sort_order: Literal["asc", "desc"] = "desc",
    page: int = Query(1, ge=1),
    size: int = Query(25, ge=1, le=100),
    filters: str = Query("{}", max_length=20000),
):
    """Возвращает страницу разрешённых случаев"""
    return await list_cases(
        session, user, parse_filters(filters), page, size, sort_order
    )


def parse_filters(filters):
    """Проверяет формат фильтров до построения запроса"""
    try:
        parsed = json.loads(filters)
        if not isinstance(parsed, dict):
            raise ValueError()
        return parsed
    except (ValueError, TypeError):
        raise HTTPException(422, "Некорректные фильтры")


@router.get("/filters")
async def options(
    filters: str = Query("{}", max_length=20000),
    session: AsyncSession = Depends(get_db),
    user: User = Depends(restricted_user),
):
    """Собирает варианты фильтров только из доступных случаев"""
    stmt, fields = query_for(user)
    stmt = apply_filters(stmt, fields, parse_filters(filters))
    # Один запрос вместо отдельного обращения к БД для каждой колонки
    rows = (await session.execute(stmt)).mappings().all()
    result = {
        key: sorted({row[key] for row in rows}, key=lambda v: str(v or ""))
        for key in LABELS
        if key != "supplier"
    }
    references = {}
    for key in {*RELATIONS, *SUMMARIES} - {"supplier"}:
        pairs = {
            (row[f"{key}_id"], row[key]) for row in rows if row[f"{key}_id"] is not None
        }
        references[key] = [
            {"id": ident, "name": name}
            for ident, name in sorted(pairs, key=lambda pair: str(pair[1] or ""))
        ]
    return {"labels": LABELS, "options": result, "references": references}


@router.get("/display-numbers")
async def numbers(
    session: AsyncSession = Depends(get_db),
    user: User = Depends(restricted_user),
    search: str = Query("", pattern=r"^[0-9]*$", max_length=10),
):
    """Ищет номера только среди доступных пользователю случаев"""
    stmt, fields = query_for(user)
    stmt = (
        stmt.with_only_columns(fields["display_number"])
        .where(cast(fields["display_number"], String).startswith(search))
        .order_by(fields["display_number"].desc())
        .limit(50)
    )
    return list((await session.scalars(stmt)).all())


@router.get("/{case_id}")
async def detail(
    case_id: int,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(restricted_user),
):
    """Проверяет РЦ до выдачи карточки с разрешёнными полями"""
    stmt, _ = query_for(user)
    row = (await session.execute(stmt.where(Case.id == case_id))).mappings().first()
    if row is None:
        raise HTTPException(404, "Случай не найден")
    return dict(row)
