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
        # 1. Проверяем старый пароль (сравниваем plain text с хешем в БД)
        if not verify_password(data.old_password, user.hashed_password):
            raise ValueError("Старый пароль указан неверно")

        # 2. Проверяем, что новый пароль не совпадает со старым
        if data.old_password == data.new_password:
            raise ValueError("Новый пароль не может совпадать со старым")

        # 3. Хешируем новый пароль и сохраняем
        user.hashed_password = get_password_hash(data.new_password)

        return user
