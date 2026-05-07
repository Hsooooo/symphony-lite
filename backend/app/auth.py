from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from typing import Optional
from fastapi import Depends, HTTPException, status, Header, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from uuid import UUID

from app.config import get_settings
from app.database import get_db
from app import crud, models

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


class OptionalOAuth2PasswordBearer(OAuth2PasswordBearer):
    """Authorization 헤더가 없어도 에러를 내지 않는 OAuth2 스킴"""
    async def __call__(self, request: Request) -> Optional[str]:
        try:
            return await super().__call__(request)
        except HTTPException:
            return None

optional_oauth2_scheme = OptionalOAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    # bcrypt는 최대 72바이트까지만 지원
    return pwd_context.verify(plain_password[:72], hashed_password)


def get_password_hash(password: str) -> str:
    # bcrypt는 최대 72바이트까지만 지원
    return pwd_context.hash(password[:72])


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = crud.get_user(db, UUID(user_id))
    if user is None:
        raise credentials_exception
    user.auth_source = "jwt"
    return user


def get_current_active_user(
    current_user: models.User = Depends(get_current_user)
) -> models.User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def get_current_user_by_api_key(
    x_api_key: str = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db)
) -> models.User:
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-API-Key header required",
        )
    
    # 모든 API 키를 순회하며 verify (API 키 수가 적을 때 효율적)
    api_keys = db.query(models.ApiKey).all()
    for api_key in api_keys:
        if verify_password(x_api_key, api_key.key_hash):
            api_key.last_used_at = datetime.utcnow()
            db.commit()
            api_key.user.auth_source = "api_key"
            return api_key.user
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API key",
    )


def get_current_user_or_api_key(
    token: Optional[str] = Depends(optional_oauth2_scheme),
    x_api_key: str = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db)
) -> models.User:
    """JWT 또는 API Key 중 하나로 인증"""
    if x_api_key:
        return get_current_user_by_api_key(x_api_key, db)
    if token:
        return get_current_user(token, db)
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )
