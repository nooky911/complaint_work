from fastapi import APIRouter, Query, Depends
from typing import Annotated

from myapp.auth.dependencies import (
    require_viewer_or_higher,
    require_superadmin,
    require_editor_or_superadmin,
)
from myapp.models.user import User
from myapp.schemas.references import (
    CaseFormReferencesResponse,
    EquipmentManagementReferencesResponse,
)
from myapp.schemas.filters import FilterOptionsResponse, CaseFilterParams
from myapp.services.reference_service import ReferenceService
from myapp.services.case_filter_service import CaseFilterService


router = APIRouter(prefix="/references", tags=["Выпадающие списки"])


@router.get(
    "/case-form",
    response_model=CaseFormReferencesResponse,
    summary="Получить все справочники для формы создания/редактирования случая",
)
async def get_case_form_references(
    _current_user: Annotated[User, Depends(require_editor_or_superadmin)],
):
    return await ReferenceService.get_case_form_references()


@router.get(
    "/filter-options",
    response_model=FilterOptionsResponse,
    summary="Получить опции для фильтров",
)
async def get_filter_options(
    _user: Annotated[User, Depends(require_viewer_or_higher)],
):
    return await CaseFilterService.get_filter_options()


@router.get(
    "/dynamic-filter-options",
    response_model=FilterOptionsResponse,
    summary="Получить динамические опции для фильтров на основе выбранных значений",
)
async def get_dynamic_filter_options(
    _user: Annotated[User, Depends(require_viewer_or_higher)],
    params: Annotated[CaseFilterParams, Query()] = CaseFilterParams(),
):
    """Получить опции фильтров с учетом уже выбранных значений"""
    return await CaseFilterService.get_dynamic_filter_options(params)


@router.get(
    "/management-references",
    response_model=EquipmentManagementReferencesResponse,
    summary="Получить справочники для управления оборудованием",
)
async def get_management_references(
    _admin: Annotated[User, Depends(require_superadmin)],
):
    """
    Получить необходимый набор справочников для страницы
    редактирования оборудования: неисправности, поставщики и их связи
    """
    return await ReferenceService.get_equipment_management_references()
