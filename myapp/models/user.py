from sqlalchemy import (
    String,
    Text,
    TIMESTAMP,
    text,
    Boolean,
    Integer,
    ForeignKey,
    CheckConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import ENUM
from datetime import datetime

from myapp.database.base import Base


# Модель пользователя
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    auth_version: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0"), default=0
    )
    login: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(Text, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        ENUM("viewer", "editor", "superadmin", name="user_role", create_type=False),
        server_default=text("'viewer'"),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        server_default=text("true"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=text("now()"),
        nullable=False,
    )


class UserEditPartner(Base):
    """Одна запись пары даёт взаимный, но не транзитивный доступ"""

    __tablename__ = "user_edit_partners"
    __table_args__ = (
        CheckConstraint("user_a_id < user_b_id", name="ck_user_edit_partner_order"),
    )
    user_a_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    user_b_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
