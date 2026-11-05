from fastapi import HTTPException
from sqlalchemy import select, or_, case as sql_case

from myapp.constants.case_lock import is_case_lock_active
from myapp.models.repair_case_equipment import RepairCaseEquipment
from myapp.models.user import UserEditPartner, User


class UserAccessService:
    @staticmethod
    def partner_ids(user_id):
        """Выбирает ID редакторов с взаимным доступом"""
        peer = sql_case(
            (UserEditPartner.user_a_id == user_id, UserEditPartner.user_b_id),
            else_=UserEditPartner.user_a_id,
        )
        return (
            select(
                sql_case(
                    (UserEditPartner.user_a_id == user_id, UserEditPartner.user_b_id),
                    else_=UserEditPartner.user_a_id,
                )
            )
            .join(User, User.id == peer)
            .where(
                User.role == "editor",
                or_(
                    UserEditPartner.user_a_id == user_id,
                    UserEditPartner.user_b_id == user_id,
                ),
            )
        )

    @staticmethod
    async def can_edit_owner(session, user, owner_id):
        """Проверяет право редактирования случаев владельца"""
        if user.role == "superadmin":
            return True
        if user.role != "editor":
            return False
        if owner_id == user.id:
            return True
        return (
            await session.scalar(
                select(User.id).where(
                    User.id == owner_id,
                    User.id.in_(UserAccessService.partner_ids(user.id)),
                )
            )
            is not None
        )

    @staticmethod
    async def validate_case_owner(session, owner_id, direction):
        """Запрещает новое назначение неактивного, просматривающего или чужого редактора"""
        owner = await session.get(User, owner_id)
        if (
            not owner
            or not owner.is_active
            or owner.role not in ("editor", "superadmin")
            or (owner.role != "superadmin" and owner.direction != direction)
        ):
            raise ValueError(
                "Выберите действующего ответственного с правом редактирования из своего раздела"
            )
        return owner


async def lock_case_for_change(session, case_id):
    """Блокирует строку случая и проверяет активную аренду редактора"""
    case = await session.scalar(
        select(RepairCaseEquipment)
        .where(RepairCaseEquipment.id == case_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if case is None:
        raise HTTPException(404, "Случай не найден")
    actor_id = session.info.get("actor_id")
    if (
        actor_id is not None
        and is_case_lock_active(case)
        and case.locked_by_id != actor_id
    ):
        raise HTTPException(423, "Случай редактирует другой пользователь")
    return case
