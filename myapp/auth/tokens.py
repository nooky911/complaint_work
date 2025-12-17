import jwt
from datetime import datetime, timedelta, timezone


from myapp.config import settings

ALGORITHM = "HS256"


def create_access_token(
    data: dict,
) -> str:
    """Создать JWT-токен с истечением по времени"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=ALGORITHM,
    )
    return encoded_jwt


def decode_token(token: str) -> dict | None:
    """Декодирует JWT токен и возвращает payload или None при ошибках"""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[ALGORITHM],
        )
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidAlgorithmError:
        return None
    except jwt.PyJWTError:
        return None
