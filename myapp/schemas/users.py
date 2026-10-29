from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal


class UserBase(BaseModel):
    """Базовая схема пользователя"""

    login: str
    role: str
    full_name: str | None = None
    is_active: bool = True


class UserCreate(UserBase):
    """Схема для создания нового пользователя"""

    password: str = Field(..., min_length=8)


class UserResponse(UserBase):
    """Схема ответа с данными пользователя"""

    id: int
    created_at: datetime
    partner_ids: list[int] = Field(default_factory=list)
    restricted_access: bool = False
    allowed_rc_names: list[str] = Field(default_factory=list, max_length=100)
    login: str

    model_config = ConfigDict(from_attributes=True)


class UserPasswordChange(BaseModel):
    """Схема для смены пароля"""

    old_password: str = Field(..., description="Текущий пароль пользователя")
    new_password: str = Field(..., min_length=8, description="Новый пароль")


class AdminUserData(BaseModel):
    """Данные пользователя для создания и редактирования в админ-панели"""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    login: str = Field(min_length=1, max_length=50, pattern=r"^[A-Za-z0-9_.@-]+$")
    full_name: str = Field(min_length=1, max_length=255)
    role: Literal["viewer", "editor", "superadmin"] = "viewer"
    is_active: bool = True
    partner_ids: list[int] = Field(default_factory=list, max_length=500)
    restricted_access: bool = False
    allowed_rc_names: list[str] = Field(default_factory=list, max_length=100)
