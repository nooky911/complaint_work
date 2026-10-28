from sqlalchemy import select, or_, case
from myapp.models.user import UserEditPartner, User


class UserAccessService:
    @staticmethod
    def partner_ids(user_id):
        """Выбирает ID редакторов с взаимным доступом"""
        peer = case(
            (UserEditPartner.user_a_id == user_id, UserEditPartner.user_b_id),
            else_=UserEditPartner.user_a_id,
        )
        return (
            select(
                case(
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
