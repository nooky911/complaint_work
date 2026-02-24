from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from myapp.auth.security import verify_password, get_password_hash
from myapp.database.transactional import transactional
from myapp.models.user import User
from myapp.schemas.users import UserPasswordChange


class UserService:
    @staticmethod
    async def get_by_login(
        session: AsyncSession,
        login: str,
    ) -> User | None:
        stmt = select(User).where(User.login == login)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    @transactional
    async def change_password(
        session: AsyncSession, user: User, data: UserPasswordChange
    ) -> User:
        """Меняет пароль пользователя"""
        if not verify_password(data.old_password, user.hashed_password):
            raise ValueError("Старый пароль указан неверно")

        if data.old_password == data.new_password:
            raise ValueError("Новый пароль не может совпадать со старым")

        user.hashed_password = get_password_hash(data.new_password)

        return user

    @staticmethod
    async def get_all_active_users(session: AsyncSession) -> list[User]:
        """Возвращает список всех активных пользователей"""
        stmt = select(User).where(User.is_active == True).order_by(User.full_name)
        result = await session.execute(stmt)
        return list(result.scalars().all())
