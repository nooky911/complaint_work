from sqlalchemy import select, delete, or_

from myapp.database.transactional import transactional
from myapp.models.user import User, UserEditPartner
from myapp.auth.security import get_password_hash
from myapp.config import settings


class AdminUserService:
    @staticmethod
    async def list_users(session):
        """Возвращает всех пользователей и их напарников"""
        users = list(
            (
                await session.scalars(select(User).order_by(User.full_name, User.id))
            ).all()
        )
        pairs = (await session.execute(select(UserEditPartner))).scalars().all()
        partners = {u.id: [] for u in users}
        for p in pairs:
            partners[p.user_a_id].append(p.user_b_id)
            partners[p.user_b_id].append(p.user_a_id)
        return [
            dict(
                id=u.id,
                login=u.login,
                full_name=u.full_name,
                role=u.role,
                is_active=u.is_active,
                created_at=u.created_at,
                partner_ids=sorted(partners[u.id]),
                restricted_access=u.restricted_access,
                allowed_rc_names=u.allowed_rc_names,
            )
            for u in users
        ]

    @staticmethod
    async def _locked_users(session, actor_id):
        # Единый порядок блокировок предотвращает одновременное отключение последних администраторов
        """Блокирует пользователей для согласованного изменения прав"""
        users = list(
            (
                await session.scalars(
                    select(User)
                    .order_by(User.id)
                    .with_for_update()
                    .execution_options(populate_existing=True)
                )
            ).all()
        )
        actor = next((u for u in users if u.id == actor_id), None)
        if not actor or not actor.is_active or actor.role != "superadmin":
            raise PermissionError("Требуется действующая учётная запись администратора")
        return users

    @staticmethod
    def validate_change(users, data, target_id):
        """Проверяет логин, напарников и наличие активного администратора"""
        if data.restricted_access and (
            data.role != "viewer" or not data.allowed_rc_names
        ):
            raise ValueError(
                "Ограниченный доступ требует роли «Просмотр» и хотя бы одного РЦ"
            )
        if any(
            not name.strip().isdigit() or not 1 <= int(name.strip()) <= 999
            for name in data.allowed_rc_names
        ):
            raise ValueError("Проверьте наименования РЦ")
        data.allowed_rc_names = (
            sorted(set(str(int(name.strip())) for name in data.allowed_rc_names))
            if data.restricted_access
            else []
        )
        if target_id in data.partner_ids:
            raise ValueError("Нельзя назначить пользователя напарником самому себе")
        if set(data.partner_ids) - {u.id for u in users}:
            raise ValueError("Один из выбранных пользователей не найден")
        if data.partner_ids and (
            data.role != "editor"
            or any(u.id in data.partner_ids and u.role != "editor" for u in users)
        ):
            raise ValueError(
                "Взаимный доступ назначается только между пользователями с ролью «Редактирование»"
            )
        if any(
            u.id != target_id and u.login.lower() == data.login.lower() for u in users
        ):
            raise ValueError("Такой логин уже используется")
        if target_id and not (data.role == "superadmin" and data.is_active):
            if not any(
                u.id != target_id and u.is_active and u.role == "superadmin"
                for u in users
            ):
                raise ValueError(
                    "Нельзя отключить или понизить роль последнего активного администратора"
                )

    @staticmethod
    async def _set_partners(session, user_id, partner_ids):
        """Обновляет взаимные пары выбранного пользователя"""
        await session.execute(
            delete(UserEditPartner).where(
                or_(
                    UserEditPartner.user_a_id == user_id,
                    UserEditPartner.user_b_id == user_id,
                )
            )
        )
        for peer in sorted(set(partner_ids)):
            a, b = sorted((user_id, peer))
            session.add(UserEditPartner(user_a_id=a, user_b_id=b))

    @classmethod
    @transactional
    async def create_user(cls, session, actor_id, data):
        """Создаёт пользователя с начальным паролем из настроек"""
        users = await cls._locked_users(session, actor_id)
        cls.validate_change(users, data, None)
        user = User(
            login=data.login,
            full_name=data.full_name,
            role=data.role,
            is_active=data.is_active,
            hashed_password=get_password_hash(
                settings.ADMIN_DEFAULT_PASSWORD.get_secret_value()
            ),
            auth_version=0,
            restricted_access=data.restricted_access,
            allowed_rc_names=data.allowed_rc_names,
        )
        session.add(user)
        await session.flush()
        await cls._set_partners(session, user.id, data.partner_ids)
        return {
            "id": user.id,
            "password": settings.ADMIN_DEFAULT_PASSWORD.get_secret_value(),
        }

    @classmethod
    @transactional
    async def update_user(cls, session, actor_id, user_id, data):
        """Изменяет данные пользователя и взаимный доступ"""
        users = await cls._locked_users(session, actor_id)
        user = next((u for u in users if u.id == user_id), None)
        if user is None:
            raise LookupError("Пользователь не найден")
        cls.validate_change(users, data, user_id)
        if (
            user.restricted_access != data.restricted_access
            or user.allowed_rc_names != data.allowed_rc_names
            or user.role != data.role
            or user.is_active != data.is_active
            or user.login != data.login
        ):
            user.auth_version += 1
        for field in (
            "login",
            "full_name",
            "role",
            "is_active",
            "restricted_access",
            "allowed_rc_names",
        ):
            setattr(user, field, getattr(data, field))
        await cls._set_partners(session, user_id, data.partner_ids)
        await session.flush()
        return {"id": user.id}

    @classmethod
    @transactional
    async def reset_password(cls, session, actor_id, user_id):
        """Сбрасывает пароль и завершает действующие сессии"""
        users = await cls._locked_users(session, actor_id)
        user = next((u for u in users if u.id == user_id), None)
        if user is None:
            raise LookupError("Пользователь не найден")
        user.hashed_password = get_password_hash(
            settings.ADMIN_DEFAULT_PASSWORD.get_secret_value()
        )
        user.auth_version += 1
        await session.flush()
        return {
            "id": user.id,
            "password": settings.ADMIN_DEFAULT_PASSWORD.get_secret_value(),
        }
