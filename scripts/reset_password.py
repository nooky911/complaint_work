#!/usr/bin/env python3
"""
Скрипт для сброса пароля пользователя
Использование: python reset_password.py <user_id> [new_password]
"""

import sys
import asyncio

from myapp.database.base import get_db
from myapp.models.user import User
from myapp.auth.security import get_password_hash
from sqlalchemy import select

sys.path.append("/")


async def reset_password(user_id: int, new_password: str = "12345678"):
    """Сбрасывает пароль пользователя"""

    # Получаем сессию БД
    async for session in get_db():
        try:
            user = await session.get(User, user_id)
            if not user:
                print(f"Пользователь с ID {user_id} не найден")
                return False

            user.hashed_password = get_password_hash(new_password)

            session.add(user)
            await session.commit()

            print(f"Пароль пользователя {user.login} (ID: {user_id}) успешно изменен")
            print(f"Имя: {user.full_name} | Роль: {user.role}")
            return True

        except Exception as e:
            await session.rollback()
            print(f"Ошибка: {e}")
            return False


async def list_users():
    """Показывает список всех пользователей"""
    async for session in get_db():
        try:
            stmt = select(User).where(User.is_active == True).order_by(User.full_name)
            result = await session.execute(stmt)
            users = result.scalars().all()

            print("\n📋 Список активных пользователей:")
            print("-" * 60)
            print(f"{'ID':<5} {'Логин':<15} {'Имя':<20} {'Роль':<10}")
            print("-" * 60)

            for user in users:
                print(
                    f"{user.id:<5} {user.login:<15} {user.full_name:<20} {user.role:<10}"
                )
            print("-" * 60)
            return True

        except Exception as e:
            print(f"Ошибка при получении списка пользователей: {e}")
            return False
        finally:
            await session.close()

    return False


def main():
    if len(sys.argv) < 2:
        print("Использование: python reset_password.py [list | user_id] [password]")
        return

    cmd = sys.argv[1]
    if cmd == "list":
        asyncio.run(list_users())
    else:
        try:
            uid = int(cmd)
            pwd = sys.argv[2] if len(sys.argv) > 2 else "12345678"
            if len(pwd) < 8:
                print("Пароль слишком короткий (мин. 8)")
                return
            asyncio.run(reset_password(uid, pwd))
        except ValueError:
            print("ID должен быть числом")


if __name__ == "__main__":
    main()
