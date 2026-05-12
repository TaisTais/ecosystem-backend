from datetime import datetime, timedelta
from typing import Optional
import bcrypt
from jose import JWTError, jwt
from fastapi import HTTPException, status

# ==================== КОНФИГУРАЦИЯ ====================
SECRET_KEY = "super-secret-key-change-this-in-production-please-make-it-very-long-and-random"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7


# ==================== ХЭШИРОВАНИЕ ПАРОЛЕЙ ====================
def hash_password(password: str) -> str:
    """Хэширует пароль с помощью bcrypt"""
    if not password:
        raise ValueError("Password cannot be empty")

    # Обрезаем до 72 байт (ограничение bcrypt)
    password = password[:72].encode('utf-8')

    # Генерируем соль и хэш
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password, salt)

    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверяет пароль"""
    if not plain_password or not hashed_password:
        return False

    try:
        plain = plain_password[:72].encode('utf-8')
        hashed = hashed_password.encode('utf-8')
        return bcrypt.checkpw(plain, hashed)
    except Exception:
        return False


# ==================== JWT ====================
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный токен",
            headers={"WWW-Authenticate": "Bearer"},
        )
