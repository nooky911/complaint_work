import asyncio
import sys

from sqlalchemy import text


async def create_user_simple():
    if len(sys.argv) < 3:
        print("Формат ввода: логин пароль роль (полное) ФИО")
        return

    login, password = sys.argv[1], sys.argv[2]
    role = sys.argv[3] if len(sys.argv) > 3 else "viewer"
    full_name = sys.argv[4]

    sys.path.insert(0, ".")

    from myapp.database.base import async_session_maker
    from myapp.auth.security import get_password_hash

    hashed = get_password_hash(password)

    async with async_session_maker() as session:
        sql = f"""
            INSERT INTO users (login, hashed_password, role, is_active, full_name)
            VALUES ('{login}', '{hashed}', '{role}'::user_role, true, '{full_name}')
        """

        await session.execute(text(sql))
        await session.commit()
        print(f"Пользователь '{full_name}' создан!")


if __name__ == "__main__":
    asyncio.run(create_user_simple())
