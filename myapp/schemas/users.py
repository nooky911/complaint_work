from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class UserBase(BaseModel):
    """Базовая схема пользователя"""

    login: str
    role: str
    full_name: str | None = None
    is_active: bool = True


class UserCreate(UserBase):
    """Схема для создания нового пользователя"""

    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    """Схема для входа в систему"""

    login: str
    password: str


class UserResponse(UserBase):
    """Схема ответа с данными пользователя"""

    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    """Схема ответа с JWT токеном"""

    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserPasswordChange(BaseModel):
    """Схема для смены пароля"""

    old_password: str = Field(..., description="Текущий пароль пользователя")
    new_password: str = Field(..., min_length=8, description="Новый пароль")
