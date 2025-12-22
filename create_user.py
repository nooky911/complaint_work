import asyncio
import sys

from sqlalchemy import text


async def create_user_simple():
    if len(sys.argv) < 3:
        print("Использование: python script.py логин пароль [роль]")
        return

    login, password = sys.argv[1], sys.argv[2]
    role = sys.argv[3] if len(sys.argv) > 3 else "viewer"

    sys.path.insert(0, ".")

    from myapp.database.base import async_session_maker
    from myapp.auth.security import get_password_hash

    hashed = get_password_hash(password)

    async with async_session_maker() as session:
        sql = f"""
            INSERT INTO users (login, hashed_password, role, is_active)
            VALUES ('{login}', '{hashed}', '{role}'::user_role, true)
        """

        await session.execute(text(sql))
        await session.commit()
        print(f"Пользователь '{login}' создан!")


if __name__ == "__main__":
    asyncio.run(create_user_simple())
